"""Exercise the scheduled wrapper without credentials, networking, or real saves."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


@unittest.skipUnless(os.name == 'nt', 'Windows Task Scheduler wrapper')
class BackgroundDeliveryTests(unittest.TestCase):
    def run_wrapper(self, sender):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'bridge').mkdir()
            (root / 'local_data').mkdir()
            wrapper = root / 'bridge/send_hosted_background.ps1'
            shutil.copyfile(Path(__file__).with_name(wrapper.name), wrapper)
            (root / 'bridge/send_hosted.ps1').write_text(sender, encoding='utf-8')
            result = subprocess.run(['powershell.exe', '-NoProfile', '-NonInteractive',
                                     '-File', str(wrapper)], capture_output=True, timeout=20)
            status = json.loads((root / 'local_data/hosted-delivery-status.json').read_text(
                encoding='utf-8-sig'))
            return result.returncode, status

    def test_success_records_delivery_result(self):
        code, status = self.run_wrapper("Write-Output 'Delivered observations: 2'")
        self.assertEqual(code, 0)
        self.assertTrue(status['success'])
        self.assertEqual(status['message'], 'Delivered observations: 2')

    def test_failure_records_status_and_nonzero_exit(self):
        code, status = self.run_wrapper("throw 'Connection failed; events remain pending'")
        self.assertEqual(code, 1)
        self.assertFalse(status['success'])
        self.assertIn('events remain pending', status['message'])
