from selenium.webdriver.common.by import By
from ui_tests.pages.base_page import BasePage

class RegisterPage(BasePage):
    URL = "/register/"
    
    # Exact locators from your HTML
    FIRST_NAME_INPUT = (By.ID, "id_firstname")
    LAST_NAME_INPUT = (By.ID, "id_lastname")
    EMAIL_INPUT = (By.ID, "id_email")
    PASSWORD_FIRST = (By.ID, "id_password_first")
    PASSWORD_SECOND = (By.ID, "id_password_second")
    REGISTER_BUTTON = (By.CSS_SELECTOR, "input[type='submit'][value='Register']")
    ERROR_MESSAGES = (By.CLASS_NAME, "errorlist")  # Django's default error container
    
    def open(self):
        self.selenium.get(f"{self.base_url}{self.URL}")
    
    def register(self, email, password, confirm_password, first_name, last_name):
        self.find_element(*self.FIRST_NAME_INPUT).clear()
        self.find_element(*self.FIRST_NAME_INPUT).send_keys(first_name)
        
        self.find_element(*self.LAST_NAME_INPUT).clear()
        self.find_element(*self.LAST_NAME_INPUT).send_keys(last_name)
        
        self.find_element(*self.EMAIL_INPUT).clear()
        self.find_element(*self.EMAIL_INPUT).send_keys(email)
        
        self.find_element(*self.PASSWORD_FIRST).clear()
        self.find_element(*self.PASSWORD_FIRST).send_keys(password)
        
        self.find_element(*self.PASSWORD_SECOND).clear()
        self.find_element(*self.PASSWORD_SECOND).send_keys(confirm_password)
        
        self.find_clickable_element(*self.REGISTER_BUTTON).click()
    
    def submit_empty_form(self):
        self.find_clickable_element(*self.REGISTER_BUTTON).click()
        
    def get_errors(self):
        errors = self.selenium.find_elements(*self.ERROR_MESSAGES)
        return [e.text for e in errors]