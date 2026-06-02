from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from ui_tests.pages.base_page import BasePage

class ProfilePage(BasePage):
    URL = "/profile/update/"
    
    # Use By.NAME as it's 100% reliable for Django ModelForms
    PHONE_INPUT = (By.NAME, "phone")
    ADDRESS_INPUT = (By.NAME, "address")
    PINCODE_INPUT = (By.NAME, "pincode")
    DOB_INPUT = (By.NAME, "date_of_birth")
    
    # Flexible button locator
    UPDATE_BUTTON = (By.CSS_SELECTOR, "button[type='submit'], input[type='submit']")
    
    def open(self):
        self.selenium.get(f"{self.base_url}{self.URL}")
        # Wait specifically for the phone field to prove the form has fully rendered
        self.wait.until(EC.presence_of_element_located(self.PHONE_INPUT))
    
    def update_profile(self, phone=None, address=None, pincode=None, date_of_birth=None):
        if phone:
            el = self.find_element(*self.PHONE_INPUT)
            el.clear()
            el.send_keys(phone)
            
        if address:
            el = self.find_element(*self.ADDRESS_INPUT)
            el.clear()
            el.send_keys(address)
            
        if pincode:
            el = self.find_element(*self.PINCODE_INPUT)
            el.clear()
            el.send_keys(pincode)
            
        if date_of_birth:
            el = self.find_element(*self.DOB_INPUT)
            el.clear()
            el.send_keys(date_of_birth)
            
        self.find_clickable_element(*self.UPDATE_BUTTON).click()