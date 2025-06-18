# main.py
from Bike_Racing_Planner.event_list import fetch_cyclocross_events
import os
import pandas as pd

OUTPUT_PATH = "output/cyclocross_events.csv"
CSV_COLUMNS = [
    "eventId", "name", "city", "state", "latitude", "longitude",
    "startDate", "endDate", "distance", "url", "types",
    "firstDate", "eventEndDate", "staticUrl", "isRegistrationOpen",
    "openRegDate", "closeRegDate", "categories"
]

def main():
    print("Fetching Cyclocross events from BikeReg...")

    # Fetch new events
    new_df = fetch_cyclocross_events(max_batches=5)
    print(f"Fetched {len(new_df)} new events.")

    os.makedirs("output", exist_ok=True)

    # Load existing events if the file exists
    if os.path.exists(OUTPUT_PATH):
        existing_df = pd.read_csv(OUTPUT_PATH)
        print(f"Loaded {len(existing_df)} existing events from file.")
    else:
        existing_df = pd.DataFrame(columns=CSV_COLUMNS)
        print("No existing file found, starting fresh.")

    # Combine and deduplicate by eventId
    combined_df = pd.concat([existing_df, new_df], ignore_index=True)
    combined_df.drop_duplicates(subset=["eventId"], keep="last", inplace=True)
    combined_df = combined_df[CSV_COLUMNS]
    combined_df.sort_values(by="startDate", inplace=True)
    combined_df.reset_index(drop=True, inplace=True)

    # Save full deduplicated dataset
    combined_df.to_csv(OUTPUT_PATH, index=False)
    print(f"Saved {len(combined_df)} total unique events to {OUTPUT_PATH}")

if __name__ == "__main__":
    main()
