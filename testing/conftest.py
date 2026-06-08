"""
Global pytest fixtures for Virtual Clinic test suite.
Provides reusable test data, database setup, and authentication helpers.

NOTE: Virtual Clinic uses Account + Profile models with 'role' field
instead of separate Patient/Doctor/Chemist/Lab models.
"""
import pytest
from django.test import Client
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User as DjangoUser
from server.models import (
    Account, Profile, Speciality, Symptom, 
    Appointment, Prescription, MedicalTest, Hospital, Location
)
from faker import Faker
from datetime import datetime, timedelta, date

fake = Faker()
User = get_user_model()


@pytest.fixture(scope='session')
def django_db_setup(django_db_setup, django_db_blocker):
    """
    Session-scoped database setup.
    Creates test database once for entire test session.
    """
    pass


@pytest.fixture
def client():
    """
    Django test client for making HTTP requests.
    """
    return Client()


@pytest.fixture
def authenticated_client(client, patient_account):
    """
    Authenticated client logged in as patient.
    """
    client.force_login(patient_account.user)
    return client


@pytest.fixture
def admin_client(client, admin_account):
    """
    Authenticated client logged in as admin.
    """
    client.force_login(admin_account.user)
    return client


@pytest.fixture
def doctor_client(client, doctor_account):
    """
    Authenticated client logged in as doctor.
    """
    client.force_login(doctor_account.user)
    return client


@pytest.fixture
def chemist_client(client, chemist_account):
    """
    Authenticated client logged in as chemist.
    """
    client.force_login(chemist_account.user)
    return client


@pytest.fixture
def lab_client(client, lab_account):
    """
    Authenticated client logged in as lab.
    """
    client.force_login(lab_account.user)
    return client


@pytest.fixture
def location(db):
    """
    Create a Location fixture.
    """
    return Location.objects.create(
        city='Mangalore',
        zip='575001',
        state='Karnataka',
        country='India',
        address='Test Address, Mangalore'
    )


@pytest.fixture
def hospital(db, location):
    """
    Create a Hospital fixture.
    """
    return Hospital.objects.create(
        name='Padhmavati Hospital',
        phone='08241234567',
        location=location
    )


@pytest.fixture
def speciality(db):
    """
    Create speciality fixture.
    """
    return Speciality.objects.create(
        name='General Medicine',
        description='General medical consultation'
    )


@pytest.fixture
def symptom(db):
    """
    Create symptom fixture.
    NOTE: Symptom model uses 'name' field, not 'code'.
    """
    return Symptom.objects.create(
        name='Fever',
        description='High body temperature'
    )


@pytest.fixture
def admin_account(db):
    """
    Create admin Account fixture.
    Role: Account.ACCOUNT_ADMIN (30)
    """
    # Create Django User
    user = DjangoUser.objects.create_user(
        username='admin@virtualclinic.test',
        email='admin@virtualclinic.test',
        password='Admin@123',
        first_name='Admin',
        last_name='User',
        is_staff=True,
        is_superuser=True
    )
    
    # Create Profile
    profile = Profile.objects.create(
        firstname='Admin',
        lastname='User',
        phone='0123456789',
        birthday=date(1980, 1, 1)
    )
    
    # Create Account linked to Profile and User
    return Account.objects.create(
        user=user,
        profile=profile,
        role=Account.ACCOUNT_ADMIN  # 30
    )


@pytest.fixture
def patient_account(db):
    """
    Create patient Account fixture.
    Role: Account.ACCOUNT_PATIENT (10)
    """
    user = DjangoUser.objects.create_user(
        username='patient@test.com',
        email='patient@test.com',
        password='Patient@123',
        first_name='John',
        last_name='Doe'
    )
    
    profile = Profile.objects.create(
        firstname='John',
        lastname='Doe',
        phone='0123456789',
        birthday=fake.date_of_birth(minimum_age=25, maximum_age=65)
    )
    
    return Account.objects.create(
        user=user,
        profile=profile,
        role=Account.ACCOUNT_PATIENT  # 10
    )


@pytest.fixture
def doctor_account(db, speciality, hospital):
    """
    Create doctor Account fixture.
    Role: Account.ACCOUNT_DOCTOR (20)
    """
    user = DjangoUser.objects.create_user(
        username='doctor@test.com',
        email='doctor@test.com',
        password='Doctor@123',
        first_name='Dr. Smith',
        last_name='John',
        is_staff=True
    )
    
    profile = Profile.objects.create(
        firstname='Dr. Smith',
        lastname='John',
        phone='0123456780',
        birthday=date(1975, 6, 15),
        speciality=speciality  # ForeignKey to Speciality
    )
    
    return Account.objects.create(
        user=user,
        profile=profile,
        role=Account.ACCOUNT_DOCTOR  # 20
    )


