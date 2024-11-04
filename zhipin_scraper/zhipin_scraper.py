from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import csv
import os
import datetime
from webdriver_manager.chrome import ChromeDriverManager

def setup_driver():
    # Configure Selenium with options
    options = Options()
    # Uncomment headless mode if you want the browser to run in the background
    # options.headless = True
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36")
    
    # Use WebDriverManager to handle driver path setup
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver

def login_to_zhipin(driver):
    try:
        # Check if the user is already logged in by looking for the user avatar
        driver.get("https://www.zhipin.com/web/user")
        if len(driver.find_elements(By.CLASS_NAME, 'user-avatar')) > 0:
            print("Already logged in.")
            return
        
        # If not logged in, proceed with the login process
        driver.get("https://www.zhipin.com/web/user/?ka=header-login")
        print("Navigating to login page...")
        
        # Pause to allow the user to log in manually
        input("Press Enter here when logged in successfully...")
        print("Login successful.")
    except Exception as e:
        print(f"Login failed: {e}")
        # Do not quit the driver here to allow further inspection
        raise e

def fetch_page_content(driver):
    # Scroll down the page a fixed number of times to load more job listings
    for _ in range(4):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        print("Scrolling to load more data...")
        time.sleep(2)  # Small delay to allow content to load
    
    page_source = driver.page_source
    return BeautifulSoup(page_source, 'html.parser')

def convert_unicode_salary(unicode_salary):
    # Define mapping from special unicode characters to numbers
    unicode_mapping = {
        '\ue032': '1',
        '\ue033': '2',
        '\ue034': '3',
        '\ue035': '4',
        '\ue036': '5',
        '\ue037': '6',
        '\ue038': '7',
        '\ue039': '8',
        '\ue040': '9',
        '\ue031': '0'
    }
    
    # Replace unicode characters with their corresponding numbers
    for key, value in unicode_mapping.items():
        unicode_salary = unicode_salary.replace(key, value)
    
    return unicode_salary

def extract_jobs(soup):
    if soup is None:
        return []
    jobs = []
    # Find each job card container based on observed HTML structure
    for job_card in soup.find_all('div', class_='job-card-wrap'):
        # Extract job title
        title_tag = job_card.find('a', class_='job-name')
        title = title_tag.get_text(strip=True) if title_tag else None
        
        # Extract job salary and convert unicode characters to readable format
        salary_tag = job_card.find('span', class_='job-salary')
        salary = salary_tag.get_text(strip=True) if salary_tag else None
        if salary:
            salary = convert_unicode_salary(salary)  # Convert special unicode characters to numbers
        
        # Extract job tags (like experience, education, etc.)
        tags = []
        tag_list = job_card.find('ul', class_='tag-list')
        if tag_list:
            tags = [li.get_text(strip=True) for li in tag_list.find_all('li')]
        
        # Extract company location
        location_tag = job_card.find('span', class_='company-location')
        location = location_tag.get_text(strip=True) if location_tag else None

        # Extract boss name
        boss_tag = job_card.find('span', class_='boss-name')
        boss_name = boss_tag.get_text(strip=True) if boss_tag else None
        
        # Append the extracted data as a dictionary
        jobs.append({
            'title': title,
            'salary': salary,
            'tags': ', '.join(tags),  # Join tags into a single string
            'location': location,
            'boss_name': boss_name
        })
    return jobs

def save_to_csv(data, filename):
    """Function to save job data to a CSV file."""
    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=["title", "salary", "tags", "location", "boss_name"])
        writer.writeheader()
        writer.writerows(data)
    print(f"Data saved to {filename}")

def load_previous_jobs(filename):
    """Function to load previous jobs from a CSV file."""
    if not os.path.exists(filename):
        return []
    
    with open(filename, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        return [row for row in reader]

def filter_new_jobs(new_jobs, previous_jobs):
    """Function to filter out jobs that are already present in the previous file."""
    previous_jobs_set = {frozenset(job.items()) for job in previous_jobs}
    return [job for job in new_jobs if frozenset(job.items()) not in previous_jobs_set]

def crawl_zhipin(url, max_pages=1):
    driver = setup_driver()
    all_jobs = []
    
    try:
        login_to_zhipin(driver)
        print(f"Crawling page...")
        driver.get(url)
        # Locate all the tab elements
        tabs = driver.find_elements(By.CLASS_NAME, 'recommend-job-btn')
        
        for tab_index, tab in enumerate(tabs):
            try:
                # Click on the tab to switch to that category
                print(f"Switching to tab {tab_index + 1}...")
                tab.click()
                time.sleep(2)  # Give the page some time to load
                
                # Fetch content for the current tab
                soup = fetch_page_content(driver)
                jobs = extract_jobs(soup)
                all_jobs.extend(jobs)
                
                # Debugging: Output the number of jobs found on the tab
                print(f"Number of jobs found in tab {tab_index + 1}: {len(jobs)}")
            except Exception as e:
                print(f"Error processing tab {tab_index + 1}: {e}")
                continue
    finally:
        driver.quit()  # Close the driver

    # Load previous jobs and filter new jobs
    all_records_filename = "zhipin_jobs_all.csv"
    previous_jobs = load_previous_jobs(all_records_filename)
    new_jobs = filter_new_jobs(all_jobs, previous_jobs)
    
    # Save the new jobs to a CSV with timestamp
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    new_jobs_filename = f"zhipin_jobs_new_{timestamp}.csv"
    save_to_csv(new_jobs, new_jobs_filename)
    
    # Update the file that stores all records
    updated_jobs = previous_jobs + new_jobs
    save_to_csv(updated_jobs, all_records_filename)
    
    return new_jobs

# Start crawling
jobs = crawl_zhipin("https://www.zhipin.com/web/geek/job-recommend")
for job in jobs:
    print(job)
