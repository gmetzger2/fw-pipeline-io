from fw_pipeline_io.fw_cli.commands import FWCLI
from unittest.mock import MagicMock, patch
import unittest


class TestFWCLI(unittest.TestCase):
    def test_init_no_path_cli_installed(self):
        with patch("shutil.which") as mock_shutil:
            mock_shutil.return_value = "/usr/local/bin/fw"
            self.fw_cli_instance = FWCLI()
            assert self.fw_cli_instance.fw_cli_path == "/usr/local/bin/fw"

    def test_init_no_path_cli_not_installed(self):
        with patch("shutil.which") as mock_shutil:
            mock_shutil.return_value = None
            with self.assertRaises(ValueError):
                self.fw_cli_instance = FWCLI()

    def test_init_with_path_exists(self):
        with patch("pathlib.Path.exists") as mock_path:
            mock_path.return_value = True
            self.fw_cli_instance = FWCLI(fw_cli_path="/usr/local/bin/fw")
            assert self.fw_cli_instance.fw_cli_path == "/usr/local/bin/fw"

    def test_init_with_path_does_not_exist(self):
        with patch("pathlib.Path.exists") as mock_path:
            mock_path.return_value = False
            with self.assertRaises(ValueError):
                self.fw_cli_instance = FWCLI(fw_cli_path="/usr/local/bin/fw")

    def setUp(self):
        with patch("pathlib.Path.exists") as mock_path:
            mock_path.return_value = True
            self.fw_cli_instance = FWCLI(fw_cli_path="/usr/local/bin/fw")

    def test_login_no_api_key(self):
        with self.assertRaises(ValueError):
            self.fw_cli_instance.login(api_key=None)

    def test_login_with_api_key(self):
        with patch("os.system") as mock_os:
            with patch("fw_pipeline_io.fw_cli.commands.log") as mock_log:
                mock_os.return_value = 0
                self.fw_cli_instance.login(api_key="1234")
                mock_os.assert_called_once_with("/usr/local/bin/fw login 1234")
                mock_log.info.assert_called_once_with(
                    "Successfully logged in to Flywheel."
                )

    def test_login_with_bad_api_key(self):
        with patch("os.system") as mock_os:
            mock_os.side_effect = Exception("Bad API key")
            with self.assertRaises(ValueError):
                self.fw_cli_instance.login(api_key="1234")

    def test_sync_pass(self):
        project_path = "mock_group/mock_project"
        dest = "flywheel/v0/input"
        params = '--include "nifti" --include-container-tags \'{"session": ["sync"], "file": ["T2_tse"]}\' --metadata'
        with patch("os.system") as mock_os:
            with patch("fw_pipeline_io.fw_cli.commands.log") as mock_log:
                mock_os.return_value = 0
                self.fw_cli_instance.sync(
                    project_path=project_path,
                    dest=dest,
                    params=params,
                )
                mock_os.assert_called_once_with(
                    '%s sync "%s" "%s" %s'
                    % (
                        self.fw_cli_instance.fw_cli_path,
                        project_path,
                        dest,
                        params,
                    )
                )
                mock_log.info.assert_called_once_with(
                    "Successfully synced file(s) from Flywheel."
                )

    def test_sync_fail(self):
        project_path = "mock_group/mock_project"
        dest = "flywheel/v0/input"
        params = '--include "nifti" --include-container-tags \'{"session": ["sync"], "file": ["T2_tse"]}\' --metadata'
        with patch("os.system") as mock_os:
            mock_os.side_effect = Exception("Test exception")
            with self.assertRaises(ValueError):
                self.fw_cli_instance.sync(
                    project_path=project_path,
                    dest=dest,
                    params=params,
                )

    def test_sync_warning(self):
        project_path = "mock_group/mock_project"
        dest = "flywheel/v0/input"
        params = '--include "nifti" --include-container-tags \'{"session": ["sync"], "file": ["T2_tse"]}\' --metadata'
        with patch("os.system") as mock_os:
            with patch("fw_pipeline_io.fw_cli.commands.log") as mock_log:
                mock_os.return_value = 1
                self.fw_cli_instance.sync(
                    project_path=project_path,
                    dest=dest,
                    params=params,
                )
                mock_os.assert_called_once_with(
                    '%s sync "%s" "%s" %s'
                    % (
                        self.fw_cli_instance.fw_cli_path,
                        project_path,
                        dest,
                        params,
                    )
                )
                mock_log.warning.assert_called_once_with(
                    "Response did not return 0, got response %s", 1
                )

    def test_sync_no_project_path(self):
        with self.assertRaises(ValueError):
            self.fw_cli_instance.sync(
                project_path="",
                dest="flywheel/v0/input",
                params='--include "nifti" --include-container-tags \'{"session": ["sync"], "file": ["T2_tse"]}\' --metadata',
            )

    def test_sync_no_dest(self):
        with self.assertRaises(ValueError):
            self.fw_cli_instance.sync(
                project_path="mock_group/mock_project",
                dest="",
                params='--include "nifti" --include-container-tags \'{"session": ["sync"], "file": ["T2_tse"]}\' --metadata',
            )

    def test_sync_no_params(self):
        project_path = "mock_group/mock_project"
        dest = "flywheel/v0/input"
        with patch("os.system") as mock_os:
            with patch("fw_pipeline_io.fw_cli.commands.log") as mock_log:
                mock_os.return_value = 0
                self.fw_cli_instance.sync(
                    project_path=project_path,
                    dest=dest,
                    params=None,
                )
                mock_os.assert_called_once_with(
                    '%s sync "%s" "%s"'
                    % (
                        self.fw_cli_instance.fw_cli_path,
                        project_path,
                        dest,
                    )
                )
                mock_log.info.assert_called_once_with(
                    "Successfully synced file(s) from Flywheel."
                )


if __name__ == "__main__":
    unittest.main()
