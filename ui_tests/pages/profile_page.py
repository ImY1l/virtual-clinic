from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from ui_tests.pages.base_page import BasePage

class ProfilePage(BasePage):
    URL = "/profile/update/"
    
    # Django auto-generates IDs like id_<field_name> for form fields.
    # ProfileForm fields are: phone, allergies, prefHospital, primaryCareDoctor, speciality,
    # plus firstname/lastname/sex/birthday.
    PHONE_INPUT = (By.ID, "id_phone")
    # Update form does not expose raw address/pincode as ProfileForm fields in this project.
    # Keep locators for potential future UI versions, but don't rely on them for this test.
    # NOTE: This ProfileForm does not have explicit address/pincode fields.
    # In this E2E we only update: phone + birthday (and form required fields already filled on server-side).
    ADDRESS_INPUT = (By.NAME, "address")
    PINCODE_INPUT = (By.NAME, "pincode")

    DOB_INPUT = (By.ID, "id_birthday")
    
    # Flexible button locator
    UPDATE_BUTTON = (By.CSS_SELECTOR, "button[type='submit'], input[type='submit']")
    
    def open(self):
        self.selenium.get(f"{self.base_url}{self.URL}")
        # Wait specifically for the phone field to prove the form has fully rendered.
        # If the page redirects (e.g., not logged in), this will fail with a clearer timeout.
        self.wait.until(EC.presence_of_element_located(self.PHONE_INPUT))
    
    def update_profile(
        self,
        first_name=None,
        last_name=None,
        sex=None,
        phone=None,
        allergies=None,
        pref_hospital_value=None,
        primary_care_doctor_value=None,
        speciality_value=None,
        date_of_birth=None,
        address=None,
        pincode=None,
    ):
        """Update all fields available in this repo's ProfileForm.

        Note: address/pincode are not present in the rendered template, so they are ignored.
        """

        if first_name is not None:
            el = self.find_element(By.ID, "id_firstname")
            el.clear()
            el.send_keys(first_name)

        if last_name is not None:
            el = self.find_element(By.ID, "id_lastname")
            el.clear()
            el.send_keys(last_name)

        if sex is not None:
            el = self.find_element(By.ID, "id_sex")
            # Use value selection by clearing and typing if possible.
            # (Select2 not used here; it's a normal <select>.)
            for option in el.find_elements(By.TAG_NAME, "option"):
                if option.get_attribute("value") == sex:
                    option.click()
                    break

        if phone is not None:
            el = self.find_element(*self.PHONE_INPUT)
            el.clear()
            el.send_keys(phone)

        if allergies is not None:
            el = self.find_element(By.ID, "id_allergies")
            el.clear()
            el.send_keys(allergies)

        # <select> fields: choose by option value.
        if pref_hospital_value is not None:
            el = self.find_element(By.ID, "id_prefHospital")
            for option in el.find_elements(By.TAG_NAME, "option"):
                if option.get_attribute("value") == pref_hospital_value:
                    option.click()
                    break

        if primary_care_doctor_value is not None:
            el = self.find_element(By.ID, "id_primaryCareDoctor")
            for option in el.find_elements(By.TAG_NAME, "option"):
                if option.get_attribute("value") == primary_care_doctor_value:
                    option.click()
                    break

        if speciality_value is not None:
            el = self.find_element(By.ID, "id_speciality")
            for option in el.find_elements(By.TAG_NAME, "option"):
                if option.get_attribute("value") == speciality_value:
                    option.click()
                    break

        if date_of_birth is not None:
            el = self.find_element(*self.DOB_INPUT)
            el.clear()
            el.send_keys(date_of_birth)

        self.find_clickable_element(*self.UPDATE_BUTTON).click()
