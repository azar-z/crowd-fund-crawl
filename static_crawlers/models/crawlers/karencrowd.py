import time

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from .crawler import TwoStepCrawler
from static_crawlers.models.platform import Platform
from static_crawlers.models.project import Project


class KarenCrowd(TwoStepCrawler):
    platform = Platform.KAREN_CROWD

    def get_project_urls(self):
        # Set up Chrome options for headless mode
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        # Create a new instance of the Chrome driver
        driver = webdriver.Chrome(options=options)

        try:
            # Load the page
            url = "https://www.karencrowd.com/plans"
            driver.get(url)

            # Click the button to load relevant content
            button_xpath = '//*[@id="tabs-with-icons-item-2"]'
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, button_xpath))).click()

            # Wait for the page to fully load
            time.sleep(10)

            # Extract the HTML of the page
            page_source = driver.page_source
            soup = BeautifulSoup(page_source, "html.parser")

            # Initialize the list to collect visible project URLs
            project_urls = []

            # Locate project elements that are currently visible # changed using gpt (not to include invisible items)
            project_elements = driver.find_elements(By.XPATH,
                                                    "//div[contains(@class, 'flex') and contains(@class, 'relative') and contains(@class, 'bg-white')]")

            for project_element in project_elements:
                # Check if the element is visible
                if project_element.is_displayed():
                    # Parse the HTML of the visible element with BeautifulSoup
                    project_html = project_element.get_attribute('outerHTML')
                    project_soup = BeautifulSoup(project_html, 'html.parser')

                    # Locate the anchor link for project details and extract the URL if it exists
                    project_link = project_soup.find("a", href=True)
                    if project_link:
                        project_urls.append(project_link['href'])

            return project_urls

        finally:
            # Close the Selenium driver
            driver.quit()

    def get_project_data(self, url: str) -> Project:
        # Set up headless Chrome options
        options = Options()
        options.add_argument("--headless")  # Run browser in background
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        # Launch the browser
        driver = webdriver.Chrome(options=options)

        try:
            # Open the URL and wait for the page to load fully
            driver.get(url)
            time.sleep(5)  # Adjust this wait time as necessary for the page to load

            # Parse the page source with BeautifulSoup
            soup = BeautifulSoup(driver.page_source, 'html.parser')

            # Extract the project title
            title_element = soup.select_one(".plan-overlay .text-sm.md\\:text-2xl.font-bold")
            title = title_element.get_text(strip=True) if title_element else None

            # Extract the company title
            company_element = soup.select_one(".plan-overlay .text-md.md\\:text-md")
            company = company_element.get_text(strip=True) if company_element else None

            # Extract the profit percentage
            profit_element = soup.find("h3", string="سود پیش‌بینی شده")
            profit = None
            if profit_element:
                profit_value = profit_element.find_next_sibling("span")
                if profit_value:
                    profit = profit_value.get_text(strip=True).replace("٪", "").strip()

            # Extract the guarantee information
            guarantee_element = soup.find("h3", string="وثایق")
            guarantee = None
            if guarantee_element:
                guarantee_value = guarantee_element.find_next_sibling("span")
                if guarantee_value:
                    guarantee = guarantee_value.get_text(strip=True)

            # Create and return the Project object
            return Project(company, title, profit, guarantee, url)

        finally:
            # Close the browser
            driver.quit()
