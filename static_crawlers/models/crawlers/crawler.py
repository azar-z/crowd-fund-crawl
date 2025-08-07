from abc import ABC, abstractmethod
from typing import List

from static_crawlers.models.platform import Platform
from static_crawlers.models.project import Project


class Crawler(ABC):
    platform: Platform

    @abstractmethod
    def find_new_projects(self) -> List[Project]:
        pass

    def save_new_projects(self):
        new_projects = self.find_new_projects()
        for project in new_projects:
            project.set_platform(self.platform)
            project.save()


class TwoStepCrawler(Crawler, ABC):
    @abstractmethod
    def get_project_urls(self):
        pass

    @abstractmethod
    def get_project_data(self, url: str) -> Project:
        pass

    def find_new_projects(self) -> List[Project]:
        new_projects = []
        urls = set(self.get_project_urls())
        for url in urls:
            try:
                project = self.get_project_data(url)
                project.set_platform(self.platform)
                new_projects.append(project)
            except Exception as e:
                print(f"something went wrong with gathering data from {url} in platform {self.platform.name}")
        return new_projects
