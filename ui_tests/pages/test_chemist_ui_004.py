"""
F-004: Chemist Medicine Delivery Workflow — UI / End-to-End (Selenium).

Source of truth: F004_Test_Cases.docx (TDS Section 2.2.5 — UCT main flow).

Accounts are seeded inline (chemist / patient / doctor + an active prescription)
rather than via testing/conftest.py, because those fixtures are not visible to
ui_tests/ and we intentionally do not modify the shared ui_tests/conftest.py.

Real routes under test: / (login), /prescription/list/, /prescription/update/, /logout/
"""
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from django.utils import timezone
from django.contrib.auth import get_user_model

from server.models import Account, Profile, Prescription

User = get_user_model()


@pytest.mark.django_db(transaction=True)
@pytest.mark.nondestructive
class TestFeatureF004ChemistDeliveryUI:

    @pytest.fixture(autouse=True)
    def setup_delivery_ui_dependencies(self):
        """Seed a chemist, a patient (John Doe), a doctor, and an open
        (active=True) prescription so the chemist has something to deliver."""
        self.password = "test1234"
        self.chemist_email = "chemist_f004@test.com"
        self.patient_email = "johndoe_f004@test.com"
        self.doctor_email = "doctor_f004@test.com"

        user_chemist = User.objects.create_user(username=self.chemist_email.lower(), password=self.password)
        user_patient = User.objects.create_user(username=self.patient_email.lower(), password=self.password)
        user_doctor = User.objects.create_user(username=self.doctor_email.lower(), password=self.password)

        profile_chemist = Profile.objects.create(firstname="Chemist", lastname="Shop")
        profile_patient = Profile.objects.create(firstname="John", lastname="Doe")
        profile_doctor = Profile.objects.create(firstname="Dr", lastname="Smith")

        self.chemist = Account.objects.create(user=user_chemist, profile=profile_chemist, role=Account.ACCOUNT_CHEMIST)
        self.patient = Account.objects.create(user=user_patient, profile=profile_patient, role=Account.ACCOUNT_PATIENT)
        self.doctor = Account.objects.create(user=user_doctor, profile=profile_doctor, role=Account.ACCOUNT_DOCTOR)

        self.prescription = Prescription.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            date=timezone.now().date(),
            medication="Paracetamol 500mg",
            strength="1 tablet",
            instruction="Twice daily after meals",
            refill=0,
            active=True,
        )

    def _login_via_ui(self, selenium, base_url, email, password):
        """Log in through the real login form at '/'."""
        selenium.delete_all_cookies()
        selenium.get(base_url + "/")
        wait = WebDriverWait(selenium, 10)
        wait.until(EC.presence_of_element_located((By.ID, "id_email"))).send_keys(email)
        selenium.find_element(By.ID, "id_password").send_keys(password)
        selenium.find_element(By.CSS_SELECTOR, "input[type='submit']").click()
        # Successful login redirects to /profile/.
        wait.until(lambda d: "/profile/" in d.current_url)

    # 2.2.5 Use Case Testing — Medicine Delivery Main Flow (UC-13)
    def test_TC_F004_UCT_01_chemist_delivers_patient_sees_delivered(self, selenium, base_url):
        """TC_F004_UCT_01: End-to-end main flow — a Chemist opens an active
        prescription, marks it delivered (uncheck 'active' + Update), and the
        Patient's prescription list then shows Status 'Delivered'.
        """
        wait = WebDriverWait(selenium, 10)
        pk = self.prescription.pk

        # --- Chemist: view the open prescription in the list ---
        self._login_via_ui(selenium, base_url, self.chemist_email, self.password)
        selenium.get(base_url + "/prescription/list/")
        assert "Paracetamol 500mg" in selenium.page_source
        assert "Active" in selenium.page_source

        # Open it via the Update control and verify the details shown.
        update_link = wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, "a[href='/prescription/update/?pk={}']".format(pk))
        ))
        update_link.click()
        medication_input = wait.until(EC.presence_of_element_located((By.ID, "id_medication")))
        assert medication_input.get_attribute("value") == "Paracetamol 500mg"
        assert "John Doe" in selenium.page_source  # patient details visible

        # --- Chemist: mark delivered (uncheck 'active') and submit ---
        active_checkbox = selenium.find_element(By.ID, "id_active")
        if active_checkbox.is_selected():
            active_checkbox.click()
        selenium.find_element(By.CSS_SELECTOR, "input[type='submit']").click()

        # The delivery transition is persisted.
        wait.until(lambda d: Prescription.objects.get(pk=pk).active is False)
        assert Prescription.objects.get(pk=pk).active is False

        # --- Patient: log in and confirm the status reads 'Delivered' ---
        selenium.get(base_url + "/logout/")
        self._login_via_ui(selenium, base_url, self.patient_email, self.password)
        selenium.get(base_url + "/prescription/list/")

        assert "Paracetamol 500mg" in selenium.page_source   # patient sees their prescription
        assert "Delivered" in selenium.page_source           # ...with Status "Delivered"
