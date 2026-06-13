"""
F-005: Lab Test Request & Report Upload — UI / End-to-End (Selenium).

Source of truth: F005_Test_Cases.docx (TDS Section 2.2.6 — UCT main flow).

Accounts are seeded inline (lab / patient / doctor + hospital), and MEDIA_ROOT
is redirected to a temp dir so the browser upload never touches the repo media/.
We do not modify the shared ui_tests/conftest.py.

Real routes under test: / (login), /medtest/upload/, /medtest/list/, /medtest/display/, /logout/
"""
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from django.utils import timezone
from django.contrib.auth import get_user_model

from server.models import Account, Profile, Hospital, Location, MedicalTest

User = get_user_model()


@pytest.mark.django_db(transaction=True)
@pytest.mark.nondestructive
class TestFeatureF005LabUploadUI:

    @pytest.fixture(autouse=True)
    def setup_lab_ui_dependencies(self, settings, tmp_path):
        """Seed lab/patient/doctor + hospital and isolate uploaded media."""
        settings.MEDIA_ROOT = str(tmp_path)  # keep uploads out of the repo media/

        self.password = "test1234"
        self.lab_email = "lab_f005@test.com"
        self.patient_email = "johndoe_f005@test.com"
        self.doctor_email = "doctor_f005@test.com"

        user_lab = User.objects.create_user(username=self.lab_email.lower(), password=self.password)
        user_patient = User.objects.create_user(username=self.patient_email.lower(), password=self.password)
        user_doctor = User.objects.create_user(username=self.doctor_email.lower(), password=self.password)

        self.lab = Account.objects.create(
            user=user_lab, profile=Profile.objects.create(firstname="Diagnostic", lastname="Lab"),
            role=Account.ACCOUNT_LAB,
        )
        self.patient = Account.objects.create(
            user=user_patient, profile=Profile.objects.create(firstname="John", lastname="Doe"),
            role=Account.ACCOUNT_PATIENT,
        )
        self.doctor = Account.objects.create(
            user=user_doctor, profile=Profile.objects.create(firstname="Dr", lastname="Smith"),
            role=Account.ACCOUNT_DOCTOR,
        )

        location = Location.objects.create(city="Cyberjaya", zip="63000", state="Selangor")
        self.hospital = Hospital.objects.create(name="Padhmavati Hospital", phone="1234567890", location=location)

        # A real file on disk for the browser to upload (FileField accepts any non-empty file).
        self.report_path = tmp_path / "report_scan.png"
        self.report_path.write_bytes(b"\x89PNG\r\n\x1a\n" + b"x" * (50 * 1024))  # ~50 KB

    def _login_via_ui(self, selenium, base_url, email, password):
        selenium.delete_all_cookies()
        selenium.get(base_url + "/")
        wait = WebDriverWait(selenium, 10)
        wait.until(EC.presence_of_element_located((By.ID, "id_email"))).send_keys(email)
        selenium.find_element(By.ID, "id_password").send_keys(password)
        selenium.find_element(By.CSS_SELECTOR, "input[type='submit']").click()
        wait.until(lambda d: "/profile/" in d.current_url)

    # 2.2.6.5 Use Case Testing — Lab Upload Main Flow (UC-12)
    def test_TC_F005_UCT_01_lab_uploads_patient_views_report(self, selenium, base_url):
        """TC_F005_UCT_01: End-to-end main flow — the Lab uploads a valid report
        (non-private, completed), and the Patient can then view it in their list
        and open the report on the display page.
        """
        wait = WebDriverWait(selenium, 10)

        # --- Lab: upload a valid report for John Doe ---
        self._login_via_ui(selenium, base_url, self.lab_email, self.password)
        selenium.get(base_url + "/medtest/upload/")

        Select(wait.until(EC.presence_of_element_located((By.ID, "id_patient")))).select_by_value(str(self.patient.id))
        Select(selenium.find_element(By.ID, "id_doctor")).select_by_value(str(self.doctor.id))
        Select(selenium.find_element(By.ID, "id_hospital")).select_by_value(str(self.hospital.id))

        name = selenium.find_element(By.ID, "id_name")
        name.clear()
        name.send_keys("CBC Test")
        desc = selenium.find_element(By.ID, "id_description")
        desc.clear()
        desc.send_keys("Complete Blood Count")
        date = selenium.find_element(By.ID, "id_date")
        date.clear()
        date.send_keys(timezone.now().date().strftime("%Y-%m-%d"))

        # Mark completed; leave 'private' unchecked so the patient can view it.
        completed = selenium.find_element(By.ID, "id_completed")
        if not completed.is_selected():
            completed.click()

        # Attach the report file (absolute path required by Selenium).
        selenium.find_element(By.ID, "id_image1").send_keys(str(self.report_path))
        selenium.find_element(By.CSS_SELECTOR, "input[type='submit']").click()

        # The report is stored: a completed, non-private MedicalTest with a file.
        wait.until(lambda d: MedicalTest.objects.filter(patient=self.patient).exists())
        mt = MedicalTest.objects.get(patient=self.patient)
        assert mt.completed is True
        assert mt.private is False
        assert bool(mt.image1)

        # --- Patient: log in and view the uploaded report ---
        selenium.get(base_url + "/logout/")
        self._login_via_ui(selenium, base_url, self.patient_email, self.password)

        selenium.get(base_url + "/medtest/list/")
        assert "CBC Test" in selenium.page_source  # appears in the patient's list

        selenium.get(base_url + "/medtest/display/?pk={}".format(mt.pk))
        assert "CBC Test" in selenium.page_source            # report details shown
        assert "/media/" in selenium.page_source             # the report image is presented
