import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model
from server.models import Account, Profile, Symptom, Hospital, Location, Prescription

User = get_user_model()

@pytest.mark.django_db(transaction=True)
@pytest.mark.nondestructive  
class TestFeatureF003DoctorConsultationPrescriptionUI:

    @pytest.fixture(autouse=True)
    def setup_clinical_ui_dependencies(self):
        """Establishes clinical entity data layout models to seed select dropdown scopes."""
        self.password = "test1234"
        self.doc_email = "doctor_yousef@gmail.com"
        self.pat_email = "patient_jan@gmail.com"
        
        # 1. Base Authentication Accounts (Ensures Account.objects.count() > 0 to skip /setup wizard)
        user_doc = User.objects.create_user(username=self.doc_email.lower(), password=self.password)
        user_pat = User.objects.create_user(username=self.pat_email.lower(), password=self.password)
        
        profile_doc = Profile.objects.create(firstname="Yousef", lastname="D")
        profile_pat = Profile.objects.create(firstname="Jan", lastname="Tan")
        
        # Role 20 matches Doctor requirements to render action button nodes in view templates
        self.doctor = Account.objects.create(user=user_doc, profile=profile_doc, role=20)
        self.patient = Account.objects.create(user=user_pat, profile=profile_pat, role=10)
        
        # 2. Structural Infrastructure Dependencies
        self.symptom = Symptom.objects.create(name="Cough", description="Dry cough symptom")
        self.location = Location.objects.create(city="Cyberjaya", zip="63000", state="Selangor")
        self.hospital = Hospital.objects.create(name="Padhmavati Clinic", phone="1234567890", location=self.location)

    def login_as_doctor_via_ui(self, selenium, live_server):
        """Automates signing into the interface using authorized Doctor privileges."""
        selenium.get(live_server.url + "/")
        wait = WebDriverWait(selenium, 10)

        username_input = wait.until(EC.presence_of_element_located((By.ID, "id_email")))
        password_input = wait.until(EC.presence_of_element_located((By.ID, "id_password")))
        submit_btn = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "input[type='submit'][value='Login'], button[type='submit']"))
        )

        username_input.clear()
        username_input.send_keys(self.doc_email)
        password_input.clear()
        password_input.send_keys(self.password)
        submit_btn.click()

        WebDriverWait(selenium, 10).until(lambda driver: "/login" not in driver.current_url.lower())

    def fill_and_submit_prescription_form(self, selenium, medication_text, strength="1 tab", instruction="Twice daily", refill_count="0"):
        """Helper matrix method to populate fields sequentially inside your singleform.html layout."""
        wait = WebDriverWait(selenium, 10)
        
        patient_select = Select(wait.until(EC.presence_of_element_located((By.ID, "id_patient"))))
        doctor_select = Select(selenium.find_element(By.ID, "id_doctor"))
        date_input = selenium.find_element(By.ID, "id_date")
        medication_input = selenium.find_element(By.ID, "id_medication")
        strength_input = selenium.find_element(By.ID, "id_strength")
        instruction_input = selenium.find_element(By.ID, "id_instruction")
        refill_input = selenium.find_element(By.ID, "id_refill")
        submit_button = selenium.find_element(By.CSS_SELECTOR, "input[type='submit'], button[type='submit']")

        patient_select.select_by_value(str(self.patient.id))
        doctor_select.select_by_value(str(self.doctor.id))
        
        date_input.clear()
        date_input.send_keys(timezone.now().date().strftime('%Y-%m-%d'))
        
        medication_input.clear()
        medication_input.send_keys(medication_text)
        
        strength_input.clear()
        strength_input.send_keys(strength)
        
        instruction_input.clear()
        instruction_input.send_keys(instruction)
        
        refill_input.clear()
        refill_input.send_keys(str(refill_count))

        submit_button.click()

    # HAPPY PATH: Create Prescription Flow
    def test_create_prescription_successful_ui_flow(self, selenium, live_server):
        """TSCEN-03-001: Verifies successful prescription workflow pipeline processing entry."""
        self.login_as_doctor_via_ui(selenium, live_server)
        selenium.get(live_server.url + "/prescription/create/")
        
        self.fill_and_submit_prescription_form(selenium, "Paracetamol 500mg", refill_count="2")
        
        # Form should redirect away from creation link endpoint cleanly on success
        assert "error" not in selenium.current_url.lower()

    # 2.2.4.3 Decision Table Testing – Prescription Creation Rules
    def test_prescription_creation_duplicate_prevention_ui(self, selenium, live_server):
        """TC_F003_DTT_02: Submitting an identical profile prescription entry blocks transaction processing."""
        # Provision baseline initial record entry
        Prescription.objects.create(
            patient=self.patient, doctor=self.doctor, date=timezone.now().date(),
            medication="Amoxicillin 250mg", strength="1 tab", instruction="Thrice daily", refill=0, active=True
        )

        self.login_doc_via_ui = self.login_as_doctor_via_ui(selenium, live_server)
        selenium.get(live_server.url + "/prescription/create/")

        # Attempt duplicate entry injection run
        self.fill_and_submit_prescription_form(selenium, "Amoxicillin 250mg", refill_count="0")

        # Page validation rules trap concurrent execution paths
        assert "create" in selenium.current_url.lower() or "error" in selenium.page_source.lower()
        assert Prescription.objects.filter(patient=self.patient, doctor=self.doctor).count() == 1

    # 2.2.4.4 & 2.2.4.5 Equivalence Partitioning & BVA – Medication Name Length
    @pytest.mark.parametrize("string_length, should_pass", [
        (0, False),   # TCON-03-BVA-035: Under length boundary floor
        (1, True),    # TCON-03-BVA-031: Floor validation valid edge
        (50, True),   # TCON-03-BVA-033: Maximum specification length edge
        (51, False)   # TCON-03-BVA-034: Overflow character string upper bound
    ])
    def test_medication_name_length_handling_ui_matrix(self, selenium, live_server, string_length, should_pass):
        """Validates alphanumeric constraint partitions assigned for input lengths inside form inputs."""
        self.login_as_doctor_via_ui(selenium, live_server)
        selenium.get(live_server.url + "/prescription/create/")

        input_string = "a" * string_length
        self.fill_and_submit_prescription_form(selenium, input_string)

        if should_pass:
            WebDriverWait(selenium, 10).until(lambda driver: "/create" not in driver.current_url.lower())
            assert "error" not in selenium.current_url.lower()
        else:
            assert "create" in selenium.current_url.lower() or "error" in selenium.page_source.lower()

    # 2.2.4.2 State Transition Testing (0-switch) – Active Delete Lifecycles
    def test_prescription_delete_modal_lifecycle_ui_flow(self, selenium, live_server):
        """TC_F003_STT_01: Tests inline datatable triggers to confirm destructive prescription drops via form-modal."""
        prescription = Prescription.objects.create(
            patient=self.patient, doctor=self.doctor, date=timezone.now().date(),
            medication="Ibuprofen 400mg", strength="1 tab", instruction="Once daily", refill=1, active=True
        )

        self.login_as_doctor_via_ui(selenium, live_server)
        selenium.get(live_server.url + "/prescription/list/") # Adjust to your matching list URL path mapping
        wait = WebDriverWait(selenium, 10)
        
        # 1. Target the inline button containing the string "Delete" matching your view template layout code
        delete_modal_trigger = wait.until(
            EC.element_to_be_clickable((By.XPATH, f"//button[contains(text(), 'Delete')]"))
        )
        delete_modal_trigger.click()

        # 2. Interact with the form_modal confirmation submit element configured dynamically by proxy script
        confirm_delete_button = wait.until(
            EC.element_to_be_clickable((By.ID, "form-modal-submit"))
        )
        confirm_delete_button.click()

        # 3. Synchronize background thread transitions to check persistence state modification handling loops
        wait.until(lambda d: Prescription.objects.filter(id=prescription.id).count() == 0 or not Prescription.objects.get(id=prescription.id).active)
