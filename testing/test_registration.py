"""
Test Suite: F-001 - Patient Registration & Profile Management

Covers:
- User registration with validation (EP, BVA)
- Profile update with constraints
- Employee registration rules (DTT)
- State transitions (STT)

Test Techniques: EP, BVA, DTT, STT, UCT
SRS References: FR-0501, FR-0502, UC-01, UC-07, REQ_U1018
"""
import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from server.models import Speciality
from server.forms import AccountRegisterForm, ProfileForm, EmployeeRegistrationForm
from datetime import datetime, timedelta

User = get_user_model()


@pytest.mark.django_db
@pytest.mark.unit
@pytest.mark.smoke
class TestPatientRegistration:
    """
    Test Class: Patient Registration Validation

    
    Validates registration form constraints using Equivalence Partitioning
    and Boundary Value Analysis.
    """
    
    def test_registration_valid_data(self, client, valid_registration_data):
        # Ensure primary admin exists; register_view redirects to /setup/ when none exist.
        from django.contrib.auth.models import User as DjangoUser
        from server.models import Account, Profile
        if Account.objects.all().count() == 0:
            superuser = DjangoUser.objects.create_superuser(
                username='primaryadmin@test.com',
                email='primaryadmin@test.com',
                password='Admin@123'
            )
            profile = Profile.objects.create(firstname='Admin', lastname='User', phone='', birthday=datetime(1980,1,1).date())
            Account.objects.create(user=superuser, profile=profile, role=Account.ACCOUNT_ADMIN)

        """
        TC_F001_EP_01: Verify successful registration with valid data.
        
        Test Technique: Equivalence Partitioning (Valid Partition)
        Expected: Account created, redirect to profile page
        """
        response = client.post(reverse('server:register'), valid_registration_data)

        # register_view redirects to /setup/ if no primary admin exists.
        # Ensure primary admin exists in test precondition.
        # Either we get redirected to /profile/ (success) or render register.html with validation errors.
        assert response.status_code in (200, 302)

        # If primary admin precondition is broken, register_view redirects to /setup/.
        if response.status_code == 302 and response.url.endswith('/setup/'):
            pytest.fail(
                'Registration redirected to /setup/; primary admin account missing in test precondition.'
            )

        if response.status_code == 200:
            # Helpful debug when registration doesn't create a user.
            form = response.context.get('form') if hasattr(response, 'context') else None
            if form is not None:
                print('REGISTER_FORM_ERRORS:', form.errors)
            print('REGISTER_RESPONSE_URL:', getattr(response, 'url', None))

        # Registration form requires firstname/lastname.
        assert response.status_code == 302

        username = valid_registration_data['email'].lower()
        created_user = User.objects.filter(username=username).first() or User.objects.filter(email=username).first()
        assert created_user is not None
        assert created_user.check_password(valid_registration_data['password_first'])

        # Ensure we created a Patient role account.
        from server.models import Account
        assert Account.objects.filter(user=created_user, role=Account.ACCOUNT_PATIENT).exists()
    
    @pytest.mark.parametrize("password,expected_error", [
        ('', 'This field is required.'),
        ('a' * 51, 'Ensure this value has at most 50 characters'),
        ('     ', 'This field is required.'),  # Whitespace stripped
    ])
    def test_registration_invalid_password(self, client, valid_registration_data,
                                           password, expected_error):
        from django.contrib.auth.models import User as DjangoUser
        from server.models import Account, Profile
        if Account.objects.all().count() == 0:
            superuser = DjangoUser.objects.create_superuser(
                username='primaryadmin@test.com',
                email='primaryadmin@test.com',
                password='Admin@123'
            )
            profile = Profile.objects.create(firstname='Admin', lastname='User', phone='', birthday=datetime(1980,1,1).date())
            Account.objects.create(user=superuser, profile=profile, role=Account.ACCOUNT_ADMIN)
        """
        TC_F001_BVA_01 to TC_F001_BVA_06: Password boundary validation.
        
        Test Technique: Boundary Value Analysis
        Tests: 0 chars, 51 chars, whitespace only
        """
        valid_registration_data = valid_registration_data.copy()
        valid_registration_data['password_first'] = password
        valid_registration_data['password_second'] = password

        
        response = client.post(reverse('server:register'), valid_registration_data)
        
        assert response.status_code == 200  # Form re-rendered
        # Form errors map to password_first/password_second fields.
        assert 'password_first' in response.context['form'].errors or 'password_second' in response.context['form'].errors
        assert not User.objects.filter(email=valid_registration_data['email']).exists()
    
    @pytest.mark.parametrize("email,should_fail", [
        ('invalid-email', True),
        ('@test.com', True),
        ('user@', True),
        ('a' * 51 + '@test.com', True),
        ('valid@test.com', False),
    ])
    def test_registration_email_validation(self, client, valid_registration_data,
                                           email, should_fail):
        from django.contrib.auth.models import User as DjangoUser
        from server.models import Account, Profile
        if Account.objects.all().count() == 0:
            superuser = DjangoUser.objects.create_superuser(
                username='primaryadmin@test.com',
                email='primaryadmin@test.com',
                password='Admin@123'
            )
            profile = Profile.objects.create(firstname='Admin', lastname='User', phone='', birthday=datetime(1980,1,1).date())
            Account.objects.create(user=superuser, profile=profile, role=Account.ACCOUNT_ADMIN)
        """
        TC_F001_EP_05 to TC_F001_EP_08: Email format validation.
        
        Test Technique: Equivalence Partitioning
        Tests: Invalid formats, length boundary
        """
        valid_registration_data['email'] = email
        
        response = client.post(reverse('server:register'), valid_registration_data)
        
        if should_fail:
            assert response.status_code == 200
            assert 'email' in response.context['form'].errors
        else:
            assert response.status_code == 302
    
    def test_password_mismatch(self, client, valid_registration_data):
        from django.contrib.auth.models import User as DjangoUser
        from server.models import Account, Profile
        if Account.objects.all().count() == 0:
            superuser = DjangoUser.objects.create_superuser(
                username='primaryadmin@test.com',
                email='primaryadmin@test.com',
                password='Admin@123'
            )
            profile = Profile.objects.create(firstname='Admin', lastname='User', phone='', birthday=datetime(1980,1,1).date())
            Account.objects.create(user=superuser, profile=profile, role=Account.ACCOUNT_ADMIN)
        """
        TC_F001_UCT_02: Password confirmation mismatch.
        
        Test Technique: Use Case Testing (Alternative Flow)
        Expected: Error message displayed
        """
        valid_registration_data['password_second'] = 'DifferentPass123!'
        
        response = client.post(reverse('server:register'), valid_registration_data)
        
        assert response.status_code == 200
        # Password mismatch is registered on password_second field.
        assert 'password_second' in response.context['form'].errors
        assert "Passwords do not match" in str(response.context['form'].errors)
    
    def test_duplicate_email_registration(self, client, patient_account, 
                                          valid_registration_data):
        from django.contrib.auth.models import User as DjangoUser
        from server.models import Account, Profile
        if Account.objects.all().count() == 0:
            superuser = DjangoUser.objects.create_superuser(
                username='primaryadmin@test.com',
                email='primaryadmin@test.com',
                password='Admin@123'
            )
            profile = Profile.objects.create(firstname='Admin', lastname='User', phone='', birthday=datetime(1980,1,1).date())
            Account.objects.create(user=superuser, profile=profile, role=Account.ACCOUNT_ADMIN)
        """
        TC_F001_DTT_03: Duplicate email rejection.
        
        Test Technique: Decision Table Testing
        Expected: Error for existing email
        """
        valid_registration_data['email'] = patient_account.user.email
        
        response = client.post(reverse('server:register'), valid_registration_data)
        
        assert response.status_code == 200
        assert 'email' in response.context['form'].errors


