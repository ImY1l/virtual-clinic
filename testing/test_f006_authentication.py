import pytest
from selenium.webdriver.common.by import By
from django.contrib.auth.models import User
from server.models import Account, Profile


@pytest.mark.django_db
def test_TC_F006_EP_001_valid_login(
    selenium,
    base_url,
    patient_credentials
):
    selenium.get("http://127.0.0.1:8000/")

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


@pytest.mark.django_db
def test_TC_F006_EP_002_invalid_password(
    selenium,
    patient_credentials
):
    selenium.get("http://127.0.0.1:8000/")

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

@pytest.mark.django_db
def test_TC_F006_EP_003_nonexistent_account(
    selenium
):
    selenium.get("http://127.0.0.1:8000/")

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


@pytest.mark.django_db
def test_TC_F006_EP_004_empty_email(
    selenium
):
    selenium.get("http://127.0.0.1:8000/")

    selenium.find_element(
        By.ID,
        "id_password"
    ).send_keys(
        "Patient@123"
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


@pytest.mark.django_db
def test_TC_F006_EP_005_empty_password(
    selenium
):
    selenium.get("http://127.0.0.1:8000/")

    selenium.find_element(
        By.ID,
        "id_email"
    ).send_keys(
        "patient@test.com"
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

@pytest.mark.django_db
def test_TC_F006_EP_007_sql_injection_attempt(
    selenium
):
    selenium.get("http://127.0.0.1:8000/")

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

    # Injection should not authenticate the user
    assert "/profile/" not in selenium.current_url