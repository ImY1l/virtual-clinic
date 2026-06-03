"""Selenium fixtures for UI/E2E testing.

Provides:
- selenium WebDriver fixture (Chrome headless)
- base_url fixture (Django live_server url)
- patient_credentials fixture (creates a test user + patient profile)

Note: This requires pytest-django and a working Django test database.
"""

import pytest
from django.contrib.auth import get_user_model
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from server.models import Account, Profile



User = get_user_model()


@pytest.fixture(autouse=True)
def _enable_db_access_for_live_server(db):
    """Allow DB access in Django live_server request thread."""
    return None


@pytest.fixture(scope="session")
def live_server_trap_django_db_access(db):
    """Hard-pin DB access for live_server; prevents request thread RuntimeError."""
    return None


@pytest.fixture(scope="session")
def chrome_options():
    """Configure Chrome options for headless CI execution."""
    options = Options()
    #options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-gpu")
    return options


@pytest.fixture(scope="session")
def selenium(chrome_options):
    """Session-scoped Selenium WebDriver."""
    driver_path = ChromeDriverManager().install()

    # Work around occasional chromedriver package/arch mismatch issues on CI/dev machines.
    # If chromedriver cannot be executed (Errno 8), fall back to system chromedriver if present.
    try:
        driver = webdriver.Chrome(
            service=Service(driver_path),
            options=chrome_options,
        )
    except OSError:
        driver = webdriver.Chrome(options=chrome_options)

    driver.implicitly_wait(10)
    yield driver
    driver.quit()


@pytest.fixture(scope="session")
def base_url(live_server):
    """Base URL for page objects."""
    return live_server.url



@pytest.fixture
def patient_credentials(db):
    """Create a test patient user and return credentials."""
    email = "e2e_patient@test.com"
    password = "E2EPass123!"

    User.objects.filter(email=email).delete()

    user = User.objects.create_user(
        username=email,
        email=email,
        password=password,
        first_name="E2E",
        last_name="Patient",
    )

    # The app model names `Patient` in some older test versions; in this repo it is represented by Profile/Account.
    # Create minimal Profile + Account for UI flows.
    profile = Profile.objects.create(
        firstname="E2E",
        lastname="Patient",
        phone="0123456789",
        birthday="1990-01-01",
    )

    Account.objects.create(
        user=user,
        profile=profile,
        role=10,  # Patient
    )


    return {"email": email, "password": password}

