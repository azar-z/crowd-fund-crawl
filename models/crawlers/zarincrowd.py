import time
from typing import List

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup

from crawler import Crawler
from models.platform import Platform
from models.project import Project


class ZarinCrowd(Crawler):
    platform = Platform.ZARIN_CROWD

    def find_new_projects(self) -> List[Project]:
        options = Options()
        options.add_argument("--headless")
        driver = webdriver.Chrome(options=options)

        try:
            driver.get("https://zarincrowd.com/projects")

            # Wait for the button to be present
            # wait = WebDriverWait(driver, 10)

            # Locate the button by text
            # time.sleep(10)
            # button = driver.find_element(By.XPATH, "//button[.//span[normalize-space(text())='فعال']]")
            # button.click()

            time.sleep(10)

            soup = BeautifulSoup(driver.page_source, "html.parser")
            project_elements = soup.find_all("div",
                                             class_="flex flex-col rounded-2xl overflow-hidden border border-light-divider cursor-pointer h-full")

            projects = []
            for el in project_elements:
                try:
                    name_el = el.find("div", class_="font-bold text-xs text-dark-default mb-4")
                    name = name_el.get_text(strip=True) if name_el else ""

                    company_el = el.find_all("div",
                                             class_="flex items-center bg-light-default p-2 rounded relative group")
                    company = company_el[0].find("span").get_text(strip=True) if company_el else ""

                    profit_box = el.find("div", class_="persian-discount")
                    profit = profit_box.get_text(strip=True) if profit_box else ""

                    guarantee_el = el.find("div", class_="text-xs font-normal text-dark-default text-center mb-4")
                    guarantee = guarantee_el.get_text(strip=True) if guarantee_el else ""

                    url = "https://zarincrowd.com/projects"

                    projects.append(Project(company=company, name=name, profit=profit, guarantee=guarantee, url=url))
                except Exception:
                    print("something went wrong with one element")

            return projects

        finally:
            driver.quit()
