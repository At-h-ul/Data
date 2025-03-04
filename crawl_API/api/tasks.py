import os
import time
import csv
import dramatiq
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from dramatiq_config import redis_broker
from action import destroyDatatable

CHROMEDRIVER_PATH = os.path.join(os.path.dirname(__file__), "chromedriver.exe")
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DATA_DIR, exist_ok=True)
SCRAPED_GP_FILE_PATH = os.path.join(DATA_DIR, "scraped_gp.csv")
SCRAPED_VILLAGES_FILE_PATH = os.path.join(DATA_DIR, "scraped_villages.csv")

def get_driver():
    options = webdriver.ChromeOptions()
    #options.add_argument('--headless')
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--start-maximized")
    service = Service(CHROMEDRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=options)
    return driver

def extract_text(soup, element_id):
    element = soup.find("input", {"id": element_id})
    return element["value"].strip() if element else None

def write_to_csv(file_path, rows):
    with open(file_path, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(rows)

def read_scraped_gps(file_path):
    scraped_gps = []
    if os.path.exists(file_path):
        with open(file_path, mode='r') as file:
            reader = csv.reader(file)
            scraped_gps = list(reader)
    return scraped_gps

def write_scraped_gp(file_path, row):
    with open(file_path, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(row)

def check_site_crash(driver):
    try:
        form_element = driver.find_element(By.NAME, "shgOuterReportForm")
        try:
            driver.find_element(By.ID, "example")
        except:
            print("Site crashed!!")
            return True
    except:
        print("Site is crashed!!")
        return True
    return False

def write_status_file(district, block, village, status, data_dir):
    filename = os.path.join(data_dir, f"{district}-{block}-{village}-{status}.txt")
    with open(filename, 'w') as file:
        file.write(f"District: {district}\nBlock: {block}\nVillage: {village}\nStatus: {status}")

def get_next_indices(scraped_gps, district_index, block_index, gp_index):
    if scraped_gps:
        last_scraped_gp = scraped_gps[-1]
        try:
            district_index = int(last_scraped_gp[4])
            block_index = int(last_scraped_gp[5])
            gp_index = int(last_scraped_gp[6]) + 1
        except ValueError:
            print("Error parsing indices from CSV. Ensure the CSV file contains integer indices.")
            district_index, block_index, gp_index = 0, 0, 0
    return district_index, block_index, gp_index

@dramatiq.actor(queue_name="scrape-queue")
def scrape_gp(url, state_index, district_index, block_index, gp_index, csv_file_path):
    driver = None
    try:
        # Initialize driver 
        driver = get_driver()
        wait = WebDriverWait(driver, 20)

        # Read previously scraped GPs to determine the next gp
        scraped_gps = read_scraped_gps(SCRAPED_GP_FILE_PATH)
        district_index, block_index, gp_index = get_next_indices(scraped_gps, district_index, block_index, gp_index)

        print(f"Starting scrape for state_index={state_index}, district_index={district_index}, block_index={block_index}, gp_index={gp_index}")
        
        # Navigate to the initial URL
        driver.get(url)
        time.sleep(5)
        
        # Select state
        state = wait.until(EC.presence_of_element_located((By.XPATH, "/html/body/div[4]/form/div[2]/div/table/tbody/tr/td/div/table/tbody/tr[29]/td[2]/a")))
        state.click()
        time.sleep(5)

        # Select district
        
        districts = wait.until(EC.presence_of_all_elements_located((By.XPATH, "//table[@id='example']/tbody/tr")))
        destroyDatatable(driver)
        time.sleep(5)
        districts = wait.until(EC.presence_of_all_elements_located((By.XPATH, "//table[@id='example']/tbody/tr")))
        dist = len(districts)
        print("Number of districts:", dist)
        district = districts[district_index]
        district_name = district.find_elements(By.TAG_NAME, "td")[1].text.strip()
        district_link = district.find_element(By.TAG_NAME, "a")
        print(f"Selecting district: {district_name}")
        district_link.click()

        # Select block
        blocks = wait.until(EC.presence_of_all_elements_located((By.XPATH, "//table[@id='example']/tbody/tr")))
        destroyDatatable(driver)
        time.sleep(5)
        blocks = wait.until(EC.presence_of_all_elements_located((By.XPATH, "//table[@id='example']/tbody/tr")))
        blk = len(blocks)
        print("Number of blocks:", blk)
        block = blocks[block_index]
        block_name = block.find_elements(By.TAG_NAME, "td")[1].text.strip()
        block_link = block.find_element(By.TAG_NAME, "a")
        print(f"Selecting block: {block_name}")
        block_link.click()

        # Select GP
        
        gps = wait.until(EC.presence_of_all_elements_located((By.XPATH, "//table[@id='example']/tbody/tr")))
        destroyDatatable(driver)
        time.sleep(5)
        gps = wait.until(EC.presence_of_all_elements_located((By.XPATH, "//table[@id='example']/tbody/tr")))
        gpt = len(gps)
        print("Number of gps:", gpt)
        gp = gps[gp_index]
        gp_name = gp.find_elements(By.TAG_NAME, "td")[1].text.strip()
        gp_link = gp.find_element(By.TAG_NAME, "a")
        print(f"Selecting GP: {gp_name}")
        gp_link.click()

        # Wait for the village table to load
        wait.until(EC.presence_of_element_located((By.ID, "example")))
        
        
        print(f"Scraping villages for GP: {gp_name}")
        soup = BeautifulSoup(driver.page_source, "html.parser")

        # Check if the site has crashed
        if check_site_crash(driver):
            print("Site appears to be crashed")
            driver.quit()
            return None

        # Extract form data
        state_name = extract_text(soup, "stateName")
        district_name = extract_text(soup, "districtName")
        block_name = extract_text(soup, "blockName")
        gp_name = extract_text(soup, "grampanchayatName")
        
        print(f"Processing villages in {state_name} > {district_name} > {block_name} > {gp_name}")

        # Process village data
        village_rows = soup.select("table#example tbody tr")
        data_rows = []
        
        print(f"Found {len(village_rows)} village rows to process")

        for i, row in enumerate(village_rows):
            try:
                cols = row.find_all("td")
                
                # Skip rows with insufficient columns
                if len(cols) < 2:
                    print(f"Skipping row {i+1}: Insufficient columns ({len(cols)})")
                    continue
                
                # Extract village name from the correct column (index 1)
                village_name = cols[1].text.strip()
                
                print(f"Processing village: {village_name}")
                data_rows.append([state_name, district_name, block_name, gp_name, village_name])

                # Write status file for each village
                write_status_file(district_name, block_name, village_name, "scraped", DATA_DIR)
            except Exception as e:
                print(f"Error processing village row {i+1}: {str(e)}")
                # Continue with next row instead of failing entire function
                continue

        # Write all collected data to CSV
        if data_rows:
            print(f"Writing {len(data_rows)} villages to CSV")
            write_to_csv(SCRAPED_VILLAGES_FILE_PATH, data_rows)
            write_scraped_gp(SCRAPED_GP_FILE_PATH, [state_name, district_name, block_name, gp_name, district_index, block_index, gp_index])
            print(f"Successfully added {len(data_rows)} villages for {gp_name}")

            # Indexes all the gps that have scraped 
            gp_index += 1
            if gp_index >= len(gps):
                gp_index = 0
                block_index += 1
                if block_index >= len(blocks):
                    block_index = 0
                    district_index += 1
                    if district_index >= len(districts):
                        print("Scraping completed for all districts, blocks, and GPs")
                        return None

            print(f"Scheduling next scraping task: district_index={district_index}, block_index={block_index}, gp_index={gp_index}")
            scrape_gp.send(url, state_index, district_index, block_index, gp_index, csv_file_path)
        else:
            print(f"No valid villages found for {gp_name}")

        return None
        
    except Exception as e:
        print(f"Error in scrape_gp: {str(e)}")
        return None
        
    finally:
        # Always make sure to close the driver
        if driver:
            print("Closing browser")
            driver.quit()