@pytest.fixture
def chemist_account(db, hospital):
    """
    Create chemist Account fixture.
    Role: Account.ACCOUNT_CHEMIST (50)
    """
    user = DjangoUser.objects.create_user(
        username='chemist@test.com',
        email='chemist@test.com',
        password='Chemist@123',
        first_name='Chemist',
        last_name='Shop'
    )
    
    profile = Profile.objects.create(
        firstname='Chemist',
        lastname='Shop',
        phone='0123456781',
        birthday=date(1985, 3, 20)
    )
    
    return Account.objects.create(
        user=user,
        profile=profile,
        role=Account.ACCOUNT_CHEMIST  # 50
    )


@pytest.fixture
def lab_account(db, hospital):
    """
    Create lab Account fixture.
    Role: Account.ACCOUNT_LAB (40)
    """
    user = DjangoUser.objects.create_user(
        username='lab@test.com',
        email='lab@test.com',
        password='Lab@123',
        first_name='Diagnostic',
        last_name='Lab'
    )
    
    profile = Profile.objects.create(
        firstname='Diagnostic',
        lastname='Lab',
        phone='0123456782',
        birthday=date(1982, 11, 10)
    )
    
    return Account.objects.create(
        user=user,
        profile=profile,
        role=Account.ACCOUNT_LAB  # 40
    )


@pytest.fixture
def appointment(patient_account, doctor_account, symptom, hospital):
    """
    Create appointment fixture.
    NOTE: Appointment uses startTime/endTime (DateTimeField), not date+time separately.
    """
    start = datetime.now() + timedelta(days=1, hours=10)
    end = start + timedelta(hours=1)
    
    return Appointment.objects.create(
        patient=patient_account,
        doctor=doctor_account,
        symptom=symptom,
        hospital=hospital,
        description='Consultation for fever',
        appointment_type='Online',
        startTime=start,
        endTime=end,
        status='Active'
    )


@pytest.fixture
def prescription(doctor_account, patient_account):
    """
    Create prescription fixture.
    NOTE: Prescription has no 'appointment' field; links directly to doctor/patient.
    Uses 'refill' not 'refill_count'.
    """
    return Prescription.objects.create(
        patient=patient_account,
        doctor=doctor_account,
        date=datetime.now().date(),
        medication='Paracetamol 500mg',
        strength='1 tablet',
        instruction='Twice daily after meals',
        refill=0,
        active=True
    )


@pytest.fixture
def medical_test(doctor_account, patient_account, hospital):
    """
    Create medical test fixture.
    NOTE: MedicalTest has no 'prescription' or 'lab' foreign keys.
    """
    return MedicalTest.objects.create(
        name='CBC Test',
        date=datetime.now().date(),
        hospital=hospital,
        description='Complete Blood Count',
        doctor=doctor_account,
        patient=patient_account,
        private=True,
        completed=False
    )


@pytest.fixture
def valid_registration_data():
    """
    Valid registration data for testing.
    Matches AccountRegisterForm fields.
    """
    return {
        'email': fake.email(),
        'password_first': 'SecurePass123!',
        'password_second': 'SecurePass123!',
        # AccountRegisterForm expects field names: firstname / lastname
        'firstname': fake.first_name(),
        'lastname': fake.last_name(),
    }



@pytest.fixture
def valid_appointment_data(symptom, hospital):
    """
    Valid appointment data for testing.
    Matches AppointmentForm fields.
    """
    start = datetime.now() + timedelta(days=1, hours=10)
    end = start + timedelta(hours=1)
    
    return {
        'doctor': None,  # Will be set in test
        'symptom': symptom.id,
        'hospital': hospital.id,
        'description': 'Test consultation',
        'appointment_type': 'Online',
        'startTime': start.strftime('%Y-%m-%d %H:%M:%S'),
        'endTime': end.strftime('%Y-%m-%d %H:%M:%S'),
    }


@pytest.fixture(params=[
    ('', 'empty password'),
    ('a', 'minimum length'),
    ('a' * 50, 'maximum length'),
    ('a' * 51, 'exceeds maximum'),
    ('SecurePass123!', 'valid format'),
    ('     ', 'whitespace only'),
])
def password_test_cases(request):
    """
    Parameterized password test cases for BVA.
    """
    return request.param


@pytest.fixture(params=[
    ('patient@test.com', 'valid email'),
    ('invalid-email', 'missing @'),
    ('@test.com', 'missing local part'),
    ('user@', 'missing domain'),
    ('a' * 51 + '@test.com', 'exceeds 50 chars'),
])
def email_test_cases(request):
    """
    Parameterized email test cases for EP.
    """
    return request.param

@pytest.fixture
def patient_credentials(patient_account):
    return {
        "email": "patient@test.com",
        "password": "Patient@123"
    }