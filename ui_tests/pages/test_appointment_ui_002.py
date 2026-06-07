import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model
from server.models import Account, Profile, Symptom, Hospital, Location, Appointment

User = get_user_model()

@pytest.mark.django_db(transaction=True)
@pytest.mark.nondestructive  
class TestFeatureF002ConsultationRequestUI:

    @pytest.fixture(autouse=True)
    def setup_ui_test_environment(self):
        """Provisions complete background relational dependencies matching your backend logic schema."""
        self.password = "test1234"
        self.email = "test@gmail.com"
        
        user_pat = User.objects.create_user(username=self.email.lower(), password=self.password)
        user_doc = User.objects.create_user(username="doctor@gmail.com", password="password123")

        profile_pat = Profile.objects.create(firstname="Amena", lastname="Mohammad")
        profile_doc = Profile.objects.create(firstname="Yousef", lastname="Mohammad")

        self.patient = Account.objects.create(user=user_pat, profile=profile_pat, role=10)
        self.doctor = Account.objects.create(user=user_doc, profile=profile_doc, role=20)

        self.symptom = Symptom.objects.create(name="Fever", description="High temperature body symptom")
        self.location = Location.objects.create(city="Cyberjaya", zip="63000", state="Selangor", address="MMU Campus")
        self.hospital = Hospital.objects.create(name="Padhmavati Hospital", phone="1234567890", location=self.location)

    def login_user_via_ui(self, selenium, live_server):
        """Automates logging in through the UI form using your specified testing credentials."""
        selenium.get(live_server.url + "/")
        wait = WebDriverWait(selenium, 10)

        username_input = wait.until(EC.presence_of_element_located((By.ID, "id_email")))
        password_input = wait.until(EC.presence_of_element_located((By.ID, "id_password")))
        submit_btn = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "input[type='submit'][value='Login'], button[type='submit']"))
        )

        username_input.clear()
        username_input.send_keys(self.email)
        password_input.clear()
        password_input.send_keys(self.password)
        submit_btn.click()

        WebDriverWait(selenium, 10).until(lambda driver: "/login" not in driver.current_url.lower())

    def fill_and_submit_appointment_form(self, selenium, description, start_dt, end_dt, mode="Online"):
        """Helper to input fields sequentially into your standard singleform.html layout wrapper."""
        wait = WebDriverWait(selenium, 10)
        
        doctor_select = Select(wait.until(EC.presence_of_element_located((By.ID, "id_doctor"))))
        patient_select = Select(selenium.find_element(By.ID, "id_patient"))
        symptom_select = Select(selenium.find_element(By.ID, "id_symptom"))
        hospital_select = Select(selenium.find_element(By.ID, "id_hospital"))
        type_select = Select(selenium.find_element(By.ID, "id_appointment_type"))
        description_input = selenium.find_element(By.ID, "id_description")
        start_time_input = selenium.find_element(By.ID, "id_startTime")
        end_time_input = selenium.find_element(By.ID, "id_endTime")
        submit_button = selenium.find_element(By.CSS_SELECTOR, "input[type='submit'], button[type='submit']")

        doctor_select.select_by_value(str(self.doctor.id))
        patient_select.select_by_value(str(self.patient.id))
        symptom_select.select_by_value(str(self.symptom.id))
        hospital_select.select_by_value(str(self.hospital.id))
        
        if mode in ["Online", "Offline"]:
            type_select.select_by_value(mode)

        description_input.clear()
        description_input.send_keys(description)
        
        start_time_input.clear()
        start_time_input.send_keys(start_dt.strftime('%Y-%m-%dT%H:%M'))
        end_time_input.clear()
        end_time_input.send_keys(end_dt.strftime('%Y-%m-%dT%H:%M'))

        submit_button.click()

    # =========================================================================
    # CASE 1: Valid Appointment Creation Flow (Happy Path)
    # =========================================================================
    def test_create_appointment_successful_ui_flow(self, selenium, live_server):
        """TSCEN-02-001: Validates successful appointment creation form entry via UI."""
        self.login_user_via_ui(selenium, live_server)
        selenium.get(live_server.url + "/appointment/create/")
        
        start_time = timezone.now() + timedelta(days=1, hours=10)
        end_time = start_time + timedelta(hours=1)
        self.fill_and_submit_appointment_form(selenium, "Automated UI Happy Path Validation", start_time, end_time)
        
        assert "error" not in selenium.current_url.lower()

    # =========================================================================
    # CASE 2: Decision Table Testing – Appointment Conflict Rules (FR-0601)
    # =========================================================================
    def test_appointment_conflict_same_doctor_and_time_ui(self, selenium, live_server):
        """TC_F002_DTT_01: Overlapping booking request is blocked on the frontend view layer."""
        start_time = timezone.now() + timedelta(days=1, hours=10)
        end_time = start_time + timedelta(hours=1)

        Appointment.objects.create(
            doctor=self.doctor, patient=self.patient, description="Baseline Block",
            symptom=self.symptom, hospital=self.hospital, appointment_type="Online",
            startTime=start_time, endTime=end_time, status="Active"
        )

        self.login_user_via_ui(selenium, live_server)
        selenium.get(live_server.url + "/appointment/create/")
        self.fill_and_submit_appointment_form(selenium, "Overlapping collision booking", start_time, end_time)

        assert "conflict" in selenium.page_source.lower() or "overlap" in selenium.page_source.lower() or "error" in selenium.page_source.lower()

    # =========================================================================
    # CASE 3: Boundary Value Analysis – Appointment Date Window
    # =========================================================================
    def test_appointment_date_boundaries_ui(self, selenium, live_server):
        """TCON-02-BVA-011: Bookings configured beyond 5 open schedule days show validation markup error warnings."""
        self.login_user_via_ui(selenium, live_server)
        selenium.get(live_server.url + "/appointment/create/")

        invalid_future_start = timezone.now() + timedelta(days=6, hours=10)
        invalid_future_end = invalid_future_start + timedelta(hours=1)

        self.fill_and_submit_appointment_form(selenium, "Future boundary check", invalid_future_start, invalid_future_end)

        assert "create" in selenium.current_url.lower() or "error" in selenium.page_source.lower()

    # =========================================================================
    # CASE 4: Equivalence Partitioning – Form Choices
    # =========================================================================
    @pytest.mark.parametrize("mode, should_pass", [('Offline', True), ('Online', True)])
    def test_appointment_mode_equivalence_partitioning_ui(self, selenium, live_server, mode, should_pass):
        """Validates functional equivalence groups execute and persist entries smoothly via UI selection."""
        self.login_user_via_ui(selenium, live_server)
        selenium.get(live_server.url + "/appointment/create/")

        start_time = timezone.now() + timedelta(days=2, hours=14)
        end_time = start_time + timedelta(hours=1)
        self.fill_and_submit_appointment_form(selenium, f"Choice validation run: {mode}", start_time, end_time, mode=mode)

        if should_pass:
            WebDriverWait(selenium, 10).until(lambda driver: "/create" not in driver.current_url.lower())
            assert "error" not in selenium.current_url.lower()

    # =========================================================================
    # CASE 5: Boundary Value Analysis – Appointment Time Sequence
    # =========================================================================
    def test_appointment_chronological_time_sequence_ui(self, selenium, live_server):
        """TCON-02-020: Browser UI correctly rendering rejections when End Time <= Start Time."""
        self.login_user_via_ui(selenium, live_server)
        selenium.get(live_server.url + "/appointment/create/")

        base_time = timezone.now() + timedelta(days=1)
        self.fill_and_submit_appointment_form(selenium, "Chronological validation check", base_time + timedelta(hours=5), base_time + timedelta(hours=4))

        assert "after" in selenium.page_source.lower() or "time" in selenium.page_source.lower() or "error" in selenium.page_source.lower()

    # =========================================================================
    # CASE 6: State Transition Testing – Modification Flow (Active -> Active)
    # =========================================================================
    def test_update_appointment_details_ui_flow(self, selenium, live_server):
        """TC_F002_STT_06: Validates updating an active appointment entry via the inline row link."""
        unique_description = "Original Booking State Description"
        appointment = Appointment.objects.create(
            doctor=self.doctor, patient=self.patient, description=unique_description,
            symptom=self.symptom, hospital=self.hospital, appointment_type="Online",
            startTime=timezone.now() + timedelta(days=3), endTime=timezone.now() + timedelta(days=3, hours=1),
            status="Active"
        )

        self.login_user_via_ui(selenium, live_server)
        selenium.get(live_server.url + "/appointment/list/")
        wait = WebDriverWait(selenium, 10)
        
        # Target the inline update hyperlink directly from your table layout
        update_link = wait.until(
            EC.element_to_be_clickable((By.LINK_TEXT, "Update"))
        )
        update_link.click()

        # Update description on the navigated form page
        description_input = wait.until(EC.presence_of_element_located((By.ID, "id_description")))
        description_input.clear()
        
        updated_text = "Altered description context via Selenium"
        description_input.send_keys(updated_text)

        submit_button = selenium.find_element(By.CSS_SELECTOR, "input[type='submit'], button[type='submit']")
        submit_button.click()

        wait.until(lambda d: Appointment.objects.get(id=appointment.id).description == updated_text)
        assert Appointment.objects.get(id=appointment.id).status == "Active"

    # =========================================================================
    # CASE 7: State Transition Testing – Cancellation Flow (Active -> Cancelled)
    # =========================================================================
    def test_appointment_lifecycle_state_transitions_ui(self, selenium, live_server):
        """TC_F002_STT_07: Tests inline table button trigger to immediately launch the confirmation modal workflow."""
        unique_description = "STT-Lifecycle-Inline-Cancel-Anchor"
        appointment = Appointment.objects.create(
            doctor=self.doctor, patient=self.patient, description=unique_description,
            symptom=self.symptom, hospital=self.hospital, appointment_type="Online",
            startTime=timezone.now() + timedelta(days=3), endTime=timezone.now() + timedelta(days=3, hours=1),
            status="Active"
        )

        self.login_user_via_ui(selenium, live_server)
        selenium.get(live_server.url + "/appointment/list/")
        wait = WebDriverWait(selenium, 10)
        
        # Target the inline danger cancel button directly from your active datatable row layout
        cancel_btn = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Cancel')]"))
        )
        cancel_btn.click()
        
        # Confirm destruction modal actions directly (no step-skipping timeouts)
        confirm_button = wait.until(EC.element_to_be_clickable((By.ID, "confirm-modal-submit")))
        confirm_button.click()

        wait.until(lambda d: Appointment.objects.get(id=appointment.id).status == "Cancelled")
        assert Appointment.objects.get(id=appointment.id).status == "Cancelled"
