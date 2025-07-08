from typing import List

import requests as requests

from crawler import Crawler
from models.platform import Platform
from models.project import Project


class IFund(Crawler):
    platform = Platform.IFUND

    API_URL = "https://ifund.ir/api/projects/projects?page=1&status=11"
    BASE_URL = "https://ifund.ir/projects/"

    def find_new_projects(self) -> List[Project]:
        response = requests.get(self.API_URL)
        response.raise_for_status()  # Raise an exception for HTTP errors

        projects_data = response.json()
        result = []

        for item in projects_data:
            company = item.get("company_name", "")
            name = item.get("title", "")
            profit = item.get("percent", 0)
            guarantee = item.get("warranty_summery", "")
            slug = item.get("slug", "")
            url = f"{self.BASE_URL}{slug}" if slug else ""

            project = Project(company, name, profit, guarantee, url)
            result.append(project)

        return result
