import unittest
import os
import shutil
from unittest.mock import MagicMock, patch, mock_open
from fw_pipeline_io.data_tools.file_downloader import FileDownloader
from flywheel import FileEntry

class TestFileDownloader(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for testing
        self.temp_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'temp_test_dir')
        os.makedirs(self.temp_dir, exist_ok=True)

        # Create a mock Flywheel Client
        self.mock_fw_client = MagicMock()

        # Create an instance of the FileDownloader class with the mock client
        self.file_downloader = FileDownloader(self.mock_fw_client)

    def tearDown(self):
        # Remove the temporary directory after the tests
        shutil.rmtree(self.temp_dir)

    @patch('zipfile.ZipFile')
    def test_unzip_files(self, mock_zipfile):
        # Create a test zip file
        test_zip_file = os.path.join(self.temp_dir, 'test_file.zip')
        with open(test_zip_file, 'w') as f:
            f.write("Test content")

        result = self.file_downloader.unzip_files(test_zip_file, self.temp_dir)

        # Verify that the ZipFile constructor was called with the correct arguments
        mock_zipfile.assert_called_once_with(test_zip_file, 'r')

        # Verify that the method returned the correct destination folder
        self.assertEqual(result, self.temp_dir)

    @patch('tempfile.mkdtemp')
    def test_download_files(self, mock_mkdtemp):
        mock_mkdtemp.return_value = self.temp_dir

        # Create a test FileEntry list with a zip file
        mock_file_entry1 = MagicMock(spec=FileEntry)
        mock_file_entry1.name = 'test_file.zip'
        file_entries = [mock_file_entry1]

        result = self.file_downloader.download_files(file_entries=file_entries)

        # Verify that the method returned the correct destination folder
        self.assertEqual(result, self.temp_dir)

        # Verify that mkdtemp() was called
        mock_mkdtemp.assert_called_once_with(prefix="file_downloads_")

        # Verify that the download_file method was called with the correct arguments
        self.mock_fw_client.download_file.assert_called_once_with(mock_file_entry1, os.path.join(self.temp_dir, 'test_file.zip'))


if __name__ == '__main__':
    unittest.main()