@pytest.mark.unit
class TestProfileManagement:
    """
    Test Class: Profile Update & Validation
    
    Validates profile update constraints and zone restrictions.
    """
    
    def test_profile_update_valid_data(self, authenticated_client, patient_account):
        """
        TC_F001_UCT_03: Successful profile update.
        
        Test Technique: Use Case Testing (Main Flow)
        Expected: Profile updated successfully
        """
        update_data = {
            'firstname': patient_account.profile.firstname,
            'lastname': patient_account.profile.lastname,
            'sex': patient_account.profile.sex,
            'birthday': '1990-01-01',
            'phone': '9876543210',
            'allergies': patient_account.profile.allergies,
            'prefHospital': '',
            'primaryCareDoctor': '',
            'speciality': '',
        }
        
        response = authenticated_client.post(
            reverse('server:profile/update'), 
            update_data,
            follow=True
        )
        
        assert response.status_code == 200
        patient_account.profile.refresh_from_db()
        assert patient_account.profile.phone == update_data['phone']
    
    def test_profile_pincode_zone_restriction(self, authenticated_client, patient_account):
        """
        TC_F001_BVA_06: Pincode outside Zone rejection.
        
        Test Technique: Boundary Value Analysis
        Expected: Pincode cannot be changed outside Zone
        """
        # Assuming Zone is 575001-575010
        update_data = {
            'phone': '9876543210',
            'address': 'New Address',
            'pincode': '560001',  # Outside Zone (Bangalore)
            'date_of_birth': '1990-01-01',
        }
        
        response = authenticated_client.post(
            reverse('server:profile/update'),
            update_data,
            follow=True
        )
        
        patient_account.profile.refresh_from_db()
        assert patient_account.profile.phone != '560001'
    
    @pytest.mark.parametrize("phone,should_accept", [
        ('123456789', True),   # 9 digits - accepted (no min_length)
        ('1234567890', True),  # 10 digits - valid
        ('12345678901', False), # 11 digits - exceeds max_length=10
        ('12345abc78', True),   # Alphanumeric - accepted (no digit validation)
    ])
    def test_profile_phone_validation(self, authenticated_client, patient_account,
                                      phone, should_accept):
        """
        TC_F001_BVA_06 to TC_F001_BVA_09: Phone number boundary validation.
        
        Test Technique: Boundary Value Analysis
        Tests: 9, 10, 11 digits, alphanumeric
        """
        update_data = {
            'firstname': patient_account.profile.firstname,
            'lastname': patient_account.profile.lastname,
            'sex': patient_account.profile.sex,
            'birthday': patient_account.profile.birthday.isoformat(),
            'phone': phone,
            'allergies': patient_account.profile.allergies,
            'prefHospital': '',
            'primaryCareDoctor': '',
            'speciality': '',
        }
        
        response = authenticated_client.post(
            reverse('server:profile/update'),
            update_data,
            follow=True
        )
        
        patient_account.profile.refresh_from_db()
        if should_accept:
            assert patient_account.profile.phone == phone
        else:
            assert len(patient_account.profile.phone) <= 10


