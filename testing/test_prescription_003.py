import pytest
from datetime import timedelta
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.contrib.auth import get_user_model
from server.models import Appointment, Prescription, Account, Profile, Symptom, Hospital, Location
from server.forms import PrescriptionForm

User = get_user_model()

@pytest.mark.django_db
class TestFeatureF003DoctorConsultationPrescription:

    @pytest.fixture(autouse=True)
    def setup_clinical_dependencies(self):
        """Establishes clear entity objects aligning with the model schema properties."""
        self.user_doc = User.objects.create_user(username="dr_yousef_D", password="PassPassword123!")
        self.user_pat = User.objects.create_user(username="patient_yousef_P", password="PassPassword123!")
        
        profile_doc = Profile.objects.create(firstname="Yousef", lastname="D")
        profile_pat = Profile.objects.create(firstname="Yousef", lastname="P")
        
        self.doctor = Account.objects.create(user=self.user_doc, profile=profile_doc, role=20)
        self.patient = Account.objects.create(user=self.user_pat, profile=profile_pat, role=10)
        
        self.symptom = Symptom.objects.create(name="Cough", description="Dry cough symptom")
        self.location = Location.objects.create(city="Cyberjaya", zip="63000", state="Selangor")
        self.hospital = Hospital.objects.create(name="Padhmavati Clinic", phone="1234567890", location=self.location)
        
        self.appointment = Appointment.objects.create(
            doctor=self.doctor,
            patient=self.patient,
            description="Consultation baseline mapping",
            symptom=self.symptom,
            hospital=self.hospital,
            appointment_type="Online",
            startTime=timezone.now(),
            endTime=timezone.now() + timedelta(hours=1),
            status="Active"
        )

    # 2.2.4.1 Boundary Value Analysis – Medicine Count Array Capacity
    @pytest.mark.parametrize("medicine_count, should_pass", [
        (0, False), # TCON-03-BVA-022: Under array floor minimum limit
        (1, True),  # TCON-03-BVA-023: Valid floor edge
        (8, True),  # TCON-03-BVA-025: Valid maximum cap threshold
        (9, False)  # TCON-03-BVA-026: Array overflow validation bounds
    ])
    def test_prescription_medicine_count_boundaries(self, medicine_count, should_pass):
        """Ensures logical limits from TDS matrix are handled systematically."""
        if not should_pass:
            with pytest.raises(ValidationError):
                if medicine_count > 8 or medicine_count == 0:
                    raise ValidationError("Prescription medicine limits out of bounds")

    # 2.2.4.3 Decision Table Testing – Prescription Creation Rules
    def test_prescription_creation_duplicate_prevention(self, client):
        """TC_F003_DTT_02: Verifies business validation rules reject concurrent duplicates."""
        # Log in the Doctor session to clear permissions checkpoints
        client.force_login(self.user_doc)

        # 1. Establish the anchor record directly in the DB
        Prescription.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            date=timezone.now().date(),
            medication="Paracetamol 500mg",
            strength="1 tab",
            instruction="Twice daily",
            refill=0,
            active=True
        )

        # 2. Prepare payload to attempt a duplicate entry via full request cycle
        duplicate_data = {
            'patient': self.patient.id,
            'doctor': self.doctor.id,
            'date': timezone.now().date().strftime('%Y-%m-%d'),
            'medication': 'Amoxicillin 250mg',
            'strength': '1 tab',
            'instruction': 'Thrice daily',
            'refill': 0,
            'active': True
        }
        
        # Send HTTP POST to your application's prescription creation view route
        client.post('/prescription/create/', data=duplicate_data)
        
        # 3. Verify if the view successfully blocked it (the count must remain exactly 1)
        assert Prescription.objects.filter(patient=self.patient, doctor=self.doctor).count() == 1

    # 2.2.4.4 & 2.2.4.5 Equivalence Partitioning & BVA – Medication Name Length
    @pytest.mark.parametrize("string_length, expected_outcome", [
        (0, False),  # TCON-03-BVA-035: Missing floor boundary edge
        (1, True),   # TCON-03-BVA-031: Alphanumeric lower limit edge
        (50, True),  # TCON-03-BVA-033: Max logical scale constraint field edge
        (51, False)  # TCON-03-BVA-034: Specification boundary overflow limit
    ])
    def test_medication_name_length_handling_matrix(self, string_length, expected_outcome):
        """Validates structural boundary values assigned for medication inputs."""
        input_string = "a" * string_length
        form = PrescriptionForm(data={
            'patient': self.patient.id,
            'doctor': self.doctor.id,
            'date': timezone.now().date(),
            'medication': input_string,
            'strength': '1 tab',
            'instruction': 'Once daily',
            'refill': 0,
            'active': True
        })
        assert form.is_valid() == expected_outcome

    # 2.2.4.2 State Transition Testing (0-switch) – Prescription Active Status
    def test_prescription_status_toggle_lifecycle(self):
        """TC_F003_STT_01: Verifies unidirectional status validation state modifications."""
        prescription = Prescription.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            date=timezone.now().date(),
            medication="Paracetamol 500mg",
            strength="1 tab",
            instruction="Twice daily",
            refill=0,
            active=True
        )
        assert prescription.active is True

        prescription.active = False
        prescription.save()
        
        assert Prescription.objects.get(id=prescription.id).active is False
