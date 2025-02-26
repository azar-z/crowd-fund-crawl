import time

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from .crawler import TwoStepCrawler
from models.platform import Platform
from models.project import Project


class Razavi(TwoStepCrawler):
    platform = Platform.RAZAVI

    def get_project_urls(self):
        pass

    def get_project_data(self, url: str) -> Project:
        return None
