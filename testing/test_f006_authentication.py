import pytest
from selenium.webdriver.common.by import By


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
        "WrongPass"
    )

    selenium.find_element(
        By.CSS_SELECTOR,
        "input[type='submit']"
    ).click()

    assert "Incorrect" in selenium.page_source


@pytest.mark.django_db
def test_TC_F006_EP_003_nonexistent_account(
    selenium,
    base_url
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

    assert "does not exist" in selenium.page_source