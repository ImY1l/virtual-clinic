import pytest
from server.forms import LoginForm
from django.contrib.auth.models import User


@pytest.mark.django_db
def test_TC_F006_DTT_001_login_page_accessible(
    client
):
    response = client.get("/")

    assert response.status_code == 302
    assert "/setup/" in response.url

# ============================================================
# DTT_002
# Admin can access admin users page, while others cannot
# ============================================================

@pytest.mark.django_db
def test_TC_F006_DTT_002_admin_access_admin_users(
    admin_client,
    doctor_client,
    lab_client,
    chemist_client,
    client,
    patient_account
):
    # Administrator
    response = admin_client.get("/admin/users/")
    assert response.status_code == 200

    # Doctor
    response = doctor_client.get("/admin/users/")
    assert response.status_code in [302, 403]

    # Patient
    client.force_login(patient_account.user)
    response = client.get("/admin/users/")
    assert response.status_code in [302, 403]

    # Laboratory Staff
    response = lab_client.get("/admin/users/")
    assert response.status_code in [302, 403]

    # Chemist
    response = chemist_client.get("/admin/users/")
    assert response.status_code in [302, 403]

    # Unauthenticated
    anon = client.__class__()
    response = anon.get("/admin/users/")
    assert response.status_code == 302

# ============================================================
# DTT_003
# Doctor can access Appointments page, while others cannot
# ============================================================

@pytest.mark.django_db
def test_TC_F006_DTT_003_doctor_access_appointments(
    doctor_client,
    admin_client,
    lab_client,
    chemist_client,
    client,
    patient_account
):
    response = doctor_client.get("/appointment/list/")
    assert response.status_code == 200

    response = admin_client.get("/appointment/list/")
    assert response.status_code in [302, 403]

    client.force_login(patient_account.user)
    response = client.get("/appointment/list/")
    assert response.status_code in [302, 403]

    response = lab_client.get("/appointment/list/")
    assert response.status_code in [302, 403]

    response = chemist_client.get("/appointment/list/")
    assert response.status_code in [302, 403]

# ============================================================
# DTT_004
# Patient can access Appointments page, while others cannot
# ============================================================

@pytest.mark.django_db
def test_TC_F006_DTT_004_patient_access_appointments(
    client,
    patient_account,
    admin_client,
    doctor_client,
    lab_client,
    chemist_client
):
    client.force_login(patient_account.user)

    response = client.get("/appointment/list/")
    assert response.status_code == 200

    response = admin_client.get("/appointment/list/")
    assert response.status_code in [302, 403]

    response = doctor_client.get("/appointment/list/")
    assert response.status_code in [302, 403]

    response = lab_client.get("/appointment/list/")
    assert response.status_code in [302, 403]

    response = chemist_client.get("/appointment/list/")
    assert response.status_code in [302, 403]
    
# ============================================================
# DTT_005
# Doctor can access prescription create page, while others cannot
# ============================================================

@pytest.mark.django_db
def test_TC_F006_DTT_005_doctor_access_prescription_create(
    doctor_client,
    admin_client,
    lab_client,
    chemist_client,
    client,
    patient_account
):
    # Doctor
    response = doctor_client.get(
        "/prescription/create/"
    )
    assert response.status_code == 200

    # Administrator
    response = admin_client.get(
        "/prescription/create/"
    )
    assert response.status_code in [302, 403]

    # Patient
    client.force_login(
        patient_account.user
    )

    response = client.get(
        "/prescription/create/"
    )
    assert response.status_code in [302, 403]

    # Laboratory Staff
    response = lab_client.get(
        "/prescription/create/"
    )
    assert response.status_code in [302, 403]

    # Chemist
    response = chemist_client.get(
        "/prescription/create/"
    )
    assert response.status_code in [302, 403]

    # Unauthenticated
    anon_client = client.__class__()

    response = anon_client.get(
        "/prescription/create/"
    )
    assert response.status_code == 302

# ============================================================
# DTT_006
# Laboratory Staff can access medical test upload page, while others cannot
# ============================================================
@pytest.mark.django_db
def test_TC_F006_DTT_006_lab_access_medtest_upload(
    lab_client,
    admin_client,
    doctor_client,
    chemist_client,
    client,
    patient_account
):
    # Laboratory Staff
    response = lab_client.get(
        "/medtest/upload/"
    )
    assert response.status_code == 200

    # Administrator
    response = admin_client.get(
        "/medtest/upload/"
    )
    assert response.status_code in [302, 403]

    # Doctor
    response = doctor_client.get(
        "/medtest/upload/"
    )
    assert response.status_code in [302, 403]

    # Patient
    client.force_login(
        patient_account.user
    )

    response = client.get(
        "/medtest/upload/"
    )
    assert response.status_code in [302, 403]

    # Chemist
    response = chemist_client.get(
        "/medtest/upload/"
    )
    assert response.status_code in [302, 403]

    # Unauthenticated
    anon_client = client.__class__()

    response = anon_client.get(
        "/medtest/upload/"
    )
    assert response.status_code == 302

