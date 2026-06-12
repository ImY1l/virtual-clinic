"""
F-004: Chemist Medicine Delivery Workflow — backend (pytest + Django test client).

Source of truth: F004_Test_Cases.docx (TDS Section 2.2.5 — STT, UCT).
Reuses the shared fixtures from testing/conftest.py
(chemist_client / chemist_account, doctor_account, patient_account, prescription)
rather than creating new accounts.

Real routes under test: /prescription/list/, /prescription/update/
"""
import pytest

from server.models import Prescription


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
