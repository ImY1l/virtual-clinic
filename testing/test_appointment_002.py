import pytest
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth import get_user_model
from server.models import Appointment, Account, Profile, Symptom, Hospital, Location
from server.forms import AppointmentForm

User = get_user_model()

@pytest.mark.django_db
class TestFeatureF002ConsultationRequest:

    @pytest.fixture(autouse=True)
    def setup_context_dependencies(self):
        """Provisions complete relational entities matching the concrete schema attributes."""
        # 1. Base Users
        self.user_doc = User.objects.create_user(username="dr_yousef_vc", password="SecurePassword123!")
        self.user_pat = User.objects.create_user(username="patient_amena_vc", password="SecurePassword123!")

        # 2. Profiles (Required by Account model structure)
        profile_doc = Profile.objects.create(firstname="Yousef", lastname="Mohammad")
        profile_pat = Profile.objects.create(firstname="Amena", lastname="Mohammad")

        # 3. Accounts
        self.doctor = Account.objects.create(user=self.user_doc, profile=profile_doc, role=20)
        self.patient = Account.objects.create(user=self.user_pat, profile=profile_pat, role=10)

        # 4. Symptom Reference Object
        self.symptom = Symptom.objects.create(name="Fever", description="High temperature body symptom")

        # 5. Location and Hospital Reference Objects
        self.location = Location.objects.create(city="Cyberjaya", zip="63000", state="Selangor", address="MMU Campus")
        self.hospital = Hospital.objects.create(name="Padhmavati Hospital", phone="1234567890", location=self.location)

    # 2.2.3.1 Decision Table Testing – Appointment Conflict Rules (FR-0601)
    def test_appointment_conflict_same_doctor_and_time(self, client):
        """TC_F002_DTT_01: Verify conflict rule rejects overlapping times for same doctor."""
        # Log in the patient to satisfy the view's authentication requirement
        client.force_login(self.user_pat)

        start_time = timezone.now() + timedelta(days=1, hours=10)
        end_time = start_time + timedelta(hours=1)

        # Establish base existing baseline record directly in the DB
        Appointment.objects.create(
            doctor=self.doctor,
            patient=self.patient,
            description="First booking",
            symptom=self.symptom,
            hospital=self.hospital,
            appointment_type="Online",
            startTime=start_time,
            endTime=end_time,
            status="Active"
        )

        # Prepare payload with string-formatted dates to mimic an HTTP POST transaction
        form_data = {
            'doctor': self.doctor.id,
            'patient': self.patient.id,
            'description': 'Overlapping collision booking',
            'symptom': self.symptom.id,
            'hospital': self.hospital.id,
            'appointment_type': 'Online',
            'startTime': start_time.strftime('%Y-%m-%d %H:%M:%S'),
            'endTime': end_time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Submit to the full application view layer
        client.post('/appointment/create/', data=form_data)
        
        # Assert that the duplicate booking was blocked (the database count stays exactly 1)
        assert Appointment.objects.filter(doctor=self.doctor).count() == 1

    # 2.2.3.2 Boundary Value Analysis – Appointment Date & 5-Day Window
    def test_appointment_date_boundaries(self, client):
        """TCON-02-BVA-011: Validates that dates beyond 5 days out are rejected by the workflow."""
        client.force_login(self.user_pat)

        invalid_future_time = timezone.now() + timedelta(days=6)
        form_data = {
            'doctor': self.doctor.id,
            'patient': self.patient.id,
            'description': 'Future boundary violation check',
            'symptom': self.symptom.id,
            'hospital': self.hospital.id,
            'appointment_type': 'Online',
            'startTime': invalid_future_time.strftime('%Y-%m-%d %H:%M:%S'),
            'endTime': (invalid_future_time + timedelta(hours=1)).strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Submit to the full application view layer
        client.post('/appointment/create/', data=form_data)
        
        # Assert that the invalid future booking was blocked (database count stays 0)
        assert Appointment.objects.filter(doctor=self.doctor).count() == 0

    # 2.2.3.5 & 2.2.3.6 Equivalence Partitioning – Form Choices
    @pytest.mark.parametrize("mode, expected_valid", [
        ('Offline', True),   # TCON-02-015
        ('Online', True),    # TCON-02-016
        ('', False),         # TCON-02-017
        ('HomeVisit', False) # TCON-02-018
    ])
    def test_appointment_mode_equivalence_partitioning(self, mode, expected_valid):
        """Tests logical partitioning for structural selection types at form layer."""
        form_data = {
            'doctor': self.doctor.id,
            'patient': self.patient.id,
            'description': 'Choice mapping test',
            'symptom': self.symptom.id,
            'hospital': self.hospital.id,
            'appointment_type': mode,
            'startTime': timezone.now() + timedelta(days=1),
            'endTime': timezone.now() + timedelta(days=1, hours=1)
        }
        form = AppointmentForm(data=form_data)
        if expected_valid:
            assert "appointment_type" not in form.errors
        else:
            assert "appointment_type" in form.errors

    # 2.2.3.7 Boundary Value Analysis – Appointment Time Sequence
    def test_appointment_chronological_time_sequence(self):
        """TCON-02-020: Verifies rejection of inverted chronological bounds (End Time <= Start Time)."""
        base_time = timezone.now() + timedelta(days=1)
        
        form = AppointmentForm(data={
            'doctor': self.doctor.id,
            'patient': self.patient.id,
            'description': 'Chronological inversion validation check',
            'symptom': self.symptom.id,
            'hospital': self.hospital.id,
            'appointment_type': 'Online',
            'startTime': base_time + timedelta(hours=2),
            'endTime': base_time + timedelta(hours=1)
        })
        assert form.is_valid() is False

    # 2.2.3.9 State Transition Testing (0-switch) – Appointment Lifecycle
    def test_appointment_lifecycle_state_transitions(self):
        """TC_F002_STT_06 & 07: Validate single-hop state progression track changes."""
        appointment = Appointment.objects.create(
            doctor=self.doctor,
            patient=self.patient,
            description="Initial care path request",
            symptom=self.symptom,
            hospital=self.hospital,
            appointment_type="Online",
            startTime=timezone.now() + timedelta(days=1),
            endTime=timezone.now() + timedelta(days=1, hours=1),
            status="Active"
        )
        assert appointment.status == "Active"

        # Explicit transition to Cancelled
        appointment.status = "Cancelled"
        appointment.save()
        
        # Verify state persistence matches target destination field
        assert Appointment.objects.get(id=appointment.id).status == "Cancelled"
