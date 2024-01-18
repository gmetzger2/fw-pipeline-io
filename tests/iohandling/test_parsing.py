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
        parser = parsing.create_args_parser()
        args = [self.config_file_path, self.tags_file_in_path]

        args_main = parser.parse_args(args)
        assert args_main.config_file_path == self.config_file_path
        assert args_main.tags_file_in_path == self.tags_file_in_path


"""
   # with patch(
        "argparse.ArgumentParser.parse_args") as mock_parse_args:
        mock_parse_args.assert_called_once_with()
        assert args_main.config_file_path == self.config_file_path
        assert args_main.tags_file_in_path == self.tags_file_in_path
"""


if __name__ == "__main__":
    unittest.main()
