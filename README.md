Google Maps Data Crawler

Author: XIE LIDONG

A Python-based tool to scrape business info (name, address, phone) from Google Maps via Selenium, with anti-detection, data deduplication and intelligent phone extraction (≥7 digits).
Core Language: Python
Browser Automation: Selenium
Web Scraping: Custom anti-detection strategies, headless browser
Text Processing: Regular Expression (Regex)
Other: Random delay control, data deduplication

Key Features
Anti-detection: Custom UA, hidden automation flags, random scroll delays
Data extraction: Auto-scroll loading, phone filter (≥7 pure digits), international number priority
Quality control: Deduplication (name+address), configurable stop conditions

Versions
Core Code Version: Directly runnable script with CLI interaction, lightweight and easy to use for quick data scraping.
Streamlit Version: Web-based UI built with Streamlit, supports local deployment or remote access via ngrok tunnel for more user-friendly operation.
