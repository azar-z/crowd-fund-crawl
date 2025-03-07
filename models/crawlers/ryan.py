from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time

from .crawler import TwoStepCrawler
from selenium.webdriver.common.by import By
from models.platform import Platform
from models.project import Project


class Ryan(TwoStepCrawler):
    platform = Platform.RYAN

    def get_project_urls(self):
        base_url = "https://ryan-funding.ir"
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        driver = webdriver.Chrome(options=options)
        driver.get(base_url)
        time.sleep(10)  # Wait for the page to fully load

        soup = BeautifulSoup(driver.page_source, "html.parser")
        driver.quit()

        urls = []
        for link in soup.find_all("a", class_="MuiButtonBase-root"):
            href = link.get("href")
            if href and href.startswith("/startup/"):
                urls.append(base_url + href)

        return urls

    def get_project_data(self, url: str) -> Project:
        # Set up Selenium WebDriver with headless option
        options = Options()
        options.add_argument("--headless")
        driver = webdriver.Chrome(options=options)

        try:
            driver.get(url)
            time.sleep(5)  # Wait for the page to fully load

            # Parse page source with BeautifulSoup
            close_button = driver.find_element(By.CSS_SELECTOR, '[data-testid="CloseSharpIcon"]')
            if close_button:
                # Click the close button
                close_button.click()

            time.sleep(10)

            soup = BeautifulSoup(driver.page_source, "html.parser")

            # Extract project name
            name_element = soup.find("h2", class_="MuiTypography-root MuiTypography-h2 ryan-1j3kx9x")
            name = name_element.text.strip() if name_element else "N/A"

            # Extract profit
            profit_element = soup.find("p", class_="MuiTypography-root MuiTypography-body1 ryan-1scfei1",
                                       string="پیش‌بینی سود یک ساله")
            profit = profit_element.find_next_sibling("p").text.strip() if profit_element else "N/A"

            # Extract company name
            company_text = 'نماد طرح'
            company_div = soup.find('h4', text=company_text)
            next_span = company_div.find_next('span').find_next('span')
            company = next_span.text.strip() if next_span else "N/A"

            # Extract guarantee
            guarantee_icon = soup.find('svg', attrs={'data-testid': 'BeachAccessIcon'})
            guarantee = guarantee_icon.find_next("h4").text.strip() if guarantee_icon else "N/A"

            return Project(company, name, profit, guarantee, url)
        finally:
            driver.quit()

