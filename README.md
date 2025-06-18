# Bikereg Cyclocross Event Scraper

This tool fetches cyclocross event data from BikeReg.com using both the public GraphQL and REST APIs, enriches the data with registration counts and category metadata, and outputs a structured CSV file for downstream use.

## Features

- Fetches event listings from the public GraphQL endpoint
- Enriches event data using the REST API to extract registration counts
- Applies tag extraction logic to identify:
  - Gender (e.g., men, women, non-binary)
  - Age group classification (e.g., juniors, masters)
  - Category level (e.g., Cat 1–5, Pro, Elite, Beginner)
- Saves data to `output/cyclocross_events.csv`
- Deduplicates events using `eventId`
- Modular codebase with support for future expansion

## Setup

```bash
pip install -r requirements.txt
