from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class BasePage:
    def __init__(self, selenium, base_url):
        self.selenium = selenium
        self.base_url = base_url
        self.wait = WebDriverWait(selenium, 15)  # Increased timeout for stability
    
    def find_element(self, by, value):
        return self.wait.until(EC.presence_of_element_located((by, value)))
    
    def find_clickable_element(self, by, value):
        return self.wait.until(EC.element_to_be_clickable((by, value)))