"""
Selenium E2E Tests: F-001 - Patient Registration & Profile Management
"""
import pytest
from ui_tests.pages.register_page import RegisterPage
from ui_tests.pages.login_page import LoginPage
from ui_tests.pages.profile_page import ProfilePage
from faker import Faker


from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


fake = Faker()

# This decorator grants the test permission to use the Django test database
@pytest.mark.django_db
class TestRegistrationE2E:
    """E2E Test Class: Patient Registration Workflow"""

    @pytest.mark.nondestructive
    def test_successful_patient_registration(self, selenium, base_url):
        """TSCEN-01-001: Complete patient registration journey."""
        register_page = RegisterPage(selenium, base_url)
        register_page.open()
        
        email = fake.email()
        password = 'SecurePass123!'
        first_name = fake.first_name()
        last_name = fake.last_name()
        
        register_page.register(email, password, password, first_name, last_name)
        
        # Verify redirect to profile page or dashboard
        assert 'profile' in selenium.current_url or 'dashboard' in selenium.current_url
        
        # Verify user's name is on the page
        assert first_name in selenium.page_source
        
        # ROBUST FIX: Check if "Logout" text exists anywhere on the page
        # This avoids brittle element-locating issues if the button is in a navbar dropdown
        assert "Logout" in selenium.page_source

    @pytest.mark.nondestructive
    def test_registration_password_mismatch(self, selenium, base_url):
        """TSCEN-01-002: Registration with mismatched passwords."""
        register_page = RegisterPage(selenium, base_url)
        register_page.open()
        
        email = fake.email()
        register_page.register(
            email=email,
            password='Password123!',
            confirm_password='DifferentPass456!',
            first_name=fake.first_name(),
            last_name=fake.last_name()
        )
        
        # Verify error message is present
        assert 'password' in selenium.page_source.lower()
        assert 'match' in selenium.page_source.lower()

    @pytest.mark.nondestructive
    def test_registration_missing_fields(self, selenium, base_url):
        """TSCEN-01-003: Registration with missing required fields."""
        register_page = RegisterPage(selenium, base_url)
        register_page.open()
        
        register_page.submit_empty_form()
        
        # Verify Django's default "required" error message appears
        assert 'required' in selenium.page_source.lower()

    @pytest.mark.nondestructive
    @pytest.mark.parametrize("password,expected_error", [
        ('', 'required'),
        ('a' * 51, '50'), # Django's "Ensure this value has at most 50 characters"
    ])
    @pytest.mark.nondestructive
    def test_registration_password_boundaries(self, selenium, base_url, password, expected_error):
        """TSCEN-01-004: Password boundary validation (BVA)."""
        register_page = RegisterPage(selenium, base_url)
        register_page.open()
        
        register_page.register(
            email=fake.email(),
            password=password,
            confirm_password=password,
            first_name=fake.first_name(),
            last_name=fake.last_name()
        )
        
        assert expected_error in selenium.page_source.lower()







@pytest.mark.django_db
class TestProfileUpdateE2E:
    """E2E Test Class: Profile Update Workflow"""
    
    @pytest.mark.nondestructive
    def test_profile_update_success(self, selenium, base_url, patient_credentials, db):
        """TSCEN-01-005: Successful profile update."""
        # Clear cookies to ensure a fresh login state
        selenium.delete_all_cookies()
        
        login_page = LoginPage(selenium, base_url)
        login_page.open()
        login_page.login(patient_credentials['email'], patient_credentials['password'])
        
        # Wait for the URL to change away from /login/
        WebDriverWait(selenium, 10).until(
            lambda driver: "login" not in driver.current_url.lower()
        )
        
        # Navigate to profile update
        profile_page = ProfilePage(selenium, base_url)
        profile_page.open()
        
        # Verify we actually made it to the update page
        assert "profile" in selenium.current_url, f"Expected profile page, got: {selenium.current_url}"
        
        new_phone = '9876543210'
        new_address = 'New Test Address, Mangalore'
        
        profile_page.update_profile(
            phone=new_phone,
            address=new_address,
            pincode='575001',
            date_of_birth='1990-01-01'
        )
        
        # Verify success message
        assert 'success' in selenium.page_source.lower() or 'updated' in selenium.page_source.lower()
        
        # Reload to verify data persisted
        profile_page.open()
        assert new_phone in selenium.page_source
        assert new_address in selenium.page_source

    @pytest.mark.nondestructive
    def test_profile_invalid_pincode(self, selenium, base_url, patient_credentials, db):
        """TSCEN-01-006: Profile update with pincode outside Zone."""
        selenium.delete_all_cookies()
        
        login_page = LoginPage(selenium, base_url)
        login_page.open()
        login_page.login(patient_credentials['email'], patient_credentials['password'])
        
        WebDriverWait(selenium, 10).until(
            lambda driver: "login" not in driver.current_url.lower()
        )
        
        profile_page = ProfilePage(selenium, base_url)
        profile_page.open()
        
        # Try to update with invalid pincode (Bangalore)
        profile_page.update_profile(
            phone='9876543210',
            address='New Address',
            pincode='560001',  # Outside Zone
            date_of_birth='1990-01-01'
        )
        
        # Verify error or rejection
        assert 'zone' in selenium.page_source.lower() or 'invalid' in selenium.page_source.lower() or 'error' in selenium.page_source.lower()