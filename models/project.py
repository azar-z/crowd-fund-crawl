from enum import Enum

from .platform import Platform


class ProjectStatus(Enum):
    ACTIVE = 1
    FINISHED = 2


class Project:
    def __init__(self, company, name, profit, guarantee, url, status=ProjectStatus.ACTIVE, platform=None):
        self.platform = platform
        self.company = company
        self.name = name
        self.profit = profit
        self.guarantee = guarantee
        self.url = url
        self.status = status

    def set_platform(self, platform: Platform):
        self.platform = platform

    def __str__(self):
        return f"company={self.company}, name={self.name}, profit={self.profit}, guarantee={self.guarantee}," \
               f" url={self.url}, platform={self.platform}"

    # TODO: add rwo to db or update and old row
    def save(self):
        print(f"project saved: {self}\n")
