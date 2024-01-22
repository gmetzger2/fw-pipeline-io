from fw_pipeline_io.fw_cli.commands import FWCLI
from unittest.mock import MagicMock, patch
import unittest


class TestFWCLI(unittest.TestCase):
    def test_init_no_path_cli_installed(self):
        """
        Test that the FWCLI class is initialized correctly when no path is passed and
        assume that the CLI is installed correctly.
        """
        with patch("shutil.which") as mock_shutil:
            mock_shutil.return_value = "/usr/local/bin/fw"
            self.fw_cli_instance = FWCLI()
            assert self.fw_cli_instance.fw_cli_path == "/usr/local/bin/fw"

    def test_init_no_path_cli_not_installed(self):
        """
        Test that the FWCLI class throws an error when it cannot find the CLI using
        shutil.which. No path to the CLI is passed.
        """
        with patch("shutil.which") as mock_shutil:
            mock_shutil.return_value = None
            with self.assertRaises(ValueError):
                self.fw_cli_instance = FWCLI()

    def test_init_with_path_exists(self):
        """
        Test that the FWCLI class is initialized correctly when a path is passed and
        assume that the CLI is installed correctly with the passed path.
        """
        with patch("pathlib.Path.exists") as mock_path:
            mock_path.return_value = True
            self.fw_cli_instance = FWCLI(fw_cli_path="/usr/local/bin/fw")
            assert self.fw_cli_instance.fw_cli_path == "/usr/local/bin/fw"

    def test_init_with_path_does_not_exist(self):
        """
        Test that the FWCLI class throws an error when the path passed does not exist.
        """
        with patch("pathlib.Path.exists") as mock_path:
            mock_path.return_value = False
            with self.assertRaises(ValueError):
                self.fw_cli_instance = FWCLI(fw_cli_path="/usr/local/bin/fw")

    def setUp(self):
        with patch("pathlib.Path.exists") as mock_path:
            mock_path.return_value = True
            self.fw_cli_instance = FWCLI(fw_cli_path="/usr/local/bin/fw")

    def test_login_no_api_key(self):
        """
        Test that an error is raised when no API key is passed or if it's a blank
        string.
        """
        with self.assertRaises(ValueError):
            self.fw_cli_instance.login(api_key=None)
        with self.assertRaises(ValueError):
            self.fw_cli_instance.login(api_key="")

    def test_login_with_api_key(self):
        """
        Test successful login to Flywheel using the CLI and a mock API key"
        """
        with patch("os.system") as mock_os:
            with patch("fw_pipeline_io.fw_cli.commands.log") as mock_log:
                mock_os.return_value = 0
                self.fw_cli_instance.login(api_key="1234")
                mock_os.assert_called_once_with("/usr/local/bin/fw login 1234")
                mock_log.info.assert_called_once_with(
                    "Successfully logged in to Flywheel."
                )

    def test_login_with_bad_api_key(self):
        """
        Test that an error is raised when the API key is invalid.
        """
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

    def test_check_if_attempting_to_pipe(self):
        """
        Test multiple ways of attempting to pipe commands to the CLI.
        """
        # Test if using `|`
        command = '/usr/local/bin/fw sync "my_group/my_project" "flywheel/v0/input"'
        params = "| /usr/local/bin/fw ingest -y -r "
        command += f" {params}"
        with self.assertRaises(ValueError):
            self.fw_cli_instance.check_if_attempting_to_pipe(command=command)

        # Test if using `&&`
        command = "fw sync && fw ingest"
        with self.assertRaises(ValueError):
            self.fw_cli_instance.check_if_attempting_to_pipe(command=command)

        # Test if using `;`
        command = "fw sync ; fw ingest"
        with self.assertRaises(ValueError):
            self.fw_cli_instance.check_if_attempting_to_pipe(command=command)

        # Test if using `||`
        command = "fw sync || fw ingest"
        with self.assertRaises(ValueError):
            self.fw_cli_instance.check_if_attempting_to_pipe(command=command)


if __name__ == "__main__":
    unittest.main()
