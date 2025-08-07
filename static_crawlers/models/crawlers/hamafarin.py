import time

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from .crawler import TwoStepCrawler
from static_crawlers.models.platform import Platform
from static_crawlers.models.project import Project


class Hamafarin(TwoStepCrawler):
    platform = Platform.HAMAFARIN

    def get_project_urls(self):
        url = "https://hamafarin.ir/businessplans"
        # Set options for headless browser
        options = Options()
        options.add_argument('--headless')  # Run in headless mode
        options.add_argument('--no-sandbox')  # Bypass OS security model
        options.add_argument('--disable-dev-shm-usage')  # Overcome limited resource problems

        # Create a new instance of the Chrome driver
        driver = webdriver.Chrome(options=options)

        # Open the given URL
        driver.get(url)

        # Wait for the page to load completely (you may adjust the sleep time if needed)
        time.sleep(3)

        # Parse the page source with BeautifulSoup
        soup = BeautifulSoup(driver.page_source, 'html.parser')

        # Close the browser
        driver.quit()

        # Find all relevant anchor tags within the specific divs containing the URLs
        project_elements = soup.select('.col-xl-4 .card a.text-dark')

        # Extract the URLs and convert them to absolute URLs
        base_url = "https://hamafarin.ir"
        urls = [base_url + element['href'] for element in project_elements if 'href' in element.attrs]

        return urls

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

            # Extract the company title
            company_element = soup.find("span", string="نام شرکت : ")
            company = None
            if company_element:
                company = company_element.find_next("strong").get_text(strip=True)

            # Extract the project title
            name_element = soup.find("span", string="موضوع تامین مالی جمعی: ")
            name = None
            if name_element:
                name = name_element.find_next_sibling(text=True).strip()

            # Extract the profit percentage
            profit_element = soup.find("span", string="پیش بینی میزان سود: ")
            profit = None
            if profit_element:
                profit_text = profit_element.find_next_sibling("span").get_text(strip=True)
                profit = profit_text.replace("%", "").replace("سالیانه", "").strip()

            # Extract the guarantee information
            guarantee_element = soup.find("span", string="وثایق:")
            guarantee = None
            if guarantee_element:
                guarantee = guarantee_element.find_next("strong").get_text(strip=True)

            # Create and return the Project object
            return Project(company, name, profit, guarantee, url)

        finally:
            # Close the browser
            driver.quit()
