import pytest
from server.forms import LoginForm


@pytest.mark.django_db
def test_TC_F006_DTT_001_login_page_accessible(
    client
):
    response = client.get("/")

    assert response.status_code == 302
    assert "/setup/" in response.url

# ============================================================
# DTT_002
# Admin can access Admin Users page
# ============================================================

@pytest.mark.django_db
def test_TC_F006_DTT_002_admin_access_admin_users(
    admin_client
):
    response = admin_client.get("/admin/users/")
    assert response.status_code == 200


# ============================================================
# DTT_003
# Doctor can access Appointments page
# ============================================================

@pytest.mark.django_db
def test_TC_F006_DTT_003_doctor_access_appointments(
    doctor_client
):
    response = doctor_client.get(
        "/appointment/list/"
    )

    assert response.status_code == 200

# ============================================================
# DTT_004
# Patient can access Appointments page
# ============================================================

@pytest.mark.django_db
def test_TC_F006_DTT_004_patient_access_appointments(
    client,
    patient_account
):
    client.force_login(patient_account.user)

    response = client.get(
        "/appointment/list/"
    )

    assert response.status_code == 200

# ============================================================
# DTT_005
# Doctor can create prescriptions
# ============================================================

@pytest.mark.django_db
def test_TC_F006_DTT_005_doctor_access_prescription_create(
    doctor_client
):
    response = doctor_client.get(
        "/prescription/create/"
    )

    assert response.status_code == 200

# ============================================================
# DTT_006
# Lab can access medical test upload page
# ============================================================

@pytest.mark.django_db
def test_TC_F006_DTT_006_lab_access_medtest_upload(
    lab_client
):
    response = lab_client.get(
        "/medtest/upload/"
    )

    assert response.status_code == 200

# ============================================================
# DTT_007
# Chemist can access prescription list page
# ============================================================

@pytest.mark.django_db
def test_TC_F006_DTT_007_chemist_access_prescription_list(
    chemist_client
):
    response = chemist_client.get(
        "/prescription/list/"
    )

    assert response.status_code == 200

# ============================================================
# DTT_008
# Admin can access create employee page
# ============================================================

@pytest.mark.django_db
def test_TC_F006_DTT_008_admin_access_create_employee(
    admin_client
):
    response = admin_client.get(
        "/admin/createemployee/"
    )

    assert response.status_code == 200

@pytest.mark.django_db
def test_TC_F006_BVA_001_email_length_49():
    email = ("a" * 37) + "@test.com"  # total length 46-49 range

    form = LoginForm(
        data={
            "email": email,
            "password": "Password123"
        }
    )

    assert form.is_valid() is False

@pytest.mark.django_db
def test_TC_F006_BVA_002_email_length_50():
    email = ("a" * 38) + "@test.com"

    form = LoginForm(
        data={
            "email": email,
            "password": "Password123"
        }
    )

    assert form.is_valid() is False

@pytest.mark.django_db
def test_TC_F006_BVA_003_email_length_51():
    email = ("a" * 39) + "@test.com"

    form = LoginForm(
        data={
            "email": email,
            "password": "Password123"
        }
    )

    assert form.is_valid() is False

@pytest.mark.django_db
def test_TC_F006_BVA_004_password_length_49(
    patient_account
):
    form = LoginForm(
        data={
            "email": patient_account.user.username,
            "password": "a" * 49
        }
    )

    assert len(form["password"].value()) == 49

@pytest.mark.django_db
def test_TC_F006_BVA_005_password_length_50(
    patient_account
):
    form = LoginForm(
        data={
            "email": patient_account.user.username,
            "password": "a" * 50
        }
    )

    assert len(form["password"].value()) == 50

@pytest.mark.django_db
def test_TC_F006_BVA_006_password_length_51(
    patient_account
):
    form = LoginForm(
        data={
            "email": patient_account.user.username,
            "password": "a" * 51
        }
    )

    assert not form.is_valid()
    assert "password" in form.errors