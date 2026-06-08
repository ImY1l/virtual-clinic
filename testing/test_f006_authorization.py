import pytest
from server.forms import LoginForm

# ============================================================
# DTT_002
# Patient cannot access Admin Users page
# ============================================================

@pytest.mark.django_db
def test_TC_F006_DTT_002_patient_denied_admin_users(
    client,
    patient_account
):
    client.force_login(patient_account.user)

    response = client.get(
        "/admin/users/"
    )

    assert response.status_code in [302, 403]


# ============================================================
# DTT_003
# Doctor cannot access Admin Users page
# ============================================================

@pytest.mark.django_db
def test_TC_F006_DTT_003_doctor_denied_admin_users(
    doctor_client
):
    response = doctor_client.get(
        "/admin/users/"
    )

    assert response.status_code in [302, 403]


# ============================================================
# DTT_004
# Admin can access Admin Users page
# ============================================================

@pytest.mark.django_db
def test_TC_F006_DTT_004_admin_access_users(
    admin_client
):
    response = admin_client.get(
        "/admin/users/"
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
# Patient cannot create prescriptions
# ============================================================

@pytest.mark.django_db
def test_TC_F006_DTT_006_patient_denied_prescription_create(
    client,
    patient_account
):
    client.force_login(patient_account.user)

    response = client.get(
        "/prescription/create/"
    )

    assert response.status_code in [302, 403]


# ============================================================
# DTT_007
# Lab can upload medical tests
# ============================================================

@pytest.mark.django_db
def test_TC_F006_DTT_007_lab_access_medtest_upload(
    lab_client
):
    response = lab_client.get(
        "/medtest/upload/"
    )

    assert response.status_code == 200


# ============================================================
# DTT_008
# Patient cannot upload medical tests
# ============================================================

@pytest.mark.django_db
def test_TC_F006_DTT_008_patient_denied_medtest_upload(
    client,
    patient_account
):
    client.force_login(patient_account.user)

    response = client.get(
        "/medtest/upload/"
    )

    assert response.status_code in [302, 403]

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