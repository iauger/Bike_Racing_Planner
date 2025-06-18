# event_list.py
import requests
import pandas as pd
import json
import re

GRAPHQL_URL = "https://outsideapi.com/fed-gw/graphql"
HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0",
    "Origin": "https://www.bikereg.com",
    "Referer": "https://www.bikereg.com/events/?types=2",
    "X-Requested-With": "XMLHttpRequest"
}

QUERY = """
query GetCyclocrossEvents($first: Int!, $after: String, $searchParameters: SearchEventQueryParamsInput!) {
  athleticEventCalendar(
    first: $first
    after: $after
    searchParameters: $searchParameters
  ) {
    pageInfo {
      endCursor
      hasNextPage
    }
    nodes {
      name
      city
      state
      startDate
      endDate
      distanceString
      latitude
      longitude
      eventId
      athleticEvent {
        eventUrl
        eventTypes
        date
        eventEndDate
        ... on AthleticEvent {
          staticUrl
          openRegDate
          closeRegDate
          isOpen
          categories {
            name
            startTime
            distance
          }
        }
      }
    }
  }
}
"""


def get_event_details(event_id):
    url = f"https://www.bikereg.com/api/search?eventID={event_id}"
    resp = requests.get(url)
    resp.raise_for_status()
    return resp.json()

def tag_category_name(name):
    name = name.lower().strip()
    tags = []

    # Gender
    if re.search(r"\b(men|male)\b", name):
        tags.append("men")
    elif re.search(r"\b(women|female|fem)\b", name):
        tags.append("women")
    elif "non-binary" in name or "nb" in name:
        tags.append("non_binary")
    elif "trans" in name:
        tags.append("trans")
    elif "coed" in name or "mixed" in name:
        tags.append("coed")
    elif "mixed" in name or "open" in name:
        tags.append("mixed")

    # Age
    if "junior" in name or re.search(r"\bages? \d+", name):
        tags.append("junior")
    if re.search(r"\b(40|45|50|60|70)[\+]?", name) or "masters" in name:
        tags.append("masters")

    # Age range
    age_match = re.search(r"ages? (\d{1,2}) ?[-–] ?(\d{1,2})", name)
    if age_match:
        tags.append(f"age_{age_match.group(1)}_{age_match.group(2)}")
    else:
        age_plus_match = re.search(r"(\d{2})\+", name)
        if age_plus_match:
            tags.append(f"age_{age_plus_match.group(1)}_plus")

    # Category level
    # Only match "pro" as a standalone word, not as part of another word like "program"
    if re.search(r"\bpro\b", name):
      tags.append("pro")
    cat_match = re.search(r"cat\s*([\d\s*/]+)", name)
    if cat_match:
        category_string = cat_match.group(1)
        delimiters = ['/', '*', ' ', ',']
        for delimiter in delimiters:
            if delimiter in category_string:
                for num in category_string.split(delimiter):
                    num = num.strip()
                    if num in {'1', '2', '3', '4', '5'}:
                        # Append cycling category levels (e.g., Cat 1, Cat 2) to tags for classification purposes
                        tags.append(f"cat_{num}")
                break
        else:
            num = category_string.strip()
            if num in {'1', '2', '3', '4', '5'}:
                tags.append(f"cat_{num}")

    # Ability
    if "beginner" in name or "novice" in name or r"\bc\b" in name:
        tags.append("beginner")
    if "sport" in name or r"\bb\b" in name:
        tags.append("sport")
    if "elite" in name or r"\ba\b" in name:
        tags.append("elite")
    if r"\bpro\b" in name or "uci" in name:
        tags.append("pro")

    return tags

def fetch_cyclocross_events(batch_size=25, max_batches=None):
    events = []
    cursor = None
    batch_count = 0

    while True:
        variables = {
            "first": batch_size,
            "after": cursor,
            "searchParameters": {
                "appTypes": ["BIKEREG"],
                "eventTypes": [2],
                "fullEventsOnly": True
            }
        }

        payload = {
            "operationName": "GetCyclocrossEvents",
            "query": QUERY,
            "variables": variables
        }

        print("Sending GraphQL payload:")
        print(json.dumps(payload, indent=2))

        resp = requests.post(GRAPHQL_URL, json=payload, headers=HEADERS)
        print(f"Response Status Code: {resp.status_code}")
        print("Response Body:")
        print(resp.text)

        resp.raise_for_status()
        result = resp.json()
        data = result["data"]["athleticEventCalendar"]

        for node in data["nodes"]:
            ae = node.get("athleticEvent", {})
            event_id = node.get("eventId")

            # Default categories from GraphQL
            categories = ae.get("categories", [])

            # Enrich categories with registration counts from REST API
            try:
                details = get_event_details(event_id)
                match = details.get("MatchingEvents", [{}])[0]
                category_counts = {
                    c["CategoryName"].strip(): c["RegistrationCount"]
                    for c in match.get("Categories", [])
                }

                for c in categories:
                    name = c.get("name", "").strip()
                    c["RegistrationCount"] = category_counts.get(name, 0)
                    c["tags"] = tag_category_name(name)
            except Exception as e:
                print(f"Warning: could not enrich event {event_id}: {e}")
                for c in categories:
                    c["RegistrationCount"] = 0
                    c["tags"] = tag_category_name(c.get("name", ""))

            events.append({
                "name": node["name"],
                "city": node["city"],
                "state": node["state"],
                "latitude": node.get("latitude"),
                "longitude": node.get("longitude"),
                "startDate": node["startDate"],
                "endDate": node["endDate"],
                "distance": node.get("distanceString"),
                "eventId": event_id,
                "url": ae.get("eventUrl"),
                "staticUrl": ae.get("staticUrl"),
                "types": ", ".join(ae.get("eventTypes", [])),
                "firstDate": ae.get("date"),
                "eventEndDate": ae.get("eventEndDate"),
                "openRegDate": ae.get("openRegDate"),
                "closeRegDate": ae.get("closeRegDate"),
                "isRegistrationOpen": ae.get("isOpen"),
                "categories": categories
            })

        if not data["pageInfo"]["hasNextPage"] or (max_batches and batch_count >= max_batches):
            break

        cursor = data["pageInfo"]["endCursor"]
        batch_count += 1

    return pd.DataFrame(events)

if __name__ == "__main__":
    df = fetch_cyclocross_events(batch_size=1, max_batches=1)
    print(df.head())