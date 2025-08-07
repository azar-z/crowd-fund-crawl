import time
from typing import List

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

from crawler import Crawler
from static_crawlers.models.platform import Platform
from static_crawlers.models.project import Project


class Hamashena(Crawler):
    platform = Platform.HAMASHENA

    def find_new_projects(self) -> List[Project]:
        options = Options()
        # options.add_argument("--headless")
        # options.add_argument("--window-size=1920,1080")
        # options.add_argument("--disable-gpu")
        # options.add_argument("--no-sandbox")
        # options.add_argument("--disable-dev-shm-usage")
        # options.add_argument("--disable-blink-features=AutomationControlled")
        driver = webdriver.Chrome(options=options)

        driver.get("https://hamashena.ir/projects")
        time.sleep(10)

        soup = BeautifulSoup(driver.page_source, "html.parser")
        driver.close()
        # driver.quit()

        projects = []
        base_url = "https://hamashena.ir"

        project_cards = soup.find_all("div", class_="MuiCard-root")

        for card in project_cards:
            try:
                # URL
                url_tag = card.find("a", href=True)
                url = base_url + url_tag["href"] if url_tag else None

                # Project Name
                name_tag = card.find("span", class_="truncate-two")
                name = name_tag.get_text(strip=True) if name_tag else None

                # Company
                company_tag = card.find("span", string=lambda s: s and "متقاضی سرمایه" in s)
                if company_tag:
                    company = company_tag.find_next_sibling(text=True)
                    company = company.strip() if company else None
                else:
                    company = None

                # Profit
                profit_tag = card.find("span", string=lambda s: s and "سود پیشبینی شده" in s)
                if profit_tag:
                    profit = profit_tag.find_next_sibling(text=True)
                    profit = profit.strip() if profit else None
                else:
                    profit = None

                # Guarantee
                guarantee_block = card.find("span", string=lambda s: s and "تضامین" in s)
                if guarantee_block:
                    guarantee = guarantee_block.find_next_sibling().get_text(strip=True)
                else:
                    guarantee = None

                # Remained time
                time_container = card.find("span", class_="muirtl-5y80py")
                remained_time = time_container.get_text(strip=True) if time_container else None

                if all([company, name, profit, url]):
                    if remained_time != '00:0000':
                        projects.append(Project(company, name, profit, guarantee, url))

            except Exception as e:
                # skip malformed project card
                continue

        return projects

