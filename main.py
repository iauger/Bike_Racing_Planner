# main.py
import os
import time
import pandas as pd
from event_list import fetch_cyclocross_events

EVENTS_PATH = "output/events.csv"
CATEGORIES_PATH = "output/event_categories.csv"
EVENTS_COLUMNS = [
    "eventId", "name", "city", "state", "latitude", "longitude",
    "startDate", "endDate", "distance", "url", "types",
    "firstDate", "eventEndDate", "staticUrl", "isRegistrationOpen",
    "openRegDate", "closeRegDate"
]
CATEGORIES_COLUMNS = [
    "eventId", "categoryName", "distance", "startTime", "registrationCount", "tags"
]

def main():
    print("Fetching Cyclocross events from BikeReg...")

    try:
        result = fetch_cyclocross_events(max_batches=1)
        if isinstance(result, tuple) and len(result) == 3:
            events_df, categories_df, errors = result
        else:
            raise ValueError("fetch_cyclocross_events did not return expected tuple of (events_df, categories_df, errors)")
    except Exception as e:
        print(f"Error fetching data: {e}")
        return

    print(f"Fetched {len(events_df)} events and {len(categories_df)} categories.")
    if errors:
        print(f"Encountered {len(errors)} errors during enrichment:")
        for event_id, msg in errors:
            print(f"  Event {event_id}: {msg}")

    os.makedirs("output", exist_ok=True)

    # Clean and store events
    events_df = events_df[EVENTS_COLUMNS]
    events_df.drop_duplicates(subset=["eventId"], keep="last", inplace=True)
    events_df.sort_values(by="startDate", inplace=True)
    events_df.reset_index(drop=True, inplace=True)
    events_df.to_csv(EVENTS_PATH, index=False)
    print(f"Saved event data to {EVENTS_PATH}")

    # Clean and store categories
    categories_df = categories_df[CATEGORIES_COLUMNS]
    categories_df.drop_duplicates(subset=["eventId", "categoryName"], keep="last", inplace=True)
    categories_df.sort_values(by=["eventId", "startTime"], inplace=True)
    categories_df.reset_index(drop=True, inplace=True)
    categories_df.to_csv(CATEGORIES_PATH, index=False)
    print(f"Saved category data to {CATEGORIES_PATH}")

    # Sleep to respect API rate limits if needed
    time.sleep(5)  # optional throttling between fetch cycles

if __name__ == "__main__":
    main()
