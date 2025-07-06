from typing import List

import requests as requests

from crawler import Crawler
from models.platform import Platform
from models.project import Project


class ZarinCrowd(Crawler):
    platform = Platform.ZARIN_CROWD

    def find_new_projects(self) -> List[Project]:
        url = "https://zarincrowd.com/api/v1/Projects/AllPaginated?internalStatus=1&pageNumber=1&pageSize=12"
        response = requests.get(url)
        response.raise_for_status()

        projects_data = response.json().get("data", {}).get("items", [])
        projects = []

        for item in projects_data:
            company = item.get("projectCompanyName", "").strip()
            name = item.get("persianName", "").strip()
            profit = f"%{item.get('profitPercent', 0)}"
            guarantee = item.get("guarantor", "").strip()
            project_id = item.get("id")
            project_url = f"https://zarincrowd.com/projects/{project_id}"

            project = Project(
                company=company,
                name=name,
                profit=profit,
                guarantee=guarantee,
                url=project_url,
                platform=self.platform
            )
            projects.append(project)

        return projects
