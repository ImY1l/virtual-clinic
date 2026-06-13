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
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone

from server.forms import MedTestForm
from server.models import MedicalTest


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
