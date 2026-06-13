import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from django.contrib.auth.models import User
from server.models import Account, Profile

@pytest.mark.nondestructive
@pytest.mark.django_db
def test_TC_F006_EP_001_valid_login(
    selenium,
    base_url,
    patient_credentials
):
    selenium.get(base_url)

    selenium.find_element(
        By.ID,
        "id_email"
    ).send_keys(
        patient_credentials["email"]
    )

    selenium.find_element(
        By.ID,
        "id_password"
    ).send_keys(
        patient_credentials["password"]
    )

    selenium.find_element(
        By.CSS_SELECTOR,
        "input[type='submit']"
    ).click()

    assert "/profile/" in selenium.current_url

@pytest.mark.nondestructive
@pytest.mark.django_db
def test_TC_F006_EP_002_invalid_password(
    selenium,
    base_url,
    patient_credentials
):
    selenium.get(base_url)

    selenium.find_element(
        By.ID,
        "id_email"
    ).send_keys(
        patient_credentials["email"]
    )

    selenium.find_element(
        By.ID,
        "id_password"
    ).send_keys(
        "WrongPass"
    )

    selenium.find_element(
        By.CSS_SELECTOR,
        "input[type='submit']"
    ).click()

    assert "/profile/" not in selenium.current_url


@pytest.mark.nondestructive
@pytest.mark.django_db
def test_TC_F006_EP_003_nonexistent_account(
    selenium,
    base_url,
    patient_credentials
):
    selenium.get(base_url)

    selenium.find_element(
        By.ID,
        "id_email"
    ).send_keys(
        "idontexist@test.com"
    )

    selenium.find_element(
        By.ID,
        "id_password"
    ).send_keys(
        "Password123"
    )

    selenium.find_element(
        By.CSS_SELECTOR,
        "input[type='submit']"
    ).click()

    assert "/profile/" not in selenium.current_url

@pytest.mark.nondestructive
@pytest.mark.django_db
def test_TC_F006_EP_004_empty_email(
    selenium,
    base_url,
    patient_credentials
):
    selenium.get(base_url)

    selenium.find_element(
        By.ID,
        "id_password"
    ).send_keys(
        "E2EPass123!"
    )

    selenium.find_element(
        By.CSS_SELECTOR,
        "input[type='submit']"
    ).click()

    email = selenium.find_element(
        By.ID,
        "id_email"
    )

    assert email.get_attribute(
        "validationMessage"
    ) != ""


@pytest.mark.nondestructive
@pytest.mark.django_db
def test_TC_F006_EP_005_empty_password(
    selenium,
    base_url,
    patient_credentials
):
    selenium.get(base_url)

    selenium.find_element(
        By.ID,
        "id_email"
    ).send_keys(
        patient_credentials["email"]
    )

    selenium.find_element(
        By.CSS_SELECTOR,
        "input[type='submit']"
    ).click()

    password = selenium.find_element(
        By.ID,
        "id_password"
    )

    assert password.get_attribute(
        "validationMessage"
    ) != ""

@pytest.mark.nondestructive
@pytest.mark.django_db
def test_TC_F006_EP_006_archived_account(
    selenium,
    live_server
):
    email = "archived@test.com"
    password = "Archived123!"

    user = User.objects.create_user(
        username=email,
        email=email,
        password=password
    )

    profile = Profile.objects.create(
        firstname="Archived",
        lastname="User",
        phone="0123456789",
        birthday="1990-01-01"
    )

    Account.objects.create(
        user=user,
        profile=profile,
        role=Account.ACCOUNT_PATIENT,
        archive=True
    )

    selenium.get(live_server.url)

    selenium.find_element(
        By.ID,
        "id_email"
    ).send_keys(email)

    selenium.find_element(
        By.ID,
        "id_password"
    ).send_keys(password)

    selenium.find_element(
        By.CSS_SELECTOR,
        "input[type='submit']"
    ).click()

    WebDriverWait(selenium, 10).until(
        lambda d: "/register/" in d.current_url
    )

    assert "/register/" in selenium.current_url

@pytest.mark.nondestructive
@pytest.mark.django_db
def test_TC_F006_EP_007_sql_injection_attempt(
    selenium,
    base_url,
    patient_credentials
):
    selenium.get(base_url)

    selenium.find_element(
        By.ID,
        "id_email"
    ).send_keys(
        "' OR 1=1 --"
    )

    selenium.find_element(
        By.ID,
        "id_password"
    ).send_keys(
        "' OR 1=1 --"
    )

    selenium.find_element(
        By.CSS_SELECTOR,
        "input[type='submit']"
    ).click()

    assert "/profile/" not in selenium.current_url