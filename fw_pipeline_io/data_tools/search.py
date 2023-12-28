"""
This module is for searching and downloading data_tools that contain a certain tag
from a container.
"""
from typing import Union, List
from flywheel import Client, Project, Subject, Session, Acquisition, Analysis, FileEntry


class Search:
    """
    This class uses the Flywheel SDK to search for files that have a
    certain tag within a container.
    """
    def __init__(self, fw_client: Client = None):
        if fw_client is None:
            self.fw_client = Client()
        else:
            self.fw_client = fw_client

    def search_for_file_with_tag(
        self,
        tag: Union[str, List[str]],
        container: Union[Project, Subject, Session, Acquisition, Analysis],
        inclusive: bool = False,
        recursive: bool = False,
    ) -> List[FileEntry]:
        """
        Returns a list of files that have a certain tag or data_tools (if a list
        is passed).

        Args
        ----
        tag: Union[str, List[str]]
            The tag or list of data_tools to search for.
        container: Union[Project, Subject, Session, Acquisition, Analysis]
            Flywheel Container - Project, Subject, Session, Acquisition, or Analysis containers.
        inclusive: bool, optional
            If a list of data_tools is passed, this sets whether to only return
            files that include all data_tools in the file. If False, it returns
            all files that have any of the passed data_tools in the list. If True,
            it returns only files that have all the data_tools.
        recursive: bool, optional
            If True, look through all child containers for the files.

        Returns
        -------
        List[FileEntry]
            A list of Flywheel FileEntry objects representing the tagged files.
        """
        tagged_files = []

        # Iterate through files in the container
        for file_entry in container.files:
            # Check if the file has the specified tag(s)
            file_tags = file_entry.tags
            if isinstance(tag, list):
                # Check if all data_tools are present or any tag is present based on 'inclusive'
                if (inclusive and all(t in file_tags for t in tag)) or (not inclusive and any(t in file_tags for t in tag)):
                    tagged_files.append(file_entry)
            elif isinstance(tag, str) and tag in file_tags:
                tagged_files.append(file_entry)

        # If recursive is True, search through child containers using iterator methods
        if recursive:
            if isinstance(container, Project):
                for subject in container.subjects.iter():
                    tagged_files.extend(
                        self.search_for_file_with_tag(tag, subject, inclusive, recursive)
                    )
            elif isinstance(container, Subject):
                for session in container.sessions.iter():
                    tagged_files.extend(
                        self.search_for_file_with_tag(tag, session, inclusive, recursive)
                    )
            elif isinstance(container, Session):
                for acquisition in container.acquisitions.iter():
                    tagged_files.extend(
                        self.search_for_file_with_tag(tag, acquisition, inclusive, recursive)
                    )

        return tagged_files