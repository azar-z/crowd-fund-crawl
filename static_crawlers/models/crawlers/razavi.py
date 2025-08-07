from .crawler import TwoStepCrawler
from static_crawlers.models.platform import Platform
from static_crawlers.models.project import Project


class Razavi(TwoStepCrawler):
    platform = Platform.RAZAVI

    def get_project_urls(self):
        pass

    def get_project_data(self, url: str) -> Project:
        return None
