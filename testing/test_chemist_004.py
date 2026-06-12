"""
F-004: Chemist Medicine Delivery Workflow — backend (pytest + Django test client).

Source of truth: F004_Test_Cases.docx (TDS Section 2.2.5 — STT, UCT).
Reuses the shared fixtures from testing/conftest.py
(chemist_client / chemist_account, doctor_account, patient_account, prescription)
rather than creating new accounts.

Real routes under test: /prescription/list/, /prescription/update/
"""
import pytest
from django.contrib.auth.models import User as DjangoUser
from django.utils import timezone

from server.models import Account, Profile, Prescription


@pytest.mark.django_db
class TestFeatureF004ChemistDelivery:

    def _update_payload(self, prescription, active=False):
        """Build a PrescriptionForm POST payload from an existing prescription.

        The Update Prescription form exposes `active` as a BooleanField(required=False).
        A checked box submits the key; an *unchecked* box omits it entirely. So to mark
        a prescription Delivered we omit `active` (-> cleaned_data['active'] == False),
        which mirrors a Chemist unchecking the box in the UI.
        """
        payload = {
            'patient': prescription.patient.id,
            'doctor': prescription.doctor.id,
            'date': prescription.date.strftime('%Y-%m-%d'),
            'medication': prescription.medication,
            'strength': prescription.strength,
            'instruction': prescription.instruction,
            'refill': prescription.refill,
        }
        if active:
            payload['active'] = 'on'  # checked checkbox keeps it Active
        return payload

    # 2.2.5.1 State Transition Testing (0-switch) — Delivery Completion Flag (UC-13)
    def test_TC_F004_STT_01_mark_prescription_delivered(self, chemist_client, prescription):
        """TC_F004_STT_01: Chemist marks an open prescription as delivered
        (active: True -> False) via /prescription/update/.

        Valid 0-switch transition: verifies the delivery flag is persisted as
        False and the success message 'Prescription has been updated' is shown.
        """
        # Pre-condition: an active (open) prescription exists.
        assert prescription.active is True

        response = chemist_client.post(
            '/prescription/update/?pk={}'.format(prescription.pk),
            data=self._update_payload(prescription, active=False),
        )

        # The view re-renders the Update page with a success alert on a valid POST.
        assert response.status_code == 200
        assert b"Prescription has been updated" in response.content

        # Core STT assertion: active=False is persisted (Status -> "Delivered").
        prescription.refresh_from_db()
        assert prescription.active is False

    def test_TC_F004_STT_02_delivered_prescription_has_no_update_control(self, chemist_client, prescription):
        """TC_F004_STT_02: Once a prescription is Delivered (active=False), the
        chemist's list exposes no state-changing control, so the invalid 0-switch
        transition (False -> change) cannot be triggered through the interface.

        Verifies the row shows Status 'Delivered', no Update control is rendered
        for it, and the state remains False (no change occurs).
        """
        # Arrange: the prescription has already been delivered.
        prescription.active = False
        prescription.save()

        # Act: chemist views the prescription list (chemist sees all prescriptions).
        response = chemist_client.get('/prescription/list/')
        assert response.status_code == 200
        content = response.content.decode()

        # The delivered prescription is present and shown as "Delivered".
        assert prescription.medication in content   # the row is rendered
        assert "Delivered" in content

        # No state-changing control is offered: the Update link (which only
        # renders while active) is absent for this delivered prescription.
        update_link = '/prescription/update/?pk={}'.format(prescription.pk)
        assert update_link not in content

        # The state is unchanged.
        prescription.refresh_from_db()
        assert prescription.active is False

    # 2.2.5.2 Use Case Testing — Access Control on Prescription Views (Security Flow)
    def test_TC_F004_UCT_02_access_control_on_prescription_views(
        self, client, prescription, patient_account, chemist_account, doctor_account
    ):
        """TC_F004_UCT_02: Role-based access control on /prescription/list/.

        - An unauthenticated request is redirected to the login page ('/').
        - A Patient sees only their OWN prescriptions, not another patient's.
        - The Chemist sees ALL prescriptions (current implemented behaviour;
          per-pincode need-to-know scoping is not implemented in this build).
        """
        # `prescription` belongs to patient_account (John Doe). Seed a second
        # patient (Patient B) with their own prescription to test isolation.
        patient_b_user = DjangoUser.objects.create_user(
            username='patient_b@test.com', email='patient_b@test.com',
            password='Patient@123', first_name='Jane', last_name='Roe',
        )
        patient_b_profile = Profile.objects.create(firstname='Jane', lastname='Roe', phone='0123456700')
        patient_b = Account.objects.create(
            user=patient_b_user, profile=patient_b_profile, role=Account.ACCOUNT_PATIENT,
        )
        Prescription.objects.create(
            patient=patient_b, doctor=doctor_account, date=timezone.now().date(),
            medication='Ibuprofen 400mg', strength='1 tablet',
            instruction='Once daily', refill=0, active=True,
        )

        # 1. Unauthenticated access is redirected to the login page.
        response = client.get('/prescription/list/')
        assert response.status_code == 302
        assert response.url == '/'

        # 2. Patient A (John Doe) sees only their own prescription.
        client.force_login(patient_account.user)
        content = client.get('/prescription/list/').content.decode()
        assert 'Paracetamol 500mg' in content       # own prescription
        assert 'Ibuprofen 400mg' not in content     # NOT Patient B's
        client.logout()

        # 3. Chemist sees all prescriptions (current implemented behaviour).
        client.force_login(chemist_account.user)
        content = client.get('/prescription/list/').content.decode()
        assert 'Paracetamol 500mg' in content
        assert 'Ibuprofen 400mg' in content

    # 2.2.5.2 Use Case Testing — Modify Delivered Prescription (Exception Flow)
    def test_TC_F004_UCT_03_cannot_modify_delivered_prescription(self, chemist_client, prescription):
        """TC_F004_UCT_03: A delivered prescription cannot be modified through the
        Chemist interface — no modification control is offered and the state
        remains active=False (no update is applied).

        Same defended behaviour as STT_02, exercised here as the UCT exception
        flow (different test technique, same requirement: BR-9 / UC-13).
        """
        # Arrange: a delivered prescription.
        prescription.active = False
        prescription.save()

        # Act: chemist views the list.
        content = chemist_client.get('/prescription/list/').content.decode()

        # No modification control is offered for the delivered prescription...
        assert 'Delivered' in content
        update_link = '/prescription/update/?pk={}'.format(prescription.pk)
        assert update_link not in content

        # ...and its state is unchanged.
        prescription.refresh_from_db()
        assert prescription.active is False
