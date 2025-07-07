import time
from typing import List

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from urllib.parse import urljoin

from crawler import Crawler
from models.platform import Platform
from models.project import Project


class Investorun(Crawler):
    platform = Platform.INVESTORUN

    def find_new_projects(self) -> List[Project]:
        base_url = "https://www.investorun.com"
        options = Options()
        options.add_argument("--headless")

        driver = webdriver.Chrome(options=options)
        driver.get(f"{base_url}/companies")
        wait = WebDriverWait(driver, 10)

        try:
            invest_tab = wait.until(
                EC.element_to_be_clickable((
                    By.XPATH, "//button[contains(text(), 'در حال جذب سرمایه')]"
                ))
            )
            invest_tab.click()
        except Exception as e:
            print(f"Could not click the investment tab: {e}")
            return []

        time.sleep(10)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        driver.quit()

        projects = []

        project_links = soup.find_all("a", href=True)
        for link in project_links:
            href = link['href']
            if not href.startswith("/company/"):
                continue
            print(href)
            name_tag = link.find("h3")
            name = name_tag.get_text(strip=True) if name_tag else None

            company = name
            profit = None
            guarantee = None

            detail_sections = link.find_all("div", class_="flex")
            for div in detail_sections:
                label = div.find("span", class_="text-xs")
                value = div.find("span", class_="block")
                if not label or not value:
                    continue
                label_text = label.get_text(strip=True)
                value_text = value.get_text(strip=True)

                if "سود پیش بینی شده طرح" in label_text:
                    profit = value_text
                elif "تضمين" in value_text or "ضمانت" in value_text or "تعهد" in value_text:
                    guarantee = value_text

            full_url = urljoin(base_url, href)

            if all([company, name, profit, guarantee]):
                project = Project(company, name, profit, guarantee, full_url)
                projects.append(project)

        return projects
