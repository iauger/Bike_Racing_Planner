# Bikereg Cyclocross Event Scraper

This tool fetches cyclocross events from the Bikereg GraphQL API and saves them to a structured CSV file for further analysis.

## Features

- Uses the public Bikereg GraphQL endpoint
- Stores results in `output/cyclocross_events.csv`
- De-duplicates events using `eventId`
- Captures event details, registration info, and category breakdowns

## Setup

```bash
pip install -r requirements.txt
