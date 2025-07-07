# streamlit_app.py
import streamlit as st
import pandas as pd
from geo_utils import get_lat_lon, haversine_distance
from pathlib import Path

# Load prebuilt datasets
data_dir = Path("output")
if not data_dir.exists():
    st.error("Data directory not found. Please run the data collection script first.")
    st.stop()
events_df = pd.read_csv(data_dir / "events.csv")
categories_df = pd.read_csv(data_dir / "event_categories.csv")

# UI Sidebar Inputs
st.sidebar.header("Filter Options")
user_zip = st.sidebar.text_input("Enter your ZIP Code", max_chars=5)
distance_limit = st.sidebar.slider("Max Distance (km)", min_value=10, max_value=1000, value=200, step=10)

st.sidebar.subheader("Filter by Tags")
selected_tags = []

#Extract all tags from the categories DataFrame
tags = sorted(set(tag for tag_list in categories_df['tags'].dropna().apply(eval) for tag in tag_list))
age_tags = sorted([tag for tag in tags if "age" in tag])

# Define tag groups for filtering
TAG_GROUPS = {
    "Gender": ["men", "women", "non_binary", "trans", "coed", "mixed"],
    "Age Group": age_tags,
    "Category Level": [f"cat_{i}" for i in range(1, 6)] + ["pro"],
    "Ability": ["beginner", "sport", "elite"]
}


for group, options in TAG_GROUPS.items():
    group_selection = st.sidebar.multiselect(f"{group}", options)
    selected_tags.extend(group_selection)


distance_filter_applied = False

if user_zip:
    try:
        user_lat, user_lon = get_lat_lon(user_zip)

        # Filter by distance
        distances = []
        for _, row in events_df.iterrows():
            if pd.notna(row['latitude']) and pd.notna(row['longitude']):
                dist = haversine_distance(user_lat, user_lon, row['latitude'], row['longitude'])
                dist = round(dist, 2)  # Round to 2 decimal places
            else:
                dist = float('inf')
            distances.append(dist)

        events_df['distance_km'] = distances
        events_df = events_df[events_df['distance_km'] <= distance_limit]
        distance_filter_applied = True
    except ValueError as e:
        st.sidebar.error(str(e))

# Apply tag filter if selected
event_ids_with_tags = set()
if selected_tags:
    for _, row in categories_df.iterrows():
        row_tags = eval(row['tags']) if pd.notna(row['tags']) else []
        if all(tag in row_tags for tag in selected_tags):
            event_ids_with_tags.add(row['eventId'])
    events_df = events_df[events_df['eventId'].isin(event_ids_with_tags)]

else:
    # If no tags are selected, exclude age-specific categories
    def is_not_age_tagged(tag_list):
        return all("age" not in tag for tag in tag_list)

    categories_df = categories_df[categories_df['tags'].apply(
        lambda x: is_not_age_tagged(eval(x)) if pd.notna(x) else True
    )]

# Display results
st.title("Cyclocross Race Finder")
st.markdown("Search for upcoming events based on your location and preferences.")

if distance_filter_applied:
    st.success(f"Showing events within {distance_limit} km of ZIP code {user_zip}.")
    display_cols = ['name', 'city', 'state', 'startDate', 'distance_km', 'url']
else:
    st.warning("Showing all events (no ZIP filter applied).")
    display_cols = ['name', 'city', 'state', 'startDate', 'url']

# Show table of events
st.subheader("Matching Events")
for _, event in events_df.sort_values(by='startDate').iterrows():
    with st.expander(f"{event['name']} — {event['city']}, {event['state']} ({event['startDate'][:10]})"):
        st.write(f"URL: [{event['url']}]({event['url']})")
        
        if pd.notna(event['latitude']) and pd.notna(event['longitude']):
            lat, lon = event['latitude'], event['longitude']
            map_url = f"https://www.google.com/maps/search/?api=1&query={lat},{lon}"
            st.markdown(f"[🌎 View on Google Maps]({map_url})", unsafe_allow_html=True)

        if 'distance_km' in event:
            st.write(f"Distance to Event: {round(event['distance_km'], 1)} km")

        event_cats = categories_df[categories_df['eventId'] == event['eventId']].copy()

        # Filter event categories by selected tags
        if selected_tags:
            def has_all_selected_tags(tag_str):
                tags_in_row = set(eval(tag_str)) if pd.notna(tag_str) else set()
                return all(tag in tags_in_row for tag in selected_tags)

            event_cats = event_cats[event_cats['tags'].apply(has_all_selected_tags)]

        # Display matching categories
        if not event_cats.empty:
            event_cats = event_cats.sort_values(by='startTime')
            st.write("### Event Categories")
            st.dataframe(event_cats[['categoryName', 'startTime', 'distance', 'registrationCount', 'tags']])
        else:
            st.info("No categories in this event match all selected tag(s).")

# Download option
st.download_button(
    label="Download Filtered Events as CSV",
    data=events_df.to_csv(index=False).encode('utf-8'),
    file_name='filtered_cyclocross_events.csv',
    mime='text/csv'
)