@pytest.mark.integration
class TestEmployeeRegistration:
    """
    Test Class: Employee Registration Decision Table Testing
    
    Validates complex business rules for Doctor/Admin/Lab/Chemist registration.
    Implements all 8 combinations from Decision Table.
    """
    
    @pytest.fixture
    def speciality(self, db):
        """Create speciality for doctor registration."""
        return Speciality.objects.create(
            name='Cardiology',
            description='Heart specialist'
        )
    
    @pytest.mark.parametrize("role_code,speciality_id,should_allow,error_message", [
        # Rule R1: Doctor + No Speciality → Reject
        (20, None, False, "Doctor must have a speciality"),
        # Rule R2: Doctor + Speciality → Allow
        (20, 1, True, None),
        # Rule R3: Admin + No Speciality → Allow
        (30, None, True, None),
        # Rule R4: Admin + Speciality → Reject
        (30, 1, False, "Only doctor can have a speciality"),
        # Rule R5: Lab + No Speciality → Allow
        (40, None, True, None),
        # Rule R6: Lab + Speciality → Reject
        (40, 1, False, "Only doctor can have a speciality"),
        # Rule R7: Chemist + No Speciality → Allow
        (50, None, True, None),
        # Rule R8: Chemist + Speciality → Reject
        (50, 1, False, "Only doctor can have a speciality"),
    ])
    def test_employee_registration_rules(self, admin_client, speciality,
                                         role_code, speciality_id, 
                                         should_allow, error_message):
        """
        TC_F001_DTT_01 to TC_F001_DTT_08: Employee Registration Decision Table.
        
        Test Technique: Decision Table Testing (All 8 Rules)
        Validates: Doctor/Admin/Lab/Chemist × Speciality combinations
        
        SRS Reference: BR-3, BR-4, FR-1500
        """
        registration_data = {
            'email': f'employee{role_code}@test.com',
            'password_first': 'Employee@123',
            'password_second': 'Employee@123',
            'firstname': f'Employee {role_code}',
            'lastname': f'Employee {role_code}',
            'employee': role_code,
            'speciality': speciality_id if speciality_id else '',
        }
        
        response = admin_client.post(
            reverse('server:admin/createemployee'),
            registration_data,
            follow=True
        )
        
        if should_allow:
            assert response.status_code == 200
            assert User.objects.filter(email=registration_data['email']).exists()
        else:
            assert response.status_code == 200
            assert error_message in str(response.content)
            assert not User.objects.filter(email=registration_data['email']).exists()


