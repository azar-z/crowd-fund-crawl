import time

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from .crawler import TwoStepCrawler
from models.platform import Platform
from models.project import Project


class Dongi(TwoStepCrawler):
    platform = Platform.DONGI

    def get_project_urls(self):
        # Set up Chrome options to run in the background (headless mode)
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        driver = webdriver.Chrome(options=options)

        try:
            # Load the page
            # url = "https://dongi.ir/discover/filter/?status%5B%5D=5&order=recently-launched"
            url = "https://dongi.ir/discover/"
            driver.get(url)

            time.sleep(3)

            # Extract the HTML of the page
            page_source = driver.page_source

            # Parse the HTML with BeautifulSoup
            soup = BeautifulSoup(page_source, "html.parser")

            # Find all project elements and extract URLs
            project_urls = []
            project_elements = soup.find_all("div", class_="projectItem")

            for project in project_elements:
                # Locate the link within each project that leads to the project details
                project_link = project.find("a", href=True)
                if project_link:
                    # Append the full URL for each project to the list
                    full_url = f"https://dongi.ir{project_link['href']}"
                    project_urls.append(full_url)

            return project_urls

        finally:
            # Close the Selenium driver
            driver.quit()

    def get_project_data(self, url: str) -> Project:

        # Set up Selenium with Chrome options
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')

        # Initialize the driver
        driver = webdriver.Chrome(options=options)
        driver.get(url)

        # Wait for the page to load
        time.sleep(5)  # Wait for the page to load, adjust if necessary

        # Parse the page content with BeautifulSoup
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        driver.quit()

        # Extract data using BeautifulSoup
        try:
            company = soup.select_one('.visible-sm.visible-md.visible-lg a').get_text(strip=True)
            name = soup.select_one('.visible-sm.visible-md.visible-lg h3').get_text(strip=True)
            profit_text = soup.select_one('.extendedTooltip .txt-bold').get_text(strip=True)
            profit = profit_text.replace('%',
                                         '') if '%' in profit_text else None  # changed to remove int type conversion
            guarantee = soup.select_one('.pull-left .font12.padd0').get_text(strip=True)  # changed using gpt

            # Return a Project instance with extracted data
            return Project(company, name, profit, guarantee, url)
        except AttributeError as e:
            print("Error extracting data:", e)
            return None
