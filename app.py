%%writefile app.py


import streamlit as st
import sys
import random
import time
import pandas as pd
from io import BytesIO
import re

# Streamlit page config
st.set_page_config(
    page_title="Google Maps Crawler",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize Selenium browser
def init_browser():
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options

    st.info("Initializing browser...")
    options = Options()
    # Colab/Streamlit config
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-setuid-sandbox')
    options.add_argument('--single-process')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-images')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--headless=new')
    options.binary_location = "/usr/lib/chromium-browser/chromium-browser"

    # Anti-block settings
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--enable-javascript")
    options.add_argument("--user-data-dir=/tmp/temp_profile")
    options.add_argument("--lang=en-US")
    options.add_argument("--start-maximized")
    options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 14_2_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36")

    # Hide automation traces
    options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
    options.add_experimental_option('useAutomationExtension', False)

    try:
        driver = webdriver.Chrome(options=options)
        st.success("Browser initialized successfully!")
        return driver
    except Exception as e:
        st.error(f"Browser initialization failed: {e}")
        return None

# Extract phone by numeric length (≥7 digits)
def extract_phone_by_digits(card):
    """Extract phone number (≥7 digits, ignore spaces/symbols)"""
    phone = "No phone"
    try:
        card_text = card.text
        raw_matches = re.findall(r'\+?\d[\d\s\-\(\)]{5,}', card_text)

        if raw_matches:
            valid_candidates = []
            for match in raw_matches:
                pure_digits = re.sub(r'[^\d]', '', match)
                if len(pure_digits) >= 6:
                    valid_candidates.append({
                        'original': match.strip(),
                        'digit_length': len(pure_digits)
                    })

            if valid_candidates:
                valid_candidates.sort(key=lambda x: x['digit_length'], reverse=True)
                # Prioritize numbers with +
                for candidate in valid_candidates:
                    if '+' in candidate['original']:
                        phone = candidate['original']
                        break
                # Fallback to longest digit string
                if phone == "No phone":
                    phone = valid_candidates[0]['original']
                # Clean format
                phone = re.sub(r'\s+', ' ', phone)
                phone = re.sub(r'[()]+', '', phone)
    except Exception as e:
        pass
    return phone

# Core crawling function
def crawl_google_maps(driver, search_keyword, max_same=6):
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys

    results = []

    try:
        st.info("Opening Google Maps...")
        driver.get("https://www.google.com/maps")
        time.sleep(5)
        st.success(f"Google Maps opened successfully! Title: {driver.title}")

        st.info("Locating search box...")
        search_box = driver.find_element(By.CSS_SELECTOR, "input.fontBodyMedium")
        search_box.click()
        time.sleep(1)

        st.info(f"Searching for: {search_keyword}")
        search_box.clear()
        time.sleep(0.5)
        search_box.send_keys(search_keyword)
        search_box.send_keys(Keys.ENTER)
        time.sleep(7)
        st.success(f"Search completed! Current URL: {driver.current_url}")

        # Initialize deduplication and counters
        extracted_shop_ids = set()
        serial_num = 1
        last_count = 0
        same_count = 0

        st.info("Starting data crawling (scroll to load)...")
        result_placeholder = st.empty()

        while True:
            # Scroll to load more content
            driver.execute_script("""
                let box1 = document.querySelector('div[role="feed"]');
                let box2 = document.querySelector('div[mqa-handle="mousewheel"]');
                let box3 = document.querySelector('div[jsname="j7nlYe"]');
                if(box1) box1.scrollTop = box1.scrollHeight;
                if(box2) box2.scrollTop = box2.scrollHeight;
                if(box3) box3.scrollTop = box3.scrollHeight;
            """)

            # Random sleep to simulate human behavior
            sleep_time = random.uniform(2.5, 3.8)
            time.sleep(sleep_time)

            # Get shop cards
            shop_cards = driver.find_elements(By.CSS_SELECTOR, "div[class*='Nv2PK']")
            current_count = len(shop_cards)

            # Extract shop info and deduplicate
            for card in shop_cards:
                shop_name = card.find_element(By.CSS_SELECTOR, "div.fontHeadlineSmall").text.strip() if card.find_elements(By.CSS_SELECTOR, "div.fontHeadlineSmall") else "No name"
                shop_addr = card.find_element(By.CSS_SELECTOR, "div.W4Efsd > span:nth-child(2)").text.strip() if card.find_elements(By.CSS_SELECTOR, "div.W4Efsd > span:nth-child(2)") else "No address"
                shop_unique_id = f"{shop_name}_{shop_addr}"

                # Extract phone (core modification)
                phone = extract_phone_by_digits(card)

                # Deduplication check
                if shop_unique_id not in extracted_shop_ids and shop_name != "No name":
                    extracted_shop_ids.add(shop_unique_id)

                    shop_info = {
                        "Serial No.": serial_num,
                        "Shop Name": shop_name,
                        "Address": shop_addr,
                        "Phone Number": phone
                    }
                    results.append(shop_info)
                    serial_num += 1

            # Real-time result display
            result_df = result_placeholder.dataframe(results, use_container_width=True)

            # Check if reached bottom
            if current_count == last_count:
                same_count += 1
                if same_count >= max_same:
                    st.info("Reached bottom of results, stopping crawl!")
                    break
            else:
                same_count = 0
            last_count = current_count

    except Exception as e:
        st.error(f"Crawling error: {e}")
    finally:
        # Close browser
        if driver:
            driver.quit()
            st.info("Browser closed")

    return results

