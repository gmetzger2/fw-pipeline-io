import unittest
from unittest.mock import MagicMock, patch
import sys

from fw_pipeline_io.iohandling import parsing


class TestParsing(unittest.TestCase):
    def setUp(self):
        # mock a config_file_path
        self.config_file_path = "tests/test_data/config.yaml"
        self.tags_file_in_path = "tests/test_data/tags_file_in.yaml"

    def test_create_args_parser_in_algorithm(self):
        """
        Test that the create_args_parser and parser.parse_args() functions
        return the correct arguments when called in the algorithm.
        """
        parser = parsing.create_args_parser()
        args = [self.config_file_path, self.tags_file_in_path]

        args_main = parser.parse_args(args)  # simulate command line arguments

        # Assert that args_main has pre-set attributes set to the correct
        # values
        assert args_main.config_file_path == self.config_file_path
        assert args_main.tags_file_in_path == self.tags_file_in_path


if __name__ == "__main__":
    unittest.main()