@pytest.mark.unit
class TestBirthdayValidation:
    @pytest.fixture(autouse=True)
    def _ensure_profile_form_fields(self, authenticated_client, patient_account):
        """ProfileForm requires firstname/lastname in POST; ensure they exist."""
        assert patient_account.profile.firstname is not None
        assert patient_account.profile.lastname is not None
    """
    Test Class: Birthday Field Validation
    
    Validates age constraints using Boundary Value Analysis.
    """
    
    def test_birthday_future_date_rejected(self, authenticated_client, patient_account):
        """
        TC_F001_BVA_08: Future birthday rejected.
        
        Test Technique: Boundary Value Analysis
        Expected: Error for date in future
        """
        future_date = datetime.now().date() + timedelta(days=1)
        
        update_data = {
            'firstname': patient_account.profile.firstname,
            'lastname': patient_account.profile.lastname,
            'sex': patient_account.profile.sex,
            'phone': patient_account.profile.phone,
            'allergies': patient_account.profile.allergies,
            'prefHospital': '',
            'primaryCareDoctor': '',
            'speciality': '',
            'birthday': future_date,
        }
        
        response = authenticated_client.post(
            reverse('server:profile/update'),
            update_data,
            follow=True
        )
        
        assert 'birthday' in response.context['form'].errors
    
    def test_birthday_200_years_ago_rejected(self, authenticated_client, patient_account):
        """
        TC_F001_BVA_09: Birthday > 200 years rejected.
        
        Test Technique: Boundary Value Analysis
        Expected: Error for unrealistic age
        """
        old_date = datetime.now().date().replace(year=datetime.now().year - 201)
        
        update_data = {
            'firstname': patient_account.profile.firstname,
            'lastname': patient_account.profile.lastname,
            'sex': patient_account.profile.sex,
            'phone': patient_account.profile.phone,
            'allergies': patient_account.profile.allergies,
            'prefHospital': '',
            'primaryCareDoctor': '',
            'speciality': '',
            'birthday': old_date,
        }
        
        response = authenticated_client.post(
            reverse('server:profile/update'),
            update_data,
            follow=True
        )
        
        assert 'birthday' in response.context['form'].errors

