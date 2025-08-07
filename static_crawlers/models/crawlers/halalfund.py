import time

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from .crawler import TwoStepCrawler
from static_crawlers.models.platform import Platform
from static_crawlers.models.project import Project


class HalalFund(TwoStepCrawler):
    platform = Platform.HALAL_FUND

    # TODO: filter over open projects
    def get_project_urls(self):
        # Base URL for constructing full URLs
        base_url = "https://halalfund.ir"
        target_url = "https://halalfund.ir/projects"

        # Set up Selenium WebDriver with headless option
        options = Options()
        options.add_argument("--headless")  # Run browser in headless mode
        options.add_argument("--disable-gpu")  # Disable GPU rendering
        options.add_argument("--no-sandbox")  # Prevent issues in some environments

        # Start WebDriver
        driver = webdriver.Chrome(options=options)
        try:
            # Open the target page
            driver.get(target_url)
            time.sleep(10)  # Wait for the page to fully load

            # Retrieve page source and parse with BeautifulSoup
            page_source = driver.page_source
            soup = BeautifulSoup(page_source, "html.parser")

            # Find all relevant <a> elements
            project_links = soup.find_all("a", class_="projectItemMainClassInner")

            # Extract hrefs and construct full URLs
            urls = [base_url + link.get("href") for link in project_links if link.get("href")]
            return urls
        finally:
            # Ensure WebDriver is properly closed
            driver.quit()

    def get_project_data(self, url: str) -> Project:
        # Set up Selenium WebDriver with headless option
        options = Options()
        options.add_argument("--headless")  # Run browser in headless mode
        options.add_argument("--disable-gpu")  # Disable GPU rendering
        options.add_argument("--no-sandbox")  # Prevent issues in some environments

        # Start WebDriver
        driver = webdriver.Chrome(options=options)
        try:
            # Open the target page
            driver.get(url)
            time.sleep(10)  # Wait for the page to fully load

            # Retrieve page source and parse with BeautifulSoup
            page_source = driver.page_source
            soup = BeautifulSoup(page_source, "html.parser")

            # Extract company name
            company = soup.find("h5", string="نام شرکت :").find_next("p").text.strip()

            # Extract project title
            title = soup.find("div", class_="projectTitleText").find("h1").text.strip()

            # Extract profit (annual predicted profit)
            profit_element = soup.find("p", string="پیش بینی سود پلن (سالیانه)")
            if profit_element:
                profit = profit_element.find_next("div", class_="rewardMinimum").text.strip()
            else:
                profit = None  # If no profit element exists

            # added this
            guarantee = None

            # Return the Project object with extracted data
            return Project(company, title, profit, guarantee)

        finally:
            # Ensure WebDriver is properly closed
            driver.quit()
