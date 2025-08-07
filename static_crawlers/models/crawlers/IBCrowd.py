from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from .crawler import TwoStepCrawler
from static_crawlers.models.platform import Platform
from static_crawlers.models.project import Project


class IBCrowd(TwoStepCrawler):
    platform = Platform.IB_CROWD

    def get_project_urls(self):
        # Set up Selenium WebDriver with headless option
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")

        # Create the driver
        driver = webdriver.Chrome(options=options)
        urls = []
        try:
            # Open the page
            url = "https://www.ibcrowd.ir/opportunities/all"
            driver.get(url)

            # Wait for the page to fully load
            WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CLASS_NAME, "card-img-top"))
            )

            # Find all clickable div elements
            elements = driver.find_elements(By.CLASS_NAME, "card-img-top")

            for index in range(len(elements)):
                # Re-fetch elements because the page reloads after clicking
                elements = driver.find_elements(By.CLASS_NAME, "card-img-top")
                # Click on the current element
                elements[index].click()

                # Wait for redirection to complete
                WebDriverWait(driver, 10).until(
                    EC.url_changes(url)
                )

                # Capture the new URL
                urls.append(driver.current_url)

                # Go back to the original page
                driver.back()

                # Wait for the page to reload
                WebDriverWait(driver, 10).until(
                    EC.presence_of_all_elements_located((By.CLASS_NAME, "card-img-top"))
                )

            return urls

        finally:
            # Ensure the driver quits even if an error occurs
            driver.quit()

    def get_project_data(self, url: str) -> Project:
        return None
