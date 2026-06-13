"""
F-005: Lab Test Request & Report Upload — backend (pytest + Django test client).

Source of truth: F005_Test_Cases.docx (TDS Section 2.2.6 — EP, BVA, STT).
Reuses shared fixtures from testing/conftest.py
(lab_client / lab_account, doctor_account, patient_account, hospital, medical_test).

Real routes under test: /medtest/upload/, /medtest/update/, /medtest/display/, /medtest/list/

NOTE: Some cases assert the file-size validation REQUIRED by SRS 2.5. The build
does not implement size validation, so those cases are expected to FAIL and
document the defect (do not weaken these assertions).
"""
import pytest
from django.contrib.auth.models import User as DjangoUser
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone

from server.forms import MedTestForm
from server.models import Account, MedicalTest, Profile


@pytest.mark.django_db
class TestFeatureF005LabUpload:

    @pytest.fixture(autouse=True)
    def _isolate_media(self, settings, tmp_path):
        """Redirect uploads to a temp dir so the repo's media/ is never touched."""
        settings.MEDIA_ROOT = str(tmp_path)

    def _upload_payload(self, doctor_account, patient_account, hospital, **overrides):
        """Required MedTestForm fields for an upload (a Lab must supply doctor +
        hospital since no defaults are injected for role 40)."""
        data = {
            'name': 'CBC Test',
            'date': timezone.now().date().strftime('%Y-%m-%d'),
            'hospital': hospital.id,
            'description': 'Complete Blood Count',
            'doctor': doctor_account.id,
            'patient': patient_account.id,
        }
        data.update(overrides)
        return data

    # ----- 2.2.6.1 Equivalence Partitioning — File Size (SRS 2.5) -----

    def test_TC_F005_EP_01_empty_file_rejected(self, lab_client, doctor_account, patient_account, hospital):
        """TC_F005_EP_01: A 0-byte (empty) lab report must be rejected and no
        MedicalTest record persisted. Documents the empty-file validation
        requirement (SRS 2.5)."""
        empty = SimpleUploadedFile('empty_file.pdf', b'', content_type='application/pdf')
        data = self._upload_payload(doctor_account, patient_account, hospital, image1=empty)

        lab_client.post('/medtest/upload/', data=data)

        # Expected: empty file rejected -> no record created.
        assert MedicalTest.objects.count() == 0

    def test_TC_F005_EP_02_valid_file_accepted(self, lab_client, doctor_account, patient_account, hospital):
        """TC_F005_EP_02: A valid-size report (850 KB) is accepted, with the
        success message and a stored MedicalTest record."""
        content = b'x' * (850 * 1024)  # 850 KB, within the valid partition
        valid = SimpleUploadedFile('report_scan.pdf', content, content_type='application/pdf')
        data = self._upload_payload(doctor_account, patient_account, hospital, image1=valid)

        response = lab_client.post('/medtest/upload/', data=data)

        assert b"Successfully uploaded medical test" in response.content
        assert MedicalTest.objects.count() == 1

    def test_TC_F005_EP_03_oversized_file_rejected(self, lab_client, doctor_account, patient_account, hospital):
        """TC_F005_EP_03: A report larger than 1 MB must be rejected and no
        MedicalTest record persisted. Documents the >1 MB validation
        requirement (SRS 2.5)."""
        content = b'x' * (2 * 1024 * 1024)  # 2 MB, above the 1 MB limit
        oversized = SimpleUploadedFile('large_scan.jpg', content, content_type='image/jpeg')
        data = self._upload_payload(doctor_account, patient_account, hospital, image1=oversized)

        lab_client.post('/medtest/upload/', data=data)

        # Expected: oversized file rejected -> no record created.
        assert MedicalTest.objects.count() == 0

    @staticmethod
    def _file(name, kb=1):
        """A report file of the given size in KiB."""
        return SimpleUploadedFile(name, b'x' * (kb * 1024), content_type='application/pdf')

    # ----- 2.2.6.2 Boundary Value Analysis — File Size (SRS 2.5) -----

    def test_TC_F005_BVA_01_zero_bytes_rejected(self, lab_client, doctor_account, patient_account, hospital):
        """TC_F005_BVA_01: 0 bytes (below min) must be rejected; no record.
        The framework rejects empty files, so this passes."""
        empty = SimpleUploadedFile('zero.pdf', b'', content_type='application/pdf')
        data = self._upload_payload(doctor_account, patient_account, hospital, image1=empty)
        lab_client.post('/medtest/upload/', data=data)
        assert MedicalTest.objects.count() == 0

    def test_TC_F005_BVA_02_1kb_accepted(self, lab_client, doctor_account, patient_account, hospital):
        """TC_F005_BVA_02: 1 KB (within range) is accepted and stored."""
        data = self._upload_payload(doctor_account, patient_account, hospital, image1=self._file('1kb.pdf', 1))
        response = lab_client.post('/medtest/upload/', data=data)
        assert b"Successfully uploaded medical test" in response.content
        assert MedicalTest.objects.count() == 1

    def test_TC_F005_BVA_03_1023kb_accepted(self, lab_client, doctor_account, patient_account, hospital):
        """TC_F005_BVA_03: 1023 KB (max - 1 KB) is accepted and stored."""
        data = self._upload_payload(doctor_account, patient_account, hospital, image1=self._file('1023kb.pdf', 1023))
        response = lab_client.post('/medtest/upload/', data=data)
        assert b"Successfully uploaded medical test" in response.content
        assert MedicalTest.objects.count() == 1

    def test_TC_F005_BVA_04_1024kb_accepted(self, lab_client, doctor_account, patient_account, hospital):
        """TC_F005_BVA_04: 1024 KB (exactly 1 MB, the max) is accepted and stored."""
        data = self._upload_payload(doctor_account, patient_account, hospital, image1=self._file('1024kb.pdf', 1024))
        response = lab_client.post('/medtest/upload/', data=data)
        assert b"Successfully uploaded medical test" in response.content
        assert MedicalTest.objects.count() == 1

    def test_TC_F005_BVA_05_1025kb_rejected(self, lab_client, doctor_account, patient_account, hospital):
        """TC_F005_BVA_05: 1025 KB (max + 1 KB) must be rejected; no record.
        The build enforces no size limit, so this is EXPECTED TO FAIL and
        documents the same >1 MB defect as EP_03 (do not weaken)."""
        data = self._upload_payload(doctor_account, patient_account, hospital, image1=self._file('1025kb.pdf', 1025))
        lab_client.post('/medtest/upload/', data=data)
        # Expected: just-over-limit file rejected -> no record created.
        assert MedicalTest.objects.count() == 0

    # ----- 2.2.6.4 Boundary Value Analysis — File Count (REQ_U1026.1) -----

    def test_TC_F005_BVA_06_zero_files_accepted(self, lab_client, doctor_account, patient_account, hospital):
        """TC_F005_BVA_06: 0 files (min) — attachments are optional, upload succeeds."""
        data = self._upload_payload(doctor_account, patient_account, hospital)
        response = lab_client.post('/medtest/upload/', data=data)
        assert b"Successfully uploaded medical test" in response.content
        assert MedicalTest.objects.count() == 1

    def test_TC_F005_BVA_07_one_file_accepted(self, lab_client, doctor_account, patient_account, hospital):
        """TC_F005_BVA_07: 1 file (min + 1) is accepted and stored."""
        data = self._upload_payload(doctor_account, patient_account, hospital, image1=self._file('a.pdf'))
        response = lab_client.post('/medtest/upload/', data=data)
        assert b"Successfully uploaded medical test" in response.content
        assert MedicalTest.objects.count() == 1
        assert bool(MedicalTest.objects.first().image1)

    def test_TC_F005_BVA_08_four_files_accepted(self, lab_client, doctor_account, patient_account, hospital):
        """TC_F005_BVA_08: 4 files (max - 1) are accepted and stored."""
        files = {'image{}'.format(i): self._file('f{}.pdf'.format(i)) for i in range(1, 5)}
        data = self._upload_payload(doctor_account, patient_account, hospital, **files)
        response = lab_client.post('/medtest/upload/', data=data)
        assert b"Successfully uploaded medical test" in response.content
        assert MedicalTest.objects.count() == 1

    def test_TC_F005_BVA_09_five_files_accepted(self, lab_client, doctor_account, patient_account, hospital):
        """TC_F005_BVA_09: 5 files (max) are accepted and stored."""
        files = {'image{}'.format(i): self._file('f{}.pdf'.format(i)) for i in range(1, 6)}
        data = self._upload_payload(doctor_account, patient_account, hospital, **files)
        response = lab_client.post('/medtest/upload/', data=data)
        assert b"Successfully uploaded medical test" in response.content
        assert MedicalTest.objects.count() == 1
        mt = MedicalTest.objects.first()
        assert all(bool(getattr(mt, 'image{}'.format(i))) for i in range(1, 6))

    def test_TC_F005_BVA_10_max_five_files_enforced(self, lab_client, doctor_account, patient_account, hospital):
        """TC_F005_BVA_10: 6 files (max + 1) — the form exposes only five file
        inputs (image1-image5), so a sixth cannot be attached/stored."""
        # The upload form structurally caps attachments at five.
        image_fields = [name for name in MedTestForm().fields if name.startswith('image')]
        assert len(image_fields) == 5
        assert 'image6' not in MedTestForm().fields

        # Behaviour: submit six files; only five are stored (the 6th is ignored).
        files = {'image{}'.format(i): self._file('f{}.pdf'.format(i)) for i in range(1, 7)}
        data = self._upload_payload(doctor_account, patient_account, hospital, **files)
        lab_client.post('/medtest/upload/', data=data)
        assert MedicalTest.objects.count() == 1
        mt = MedicalTest.objects.first()
        assert all(bool(getattr(mt, 'image{}'.format(i))) for i in range(1, 6))  # 5 stored
        assert not hasattr(mt, 'image6')  # no sixth slot exists

    # ----- 2.2.6.4 State Transition Testing (0-switch) — Completion Flag (UC-12) -----

    def test_TC_F005_STT_01_lab_marks_test_completed(self, lab_client, medical_test):
        """TC_F005_STT_01: Lab transitions a medical test's completion flag from
        False to True via /medtest/update/ (valid 0-switch transition).

        Verifies the success message and that completed=True is persisted.
        (Report-file storage is validated by the EP/BVA upload tests, since the
        update view processes only request.POST, not request.FILES.)
        """
        # Pre-condition: an assigned, not-yet-completed medical test.
        assert medical_test.completed is False

        payload = {
            'name': medical_test.name,
            'date': medical_test.date.strftime('%Y-%m-%d'),
            'hospital': medical_test.hospital.id,
            'description': medical_test.description,
            'doctor': medical_test.doctor.id,
            'patient': medical_test.patient.id,
            'private': 'on',       # keep the test private (unchanged)
            'completed': 'on',     # mark complete (the transition under test)
        }
        response = lab_client.post(
            '/medtest/update/?pk={}'.format(medical_test.pk), data=payload,
        )

        assert response.status_code == 200
        assert b"Medical test has been updated" in response.content

        # Core STT assertion: completion flag persisted as True.
        medical_test.refresh_from_db()
        assert medical_test.completed is True

    # ----- 2.2.6.5 Use Case Testing — Lab Workflow (UC-12) -----

    def test_TC_F005_UCT_02_oversized_upload_rejected(self, lab_client, doctor_account, patient_account, hospital):
        """TC_F005_UCT_02: Error flow — a >1 MB upload must be rejected and the
        database left unchanged. The build enforces no size limit, so this is
        EXPECTED TO FAIL and documents the same >1 MB defect (do not weaken)."""
        content = b'x' * (2 * 1024 * 1024)  # 2 MB
        oversized = SimpleUploadedFile('large_scan.jpg', content, content_type='image/jpeg')
        data = self._upload_payload(doctor_account, patient_account, hospital, image1=oversized)

        lab_client.post('/medtest/upload/', data=data)

        # Expected: oversized file rejected -> DB unchanged (no record).
        assert MedicalTest.objects.count() == 0

    def test_TC_F005_UCT_03_access_control_on_medtest_views(
        self, client, lab_account, chemist_account, medical_test
    ):
        """TC_F005_UCT_03: Security flow — role-based access control.

        - Unauthenticated request to /medtest/upload/ is redirected to login.
        - A Chemist (non-authorized role) is denied the upload endpoint
          (redirect to /error/denied/).
        - The Lab can reach /medtest/list/ and sees medical tests (current
          implemented behaviour; per-pincode scoping is not implemented).
        """
        # 1. Unauthenticated access to the upload endpoint -> login page.
        response = client.get('/medtest/upload/')
        assert response.status_code == 302
        assert response.url == '/'

        # 2. Chemist is not in [Doctor, Lab] -> denied.
        client.force_login(chemist_account.user)
        response = client.get('/medtest/upload/')
        assert response.status_code == 302
        assert response.url == '/error/denied/'
        client.logout()

        # 3. Lab can access the list and sees the medical test.
        client.force_login(lab_account.user)
        response = client.get('/medtest/list/')
        assert response.status_code == 200
        assert medical_test.name in response.content.decode()

    def test_TC_F005_UCT_04_cross_patient_report_access_denied(self, client, medical_test):
        """TC_F005_UCT_04: Security flow (NFR-04 need-to-know) — Patient B must
        NOT be able to view Patient A's report via /medtest/display/.

        `display_view` performs no ownership check, so Patient B can open any
        report by pk. This is EXPECTED TO FAIL and documents the cross-patient
        data-exposure defect (do not weaken)."""
        # `medical_test` belongs to patient_account (John Doe = Patient A).
        patient_a_test = medical_test

        # Seed Patient B (a different patient with no access to A's report).
        patient_b_user = DjangoUser.objects.create_user(
            username='patient_b5@test.com', email='patient_b5@test.com',
            password='Patient@123', first_name='Jane', last_name='Roe',
        )
        Account.objects.create(
            user=patient_b_user,
            profile=Profile.objects.create(firstname='Jane', lastname='Roe', phone='0123456701'),
            role=Account.ACCOUNT_PATIENT,
        )

        # Patient B directly requests Patient A's report by pk.
        client.force_login(patient_b_user)
        response = client.get('/medtest/display/?pk={}'.format(patient_a_test.pk))

        # Expected: access denied -> Patient A's report must NOT be shown to B.
        assert patient_a_test.name not in response.content.decode()
