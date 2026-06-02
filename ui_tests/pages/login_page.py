from selenium.webdriver.common.by import By
from ui_tests.pages.base_page import BasePage

class LoginPage(BasePage):
    URL = "/"
    
    # Exact locators from your HTML
    EMAIL_INPUT = (By.ID, "id_email")
    PASSWORD_INPUT = (By.ID, "id_password")
    LOGIN_BUTTON = (By.CSS_SELECTOR, "input[type='submit'][value='Login']")
    REGISTER_LINK = (By.CSS_SELECTOR, "a.btn-success[href='/register/']")
    
    def open(self):
        self.selenium.get(f"{self.base_url}{self.URL}")
    
    def login(self, email, password):
        self.find_element(*self.EMAIL_INPUT).clear()
        self.find_element(*self.EMAIL_INPUT).send_keys(email)
        self.find_element(*self.PASSWORD_INPUT).clear()
        self.find_element(*self.PASSWORD_INPUT).send_keys(password)
        self.find_clickable_element(*self.LOGIN_BUTTON).click()