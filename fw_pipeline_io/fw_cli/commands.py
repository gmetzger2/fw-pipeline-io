"""
Python functions for the Flywheel CLI.
"""
import shutil
from pathlib import Path
import os
import logging
from uuid import uuid4

log = logging.getLogger(__name__)


class FWCLI:
    cli_missing_msg = (
        "If this is a Docker image/Flywheel gear, ensure that the "
        "Dockerfile copies the executable as follows:\n"
        "\tCOPY ./fw '/usr/local/bin/'\n"
        "Please also check that the .dockerignore file does not exclude"
        "`fw` from being copied into the Docker image."
    )

    def check_if_attempting_to_pipe(self, command: str):
        """
        Check if the string that the user passes contains any piping characters, like
        `|`, `;`, `&&`, etc. If so, raise an error.
        """
        if "|" in command or ";" in command or "&" in command:
            raise ValueError(
                "You are attempting to pipe commands. This is not allowed."
            )

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
                    "path to the CLI and try again.\n"
                    "%s" % self.cli_missing_msg
                )
        else:
            if not Path(fw_cli_path).exists():
                raise ValueError(
                    "Could not find Flywheel CLI at the specified path. Please"
                    " install it or pass a path to the CLI and try again.\n"
                    "%s" % self.cli_missing_msg
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
        if not api_key:
            raise ValueError("Please provide a Flywheel API key.")

        command = f"{self.fw_cli_path} login {api_key}"
        self.check_if_attempting_to_pipe(command=command)
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
        src : str
            Source path on Flywheel. Example path for a file:
                "my_group/my_project/my_subject/my_session/my_acq/my_file_name.zip"
        dest : str
            Destination path on local machine, e.g., "/Users/jesusavila/Downloads"
        params : str
            Additional parameters to pass to the CLI. `fw download -h` for
            available parameters.
        """
        if not src:
            raise ValueError("Please provide a source path on Flywheel.")
        if not dest:
            raise ValueError("Please provide a destination path on your local machine.")

        # Change the directory to the destination folder
        cwd = os.getcwd()
        os.chdir(dest)

        command = f'{self.fw_cli_path} download "{src}"'
        if params is not None:
            command += f" {params}"

        self.check_if_attempting_to_pipe(command=command)
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
            Destination path on local machine, e.g., "/Users/jesusavila/Downloads"
        params : str
            Additional parameters to pass to the CLI. Reference `fw sync -h` for
            available parameters.
        """
        if not project_path:
            raise ValueError("Please provide a Flywheel project path.")
        if not dest:
            raise ValueError("Please provide a destination path on your local machine.")

        command = f'{self.fw_cli_path} sync "{project_path}" "{dest}"'
        if params is not None:
            command += f" {params}"

        self.check_if_attempting_to_pipe(command=command)
        try:
            response = os.system(command)
        except Exception as e:
            raise ValueError(f"Could not sync files from Flywheel. Error: {e}")

        if response == 0:
            log.info("Successfully synced file(s) from Flywheel.")
        else:
            log.warning("Response did not return 0, got response %s", response)
