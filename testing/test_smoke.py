import pytest
from server.models import Account, Profile

@pytest.mark.smoke
def test_fixtures_work(patient_account, doctor_account, appointment, prescription):
    """Verify all core fixtures create valid objects."""
    # Verify patient
    assert patient_account.role == Account.ACCOUNT_PATIENT
    assert isinstance(patient_account.profile, Profile)
    assert patient_account.profile.firstname == 'John'
    
    # Verify doctor
    assert doctor_account.role == Account.ACCOUNT_DOCTOR
    assert doctor_account.profile.speciality is not None
    
    # Verify appointment
    assert appointment.patient == patient_account
    assert appointment.doctor == doctor_account
    assert appointment.status == 'Active'
    
    # Verify prescription
    assert prescription.patient == patient_account
    assert prescription.doctor == doctor_account
    assert prescription.medication == 'Paracetamol 500mg'
    
    print("✅ All fixtures working correctly!")