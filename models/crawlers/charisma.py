from typing import List

import requests as requests

from crawler import Crawler
from models.platform import Platform
from models.project import Project


class Charisma(Crawler):
    platform = Platform.CHARISMA

    GUARANTEE_TRANSLATIONS = {
        "STOCK": "بدون تضمین سود و با تضمین توثیق سهام اصل سرمایه",
        "PAYMENT_GUARANTEE": "بدون تضمین سود و با تضمین ضمانت نامه انجام تعهدات اصل سرمایه",
        "PAYMENT_GUARANTEE_BANK": "بدون تضمین سود و با تضمین ضمانت نامه تعهد پرداخت بانکی اصل سرمایه",
        "CHEQUE": "بدون تضمین سود بدون تضمین اصل سرمایه",
        "PAYMENT_GUARANTEE_SANDOGH": "بدون تضمین سود و با تضمین ضمانت نامه تعهد پرداخت صندوق اصل سرمایه",
    }

    def find_new_projects(self) -> List[Project]:
        url = "https://crowd.charisma.ir/api/v1/sp/executePermit?spName=landing_plan_page"
        payload = {
            "page": 0,
            "size": 10,
            "sortBy": None,
            # "planStatus": None,
            "planStatus": "START_FUNDING",
            "profit": None,
            "industry": None
        }

        response = requests.post(url, json=payload)
        response.raise_for_status()

        data = response.json()
        projects_data = data.get("#result-set-1", [])
        projects = []

        for item in projects_data:
            company = item.get("compnany_name")
            name = item.get("persian_name")
            profit = item.get("benefitPredict")
            guarantee_key = item.get("guarantee")
            guarantee = self.GUARANTEE_TRANSLATIONS.get(guarantee_key, "نامشخص")
            project_id = item.get("id")
            project_url = f"https://crowd.charisma.ir/main/plan-details/{project_id}"

            project = Project(company, name, profit, guarantee, project_url)
            projects.append(project)

        return projects