# Excel export helper
def to_excel(df):
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='openpyxl')
    df.to_excel(writer, index=False, sheet_name='Google Maps Results')
    writer.close()
    output.seek(0)
    return output

# Main UI
def main():
    st.title("🗺️ Google Maps Crawler")
    st.markdown("---")

    # Sidebar config
    with st.sidebar:
        st.header("⚙️ Crawler Settings")
        # Input fields
        country = st.text_input("🇨🇳 Country", value="Saudi Arabia", help="Required, e.g.: China, United States, Saudi Arabia")
        city = st.text_input("🏙️ City", value="Riyadh", help="Optional, leave blank to search entire country")
        keyword = st.text_input("🔍 Keyword", value="logistics", help="Required, e.g.: constraction,freight")
        max_same = st.slider("Stop after consecutive empty scrolls", min_value=3, max_value=10, value=6, help="Stop if no new data after N scrolls")

        # Build search keyword
        if country and keyword:
            if city:
                search_keyword = f"{keyword} in {city}, {country}"
            else:
                search_keyword = f"{keyword} in {country}"
        else:
            search_keyword = ""

        # Disable button if required fields empty
        start_disabled = not (country and keyword)
        start_crawl = st.button("🚀 Start Crawling", type="primary", disabled=start_disabled)

    # Display final search keyword
    if search_keyword:
        st.sidebar.info(f"📝 Final Search Query: {search_keyword}")
    else:
        st.sidebar.warning("⚠ Please fill in Country and Keyword!")

    # Main content area
    if start_crawl:
        # Initialize browser
        driver = init_browser()
        if not driver:
            st.stop()

        # Execute crawl
        with st.spinner("Crawling data, please wait..."):
            results = crawl_google_maps(driver, search_keyword, max_same)

        # Display results
        st.markdown("---")
        st.subheader(f"✅ Crawling Completed! Total unique results: {len(results)}")
        st.dataframe(results, use_container_width=True)

        # Export to Excel
        if results:
            df = pd.DataFrame(results)
            # Optional: remove serial number column
            # df = df.drop(columns=["Serial No."])
            excel_data = to_excel(df)
            st.download_button(
                label="📥 Export to Excel",
                data=excel_data,
                file_name=f"Google_Maps_{search_keyword.replace(' ', '_')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

if __name__ == "__main__":
    main()
