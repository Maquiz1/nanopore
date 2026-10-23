"""Exports and uploaded source files are kept out of the public media folder."""
import os
import tempfile
from pathlib import Path
from unittest import mock

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse

from nanopore.test_access import AccessTestBase
from reports.tasks_export_models import export_model_raw_data_task
from utils import access


class PrivateFilesTests(AccessTestBase):
    def setUp(self):
        self.media = tempfile.mkdtemp()
        self.private = Path(tempfile.mkdtemp())
        self.settings_override = override_settings(
            MEDIA_ROOT=self.media, PRIVATE_ROOT=self.private,
            PRIVATE_EXPORTS_DIR=self.private / "exports", PRIVATE_IMPORTS_DIR=self.private / "imports",
        )
        self.settings_override.enable()
        self.admin = self.make_user("admin", [access.ADMIN])

    def tearDown(self):
        self.settings_override.disable()

    def files_under(self, root):
        return [p for p in Path(root).rglob("*") if p.is_file()]

    def test_model_export_is_written_to_private_folder_and_served_by_view(self):
        result = export_model_raw_data_task.apply(args=["Screening"], kwargs={"user_id": self.admin.pk}).get()
        self.assertTrue((self.private / "exports" / result["file"]).exists())
        self.assertEqual(self.files_under(self.media), [])
        self.client.force_login(self.admin)
        response = self.client.get(reverse("reports:serve_model_data", args=[result["file"]]))
        self.assertEqual(response.status_code, 200)

    def test_uploaded_tblis_file_is_stored_privately(self):
        superuser = self.make_user("root")
        superuser.is_superuser = True
        superuser.save()
        self.client.force_login(superuser)
        upload = SimpleUploadedFile("tblis.csv", b"labno,spectype,peripheralres_genexpert\n")
        with mock.patch("nanopore.views.laboratory.edcs_tblis.tblis_raw_upload_view.process_raw_tblis_upload") as task:
            task.delay.return_value.id = "task-1"
            self.client.post(reverse("nanopore:tblis-raw-upload"), {"file": upload})
            stored_path = task.delay.call_args[0][0]
        self.assertTrue(str(stored_path).startswith(str(self.private)))
        self.assertTrue(os.path.exists(stored_path))
        self.assertEqual(self.files_under(self.media), [])
