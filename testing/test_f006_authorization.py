import pytest


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