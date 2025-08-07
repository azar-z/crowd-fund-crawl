from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time

from crawler import TwoStepCrawler
from selenium.webdriver.common.by import By
from static_crawlers.models.platform import Platform
from static_crawlers.models.project import Project


class StarTamin(TwoStepCrawler):
    platform = Platform.STAR_TAMIN

    def get_project_urls(self):
        base_url = "https://startamin.ir"
        target_url = f"{base_url}/InvestProjects"

        # Set up headless Chrome
        options = Options()
        options.add_argument("--headless")
        driver = webdriver.Chrome(options=options)

        try:
            driver.get(target_url)

            # Wait for up to 10 seconds for presence of any element on the page
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "a"))
            )

            # Wait an extra second to ensure full load
            time.sleep(10)

            soup = BeautifulSoup(driver.page_source, "html.parser")
            project_links = soup.find_all("a", class_="btn btn-md btn-secondary-detail cursor-p w-100")

            urls = [base_url + link.get("href") for link in project_links if link.get("href")]
            print(urls)

            return urls
        finally:
            driver.quit()

    def get_project_data(self, url: str) -> Project:
        options = Options()
        options.add_argument("--headless")
        driver = webdriver.Chrome(options=options)

        try:
            driver.get(url)
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "h2")))
            time.sleep(10)  # Additional wait for dynamic content

            soup = BeautifulSoup(driver.page_source, "html.parser")

            # Project name
            name_tag = soup.find("h2")
            name = name_tag.get_text(strip=True) if name_tag else ""

            # Company name
            company = ""
            all_divs = soup.find_all("div")
            for div in all_divs:
                if div.get_text().strip().startswith("سرمایه پذیر"):
                    lines = list(div.stripped_strings)
                    if len(lines) >= 2:
                        company = lines[1]
                        break

            # Profit (contains text like "پیش بینی سود" and percentage)
            profit_divs = soup.find_all("div")
            profit = ""
            for div in profit_divs:
                if div.get_text().strip().startswith("پیش بینی سود"):
                    span = div.find("span")
                    if span:
                        profit = span.get_text(strip=True)
                        break

            # Guarantee (div containing img with src that includes 'tik')
            guarantee = ""
            for div in soup.find_all("div"):
                img = div.find("img")
                if img and "tik" in img.get("src", ""):
                    guarantee = div.get_text(strip=True)
                    break

            return Project(company=company, name=name, profit=profit, guarantee=guarantee, url=url)

        finally:
            driver.quit()

