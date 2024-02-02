import unittest
from unittest.mock import MagicMock
from flywheel import Project, Subject, Session, Acquisition, Analysis, FileEntry, Client
from fw_pipeline_io.fwdatatools.search import Search


class TestSearch(unittest.TestCase):
    def setUp(self):
        ############################################################
        # Create mock Flywheel Containers for testing
        ############################################################

        # Create files with tags
        self.mock_file_entry1 = MagicMock(spec=FileEntry, tags=["tag1", "tag2"])
        self.mock_file_entry2 = MagicMock(spec=FileEntry, tags=["tag2", "tag3"])
        self.mock_file_entry3 = MagicMock(spec=FileEntry, tags=["tag1", "tag3"])

        # Mock an aquisition container with files
        self.mock_acquisition = MagicMock(
            spec=Acquisition,
            files=[self.mock_file_entry1, self.mock_file_entry2, self.mock_file_entry3],
        )

        # Mock a session container with files and an acquisition (including the
        # method iter)
        self.mock_session = MagicMock(
            spec=Session,
            files=[self.mock_file_entry1, self.mock_file_entry2, self.mock_file_entry3],
            acquisitions=MagicMock(
                iter=MagicMock(return_value=[self.mock_acquisition])
            ),
        )
        # Mock a subject container with files and a session
        self.mock_subject = MagicMock(
            spec=Subject,
            files=[self.mock_file_entry1, self.mock_file_entry2, self.mock_file_entry3],
            sessions=MagicMock(iter=MagicMock(return_value=[self.mock_session])),
        )
        # Mock a project container with files and a subject
        self.mock_project = MagicMock(
            spec=Project,
            files=[self.mock_file_entry1, self.mock_file_entry2, self.mock_file_entry3],
            subjects=MagicMock(iter=MagicMock(return_value=[self.mock_subject])),
        )

        # Create an instance of the Search class
        fw_client = MagicMock(spec=Client)
        self.search_instance = Search(fw_client=fw_client)

    def test_search_for_file_with_single_tag(self):
        result = self.search_instance.search_for_file_with_tag(
            "tag1", self.mock_project
        )
        self.assertEqual(result, [self.mock_file_entry1, self.mock_file_entry3])

    def test_search_for_file_with_list_of_tags_inclusive(self):
        result = self.search_instance.search_for_file_with_tag(
            tag=["tag1", "tag2"],
            container=self.mock_project,
            inclusive=True,
            recursive=False,
        )
        self.assertEqual(result, [self.mock_file_entry1])

    def test_search_for_file_with_list_of_tags_not_inclusive(self):
        result = self.search_instance.search_for_file_with_tag(
            tag=["tag1", "tag2"],
            container=self.mock_project,
            inclusive=False,
            recursive=False,
        )
        self.assertEqual(
            result,
            [self.mock_file_entry1, self.mock_file_entry2, self.mock_file_entry3],
        )

    def test_search_for_file_recursive(self):
        # Test with recursive search
        result = self.search_instance.search_for_file_with_tag(
            "tag1", self.mock_project, recursive=True
        )
        # Since we're traversing every container from the project level, then we can
        # expect that each file with `tag1` will be returned twice (once for each
        # container)
        self.assertEqual(result, [self.mock_file_entry1, self.mock_file_entry3] * 4)


if __name__ == "__main__":
    unittest.main()
