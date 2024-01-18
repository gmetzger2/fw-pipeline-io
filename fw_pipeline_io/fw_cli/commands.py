"""
Python functions for the Fllywheel CLI.
"""
import shutil
from pathlib import Path
import os
import logging
from uuid import uuid4

log = logging.getLogger(__name__)


class FWCLI:
    def __init__(self, fw_cli_path: str = None):
        """
        Initialize the FWCLI object.

        Parameters
        ----------
        fw_cli_path : str
            Path to the Flywheel CLI.
        """
        if fw_cli_path is None:
            fw_cli_path = shutil.which("fw")
            if fw_cli_path is None:
                raise ValueError(
                    "Could not find Flywheel CLI. Please install it or pass a "
                    "path to the CLI and try again."
                )
        else:
            if not Path(fw_cli_path).exists():
                raise ValueError(
                    "Could not find Flywheel CLI at the specified path. Please"
                    " install it or pass a path to the CLI and try again."
                )

        self.fw_cli_path = fw_cli_path

    def login(self, api_key: str = None):
        """
        Login to Flywheel using the CLI.

        Parameters
        ----------
        api_key : str
            Flywheel API key.
        """
        if api_key is None:
            raise ValueError("Please provide a Flywheel API key.")

        command = f"{self.fw_cli_path} login {api_key}"
        try:
            response = os.system(command)
        except Exception as e:
            raise ValueError(
                f"Could not log in to Flywheel. Please check your API key. "
                f"Error: {e}"
            )

        if response == 0:
            log.info("Successfully logged in to Flywheel.")
        else:
            log.warning("Response did not return 0, got response %s", response)

    def download(self, src: str, dest: str, params: str = None):
        """
        Download a file from Flywheel using the CLI.

        Parameters
        ----------
        project_path : str
            Source path on Flywheel.
        dest : str
            Destination path on local machine.
        params : str
            Additional parameters to pass to the CLI.
        """
        if src is None:
            raise ValueError("Please provide a source path on Flywheel.")
        if dest is None:
            raise ValueError("Please provide a destination path on your local machine.")

        # Change the directory to the destination folder
        cwd = os.getcwd()
        os.chdir(dest)

        command = f'{self.fw_cli_path} download "{src}"'
        if params is not None:
            command += f" {params}"

        try:
            response = os.system(command)
        except Exception as e:
            raise ValueError(
                f"Could not download file from Flywheel. Please check your "
                f"parameters. Error: {e}"
            )

        if response == 0:
            log.info("Successfully downloaded file(s) from Flywheel.")
        else:
            log.warning("Response did not return 0, got response %s", response)

        # Change back to the original directory
        os.chdir(cwd)

    def sync(self, project_path: str, dest: str, params: str = None):
        """
        Sync files from Flywheel using the CLI.

        Parameters
        ----------
        project_path : str
            Flywheel project path, e.g., "my_group/my_project".
        dest : str
            Destination path on local machine.
        params : str
            Additional parameters to pass to the CLI.
        """
        if project_path is None:
            raise ValueError("Please provide a Flywheel project path.")
        if dest is None:
            raise ValueError("Please provide a destination path on your local machine.")

        command = f'{self.fw_cli_path} sync "{project_path}" "{dest}"'
        if params is not None:
            command += f" {params}"

        try:
            response = os.system(command)
        except Exception as e:
            raise ValueError(f"Could not sync files from Flywheel. Error: {e}")

        if response == 0:
            log.info("Successfully synced file(s) from Flywheel.")
        else:
            log.warning("Response did not return 0, got response %s", response)