# ============================================================
# DTT_007
# Chemist can access prescription list page, while others cannot
# ============================================================

@pytest.mark.django_db
def test_TC_F006_DTT_007_chemist_access_prescription_list(
    chemist_client,
    admin_client,
    doctor_client,
    lab_client,
    client,
    patient_account
):
    # Chemist
    response = chemist_client.get(
        "/prescription/list/"
    )
    assert response.status_code == 200

    # Administrator
    response = admin_client.get(
        "/prescription/list/"
    )
    assert response.status_code in [302, 403]

    # Doctor
    response = doctor_client.get(
        "/prescription/list/"
    )
    assert response.status_code in [302, 403]

    # Patient
    client.force_login(
        patient_account.user
    )

    response = client.get(
        "/prescription/list/"
    )
    assert response.status_code in [302, 403]

    # Laboratory Staff
    response = lab_client.get(
        "/prescription/list/"
    )
    assert response.status_code in [302, 403]

    # Unauthenticated
    anon_client = client.__class__()

    response = anon_client.get(
        "/prescription/list/"
    )
    assert response.status_code == 302

# ============================================================
# DTT_008
# Admin can access create employee page, while others cannot
# ============================================================

@pytest.mark.django_db
def test_TC_F006_DTT_008_admin_access_create_employee(
    admin_client,
    doctor_client,
    lab_client,
    chemist_client,
    client,
    patient_account
):
    # Administrator
    response = admin_client.get(
        "/admin/createemployee/"
    )
    assert response.status_code == 200

    # Doctor
    response = doctor_client.get(
        "/admin/createemployee/"
    )
    assert response.status_code in [302, 403]

    # Patient
    client.force_login(
        patient_account.user
    )

    response = client.get(
        "/admin/createemployee/"
    )
    assert response.status_code in [302, 403]

    # Laboratory Staff
    response = lab_client.get(
        "/admin/createemployee/"
    )
    assert response.status_code in [302, 403]

    # Chemist
    response = chemist_client.get(
        "/admin/createemployee/"
    )
    assert response.status_code in [302, 403]

    # Unauthenticated
    anon_client = client.__class__()

    response = anon_client.get(
        "/admin/createemployee/"
    )
    assert response.status_code == 302

# ============================================================
# BVA_001
# Email Length = 50 Characters
# ============================================================

@pytest.mark.django_db
def test_TC_F006_BVA_001_email_length_50():

    email = ("a" * 41) + "@test.com"   # 50 chars
    password = "ValidPass123"

    User.objects.create_user(
        username=email,
        email=email,
        password=password
    )

    form = LoginForm(
        data={
            "email": email,
            "password": password
        }
    )

    assert form.is_valid()

# ============================================================
# BVA_002
# Email Length = 51 Characters
# ============================================================

@pytest.mark.django_db
def test_TC_F006_BVA_002_email_length_51():

    email = ("a" * 42) + "@test.com"   # 51 chars

    form = LoginForm(
        data={
            "email": email,
            "password": "ValidPass123"
        }
    )

    assert not form.is_valid()

# ============================================================
# BVA_003
# Password Length = 1 Character
# ============================================================

@pytest.mark.django_db
def test_TC_F006_BVA_003_password_length_1():

    email = "bva1@test.com"
    password = "a"

    User.objects.create_user(
        username=email,
        email=email,
        password=password
    )

    form = LoginForm(
        data={
            "email": email,
            "password": password
        }
    )

    assert form.is_valid()

# ============================================================
# BVA_004
# Password Length = 50 Characters
# ============================================================

@pytest.mark.django_db
def test_TC_F006_BVA_004_password_length_50():

    email = "bva50@test.com"
    password = "a" * 50

    User.objects.create_user(
        username=email,
        email=email,
        password=password
    )

    form = LoginForm(
        data={
            "email": email,
            "password": password
        }
    )

    assert form.is_valid()

# ============================================================
# BVA_005
# Password Length = 51 Characters
# ============================================================

@pytest.mark.django_db
def test_TC_F006_BVA_005_password_length_51():

    email = "bva51@test.com"
    password = "a" * 51

    form = LoginForm(
        data={
            "email": email,
            "password": password
        }
    )

    assert not form.is_valid()

# ============================================================
# BVA_006
# Password Length = 0 Characters
# ============================================================

@pytest.mark.django_db
def test_TC_F006_BVA_006_password_length_0():

    email = "bva0@test.com"

    form = LoginForm(
        data={
            "email": email,
            "password": ""
        }
    )

    assert not form.is_valid()