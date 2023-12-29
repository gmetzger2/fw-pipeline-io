"""
file_downloader.py - Module for downloading and handling files using the Flywheel SDK.

This module provides a FileDownloader class that allows users to download files from the Flywheel platform
and perform additional operations, such as unzipping.

Example:
    from fw_pipeline_io.data_tools.file_downloader import FileDownloader
    from fw_pipeline_io.data_tools.search import Search
    from flywheel import Project

    # Initialize the Search and FileDownloader classes
    search_instance = Search()
    file_downloader_instance = FileDownloader()

    # Perform a search to get FileEntry objects
    tagged_files = search_instance.search_for_file_with_tag('tag1', your_container)

    # Download and unzip the files, get the destination folder
    downloaded_folder = file_downloader_instance.download_and_unzip_files(tagged_files)
    print(f"Files downloaded and unzipped to: {downloaded_folder}")

Classes:
    FileDownloader: A class for downloading and handling files from the Flywheel platform.

Functions:
    download_files(file_entries: List[FileEntry], destination_folder: str = None) -> str:
        Download files from Flywheel and store them in the specified destination folder.

    unzip_files(zip_file_path: str, destination_folder: str = None) -> str:
        Unzip a file to the specified destination folder.

    download_and_unzip_files(file_entries: List[FileEntry], destination_folder: str = None) -> str:
        Download and unzip files from Flywheel and store them in the specified destination folder.
"""

import os
import tempfile
import zipfile
from typing import List
from flywheel import FileEntry, Client


class FileDownloader:
    def __init__(self, fw_client: Client = None):
        """
        Initialize the FileDownloader instance.

        Args:
            fw_client (Client, optional): The Flywheel SDK Client instance. Defaults to None, which creates a new Client.
        """
        if fw_client is None:
            self.fw_client = Client()
        else:
            self.fw_client = fw_client

    def download_files(
        self, file_entries: List[FileEntry], destination_folder: str = None
    ) -> str:
        """
        Download files from Flywheel and store them in the specified destination folder.

        Args:
            file_entries (List[FileEntry]): List of Flywheel FileEntry objects to download.
            destination_folder (str, optional): The destination folder to store the downloaded files.
                Defaults to None, in which case a temporary folder is created.

        Returns:
            str: The path to the destination folder.
        """
        if not destination_folder:
            destination_folder = tempfile.mkdtemp(prefix="file_downloads_")

        for file_entry in file_entries:
            file_path = os.path.join(destination_folder, file_entry.name)
            self.fw_client.download_file(file_entry, file_path)

        return destination_folder

    def unzip_files(self, zip_file_path: str, destination_folder: str = None) -> str:
        """
        Unzip a file to the specified destination folder.

        Args:
            zip_file_path (str): The path to the zip file to be extracted.
            destination_folder (str, optional): The destination folder to extract the contents.
                Defaults to None, in which case the extraction is done in the same folder as the zip file.

        Returns:
            str: The path to the destination folder.
        """
        if not destination_folder:
            destination_folder = os.path.dirname(zip_file_path)

        with zipfile.ZipFile(zip_file_path, "r") as zip_ref:
            zip_ref.extractall(destination_folder)

        return destination_folder

    def download_and_unzip_files(
        self, file_entries: List[FileEntry], destination_folder: str = None
    ) -> str:
        """
        Download and unzip files from Flywheel and store them in the specified destination folder.

        Args:
            file_entries (List[FileEntry]): List of Flywheel FileEntry objects to download and unzip.
            destination_folder (str, optional): The destination folder to store the downloaded and unzipped files.
                Defaults to None, in which case a temporary folder is created.

        Returns:
            str: The path to the destination folder.
        """
        downloaded_folder = self.download_files(file_entries, destination_folder)
        for file_entry in file_entries:
            file_path = os.path.join(downloaded_folder, file_entry.name)
            if file_path.endswith(".zip"):
                self.unzip_files(file_path, downloaded_folder)

        return downloaded_folder
