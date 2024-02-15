from typing import Type

from abc import ABC, abstractmethod
import logging
from pydantic import BaseModel
from flywheel.models import FileEntry
from typing import Union
import flywheel
import os
from uuid import uuid4
import pandas as pd

from fw_pipeline_io.fwdatatools.search import Search
from fw_pipeline_io.iohandling.yamlfiles import TagsFileManager
from flywheel_gear_toolkit import GearToolkitContext
from fw_pipeline_io.fwcli.commands import FWCLI
from fw_pipeline_io.fwdatatools.file_downloader import PrepareSync
from fw_pipeline_io.iohandling.yamlfiles import YamlFile


log = logging.getLogger(__name__)


def get_project_from_dest_container(
    gear_context: GearToolkitContext,
) -> (flywheel.Project, str):
    """
    Get the Flywheel project container object from the destination container.

    Params
    ------
    gear_context: GearToolkitContext
        The gear context object.

    Returns
    -------
    project: Project
        The Flywheel project container object.
    project_id: str
        The Flywheel project id.
    """
    # Get the destination container
    dest_container = gear_context.get_destination_container()
    log.debug(
        "dest_container id: %s, label: %s, type: %s"
        % (dest_container.id, dest_container.label, dest_container.container_type)
    )

    # Get the project from the destination container
    project_id = dest_container.parents["project"]
    project = gear_context.client.get_project(project_id)
    log.debug(
        "project id: %s, label: %s, group: %s"
        % (project.id, project.label, project.group)
    )
    return project, project_id


class AlgoInputs(BaseModel):
    """
    This model contains all the inputs and options that are needed to run
    the algorithm.
    """

    # Path to algorithm's config.yaml path, which is an input to the gear
    config_file_path: str
    # Path to tags_file_in.yaml path, which should be created by the gear using
    # fw-pipeline-io
    tags_file_in_path: str


class GearConfigYaml:
    """
    A class for getting and verifying the gear's config.yaml file.

    This class provides a method for getting the config.yaml file from the gear's input
    directory, and a method for verifying that the config.yaml file has the correct
    parameters.
    """

    def __init__(
        self, gear_context: GearToolkitContext, config_file_model: Type[BaseModel]
    ):
        self.gear_context = gear_context
        self.config_file_model = config_file_model

    def get_config_yaml_path(self):
        """
        Get the config.yaml file from the gear's input directory. If it's not in the
        gear's input directory, look for it in the Flywheel project and download it to
        the gear's work directory. Raise an error if it can't find it.

        The gear context object should have the following attributes:
            gear_context.input.get("config_yaml"): The config.yaml file from the gear's
                input directory.
            gear_context.config.get("config_yaml_name"): The name of the config.yaml file
                in the Flywheel project.

        Returns
        -------
        config_yaml_path: str
        """
        config_yaml_path = self.gear_context.get_input_path("config_yaml")

        # Verify that it actually got an input config.yaml file. If not, look for it using
        # the Flywheel SDK and download it to the gear's work directory. If it's not found,
        # raise an error.
        if not config_yaml_path:
            log.warning(
                "No config.yaml file was found in the gear's input directory. Looking for "
                "it in the Flywheel project."
            )
            # Get the default name of the config_yaml file from the gear's config.json file
            config_yaml_name = self.gear_context.config.get("config_yaml_name")

            # Raise an error if the config_yaml_name is not in the gear's config.json file
            if not config_yaml_name:
                raise ValueError(
                    "The 'config_yaml_name' key was not found in the gear's config.json file."
                )
            # Search the Flywheel project for the config.yaml file
            project, project_id = get_project_from_dest_container(
                gear_context=self.gear_context
            )
            for file_ in project.files:
                if file_.name == config_yaml_name:
                    # Download the file to the gear's work directory
                    config_yaml_path = os.path.join(
                        self.gear_context.work_dir, config_yaml_name
                    )
                    file_.download(config_yaml_path)
                    log.warning(
                        "The config.yaml file was found in the Flywheel project and has been "
                        "downloaded to the gear's work directory as the following:\n\t%s"
                        % config_yaml_path
                    )
                    break
            if not config_yaml_path:
                raise ValueError(
                    "The config.yaml file '%s' was not found in the Flywheel project '%s'."
                    % (config_yaml_name, project.label)
                )
        return config_yaml_path

    def verify_config_yaml_file(self, config_file_path: Union[str, os.PathLike]):
        """
        Ensure that the algorithm's input config.yaml file is set to the gear's work
        directory and the gear's output directories. If not, change these and save it to
        the gear's work directory.
        """
        # Separate the config file name from the path
        config_file_dir, config_file_filename = os.path.splitdrive(config_file_path)

        # Load the config.yaml file
        algo_config_file = YamlFile.load_yaml_settings(
            yaml_path=config_file_path, class_type=self.config_file_model
        )

        change_path = False

        # Get the gear's work and output directories. Convert from PathLike to string
        gear_work_dir = str(self.gear_context.work_dir)
        gear_output_dir = str(self.gear_context.output_dir)

        # Get the algorithm's input and output directories
        algo_input_folder = algo_config_file.input_folder
        algo_output_folder = algo_config_file.output_folder

        # Check if the algorithm's input and output directories are set to the gear's work
        # and output directories. Input should be the same as gear's working directory b/c
        # that's where the files will be synced locally. Don't mess w/ the gear's
        # input directory.
        if algo_input_folder != gear_work_dir:
            algo_config_file.input_folder = gear_work_dir
            change_path = True
            log.warning(
                "Changed config.yaml input_folder from '%s' to input_folder to '%s'"
                % (algo_input_folder, gear_work_dir)
            )
        if algo_output_folder != gear_output_dir:
            algo_config_file.output_folder = gear_output_dir
            change_path = True
            log.warning(
                "Changed config.yaml output_folder from '%s' to output_folder to '%s'"
                % (algo_output_folder, gear_output_dir)
            )
        log.debug("algo_config_file: %s" % algo_config_file)

        if change_path:
            log.warning(
                "The input_folder and/or output_folder in the algorithm's config.yaml file "
                "were not set to the gear's work directory and/or the gear's output "
                "directories. These have been changed and saved to the gear's work "
                "directory."
            )
            config_file_path = os.path.join(
                self.gear_context.work_dir, config_file_filename
            )
            YamlFile.save_yaml_file(
                base_model=algo_config_file,
                yaml_dir_path=self.gear_context.work_dir,
                yaml_file_name=config_file_filename,
            )

        return config_file_path

    def get_and_verify_config_yaml(self):
        """
        Get the config.yaml file and verify that it has the correct parameters.

        Args
        ----
        config_file_model: Type[BaseModel]
            The pydantic model that represents the config.yaml file.

        Returns
        -------
        config_yaml_path: str
            The path to the config.yaml file.
        """
        config_yaml_path = self.get_config_yaml_path()

        # Verify that the algorithm's input config.yaml file is set to the
        # gear's work directory and the gear's output directories.
        # Save it to the gear's work directory.
        config_yaml_path = self.verify_config_yaml_file(
            config_file_path=config_yaml_path
        )

        return config_yaml_path


class SyncInterface(ABC):
    @property
    @abstractmethod
    def sync_params_prefix(self):
        """
        The prefix parameters to be used when syncing files.
        """
        raise NotImplementedError

    @abstractmethod
    def sync_main_function(self) -> Union[os.PathLike, str]:
        """
        This is the main sync function that should be called by the GearInterface.

        Returns
        -------
        tags_file_in_path: Union[os.PathLike, str]
        """
        raise NotImplementedError

    @abstractmethod
    def sync_file(
        self,
        fw_cli: FWCLI,
        file_entry: FileEntry,
        project_path: str,
        dest: Union[os.PathLike, str],
        params: str,
    ):
        """
        This should call the create_sync_suffix_params_for_file method with the
        appropriate arguments.
        """
        raise NotImplementedError

    @abstractmethod
    def create_sync_suffix_params_for_file(
        self,
        file_entry: FileEntry,
        params: str,
    ) -> str:
        """
        This returns the suffix params for the file to be synced.

        This method gets called by the sync_file method.
        """
        raise NotImplementedError

    def sync_files(
        self,
        gear_context: GearToolkitContext,
        fw_tagged_files: dict,
        sync_params_prefix: str = '--include "nifti" --include "source code" --no-audit-log',
    ) -> tuple[dict, Union[os.PathLike, str]]:
        # Instantiate and login to the Flywheel CLI
        fw_cli = FWCLI()
        api_key = gear_context.get_input("api-key").get("key")
        fw_cli.login(api_key=api_key)

        # Sync the files to the gear's input directory
        # Right now, we're assuming we're tagging the dicom files, so we want to sync the
        # parent directory of the dicom files with only the nifties and .json files. For
        # now, assume only one dicom files per acquisition, but later optimize

        # Create the Flywheel project path (group/project) from which to sync the files
        fw_project, fw_project_id = get_project_from_dest_container(
            gear_context=gear_context
        )
        project_path = fw_project.group + "/" + fw_project.label
        log.debug("project_path: %s" % project_path)

        # Sync files
        synced_files = {}
        for field, file_entry in fw_tagged_files.items():
            if isinstance(file_entry, list):
                paths_synced_files = []
                for f in file_entry:
                    paths_synced_files.extend(
                        self.sync_file(
                            fw_cli=fw_cli,
                            file_entry=f,
                            project_path=project_path,
                            dest=gear_context.work_dir,
                            params=sync_params_prefix,
                        )
                    )
            else:
                paths_synced_files = self.sync_file(
                    fw_cli=fw_cli,
                    file_entry=file_entry,
                    project_path=project_path,
                    dest=gear_context.work_dir,
                    params=sync_params_prefix,
                )
            synced_files[field] = paths_synced_files

        return synced_files, gear_context.work_dir


class DefaultSyncInterface(SyncInterface):
    sync_params_prefix: str = (
        '--include "nifti" --include "source code" --no-audit-log',
    )

    def __init__(
        self,
        gear_context: GearToolkitContext,
        tags_file_in_model: Type[BaseModel],
    ):
        self.gear_context = gear_context
        self.tags_file_in_model = tags_file_in_model

    def prepare_and_sync_files(self) -> tuple[dict, Union[os.PathLike, str]]:
        """
        Call several methods to sync prepare and sync the files to the gear.
        """
        # Get the tagged files from the input container
        fields_and_types, fw_tagged_files = self.get_input_files()
        self.log_tagged_files(
            log_string="Found '%s' fw_tagged_files: %s", fw_tagged_files=fw_tagged_files
        )

        # Filter the tagged files
        fw_tagged_files = self.filter_tagged_files(fw_tagged_files)
        self.log_tagged_files(
            log_string="Got '%s' files after filtering: %s",
            fw_tagged_files=fw_tagged_files,
        )

        # Use the FW CLI to sync the files to the gear's input directory
        synced_files, dest = self.sync_files(
            gear_context=self.gear_context,
            fw_tagged_files=fw_tagged_files,
            sync_params_prefix=self.sync_params_prefix,
        )
        log.debug("synced_files:\n%s" % synced_files)

        return synced_files, dest

    def sync_main_function(self) -> Union[os.PathLike, str]:
        """
        This is the main sync function that should be called by the GearInterface.
        """
        # Prepare and sync the files locally
        synced_files, dest = self.prepare_and_sync_files()

        # Get only nifti files from the synced files. Need to fix later to handle single
        # strings. This only works for lists at the moment.
        synced_files = self.filter_nifti_files(synced_files=synced_files)
        log.debug("synced_files after filtering only niftis: \n%s" % synced_files)

        # Create the tags_file_in.yaml file
        tags_file_in_path = self.create_tags_file_in_file(
            synced_files=synced_files, dest=dest
        )
        log.debug("tags_file_in_path: %s" % tags_file_in_path)

        return tags_file_in_path

    def get_input_files(self):
        """
        Use the Flywheel SDK to look for tagged files in the input container.

        Uses the algorithms tags_file_in_model to determine which tags to search for in the
        input files. The files are then stored in a dictionary with the field names as keys
        and the corresponding FileEntry or list of FileEntry as values. The field names and
        types are also returned as a list of tuples.

        Args
        ----
        gear_context (GearToolkitContext): The gear context object.
        tags_file_in_model (Type[BaseModel]): A concrete class of pydantic.BaseModel that
            represents the input tags file. This is the uninstantiated class.


        Returns
        -------
        fields_and_types (List[Tuple[str, type]]): A list of tuples containing the
            field names and types of the model.
        fw_tagged_files (Dict[str, Union[FileEntry, List[FileEntry]]]): A dictionary
            containing the field names and the corresponding FileEntry or list of
            FileEntry.
        """
        # Use the TagsFileIn model to get what tags to search for in the input files
        fields_and_types = TagsFileManager.get_model_fields_and_types(
            tags_file=self.tags_file_in_model
        )

        # Get the container that's the input to the gear. This should be the destination
        # container's parent, since it's an analysis
        input_container = self.gear_context.get_destination_parent()
        log.debug(
            "input_container id: %s, label: %s, type: %s"
            % (
                input_container.id,
                input_container.label,
                input_container.container_type,
            )
        )

        # Instantiate a flywheel tag Search object
        fw_search = Search(fw_client=self.gear_context.client)

        # Loop through the fields and types to determine which files to sync
        fw_tagged_files = {}
        for field, field_type in fields_and_types:
            # Search for the tag in the input container
            file_entries = fw_search.search_for_file_with_tag(
                tag=field, container=input_container, inclusive=False, recursive=True
            )
            log.debug(
                "file_entries ids: %s, names: %s"
                % ([f.id for f in file_entries], [f.name for f in file_entries])
            )

            # Check the correct number of files were found for each field, and store in a
            # dictionary fw_tagged_files
            if field_type == str:
                # Verify that only one file was found
                if len(file_entries) > 1:
                    raise ValueError(
                        "More than one file found for tag '%s', found the following files:\n"
                        "\t%s" % (field, [f.name for f in file_entries])
                    )
                elif len(file_entries) == 0:
                    raise ValueError("No file found for tag '%s'." % field)
                else:
                    # Add the file to the fw_tagged_files
                    fw_tagged_files[field] = file_entries[0]

            elif field_type == list:
                # Raise error if no files were found
                if len(file_entries) == 0:
                    raise ValueError("No file found for tag '%s'." % field)
                else:
                    # Add the files to fw_tagged_files
                    fw_tagged_files[field] = file_entries
                pass
            else:
                raise ValueError(
                    "The type of a field must be str or typing.List[str]."
                    " The type of field '%s' was %s." % (field, field_type)
                )
        return fields_and_types, fw_tagged_files

    def log_tagged_files(self, log_string: str, fw_tagged_files: dict):
        """
        Log the number of files found for each tag and the names of the files.

        The log string should contain two %s, the first for the total number of files and
        the second for the names of the files.

        Args
        ----
        log_string (str): The log string to log the number of files and the names of the
            files.
        fw_tagged_files (dict): A dictionary containing the field names and the
            corresponding FileEntry or list of FileEntry.
        """

        tagged_file_names = self.get_file_names_from_tagged_files(fw_tagged_files)
        num_files_dict, total_num_files = self.get_num_files_from_tagged_files(
            fw_tagged_files
        )
        log.info(log_string % (total_num_files, tagged_file_names))
        log.info("Number of files per tag: %s" % num_files_dict)

    @staticmethod
    def get_file_names_from_tagged_files(fw_tagged_files: dict):
        """
        Get the names of the files from the tagged FileEntry files.

        Args
        ----
        fw_tagged_files (dict): A dictionary containing the field names and the
            corresponding FileEntry or list of FileEntry.

        Returns
        -------
        file_names_dict (dict): A dictionary containing the tag names and the corresponding
            file names.
        """
        file_names_dict = {
            key: [
                entry.name if isinstance(entry, FileEntry) else entry.name
                for entry in value
            ]
            if isinstance(value, list)
            else value.name
            for key, value in fw_tagged_files.items()
        }
        return file_names_dict

    @staticmethod
    def get_num_files_from_tagged_files(fw_tagged_files: dict):
        """
        Get the number of files from the dictionary of file names.

        Args
        ----
        file_names_dict (dict): A dictionary containing the tag names and the
            corresponding file names.

        Returns
        -------
        num_files_dict (dict): A dictionary containing the tag names and the number of
            corresponding files.
        total_num_files (int): The total number of files.
        """
        num_files_dict = {
            key: len(value) if isinstance(value, list) else 1
            for key, value in fw_tagged_files.items()
        }
        total_num_files = sum(num_files_dict.values())
        return num_files_dict, total_num_files

    def filter_tagged_files(self, fw_tagged_files: dict):
        """
        Ensure that only dicoms are the returned in the tagged files. This is so that
        nifti's that have been tagged aren't duplicated in the input directory, since
        we sync using the acquisition and not the files.

        Replace this method in the gear if you want to filter for a different type
        of file or files.
        """
        fw_tagged_files = self._filter_tagged_files(
            filter_type="dicom", fw_tagged_files=fw_tagged_files
        )
        return fw_tagged_files

    @staticmethod
    def _filter_tagged_files(filter_type: Union[str, list], fw_tagged_files: dict):
        """
        Ensure that only a certain type of file or files are returned in the tagged
        files.

        Args
        ----
        filter_type (Union[str, list]): The type of file or files to filter for.
        fw_tagged_files (dict): A dictionary containing the field names and the
            corresponding FileEntry or list of FileEntry.

        Returns
        -------
        fw_tagged_files_filtered (dict): A dictionary containing the field names and
            the corresponding FileEntry or list of FileEntry.
        """
        log.info("Filtering tagged files for the following type(s): %s" % filter_type)
        # If the filter_type is a string, convert it to a list
        if isinstance(filter_type, str):
            filter_type = [filter_type]

        # Filter the tagged files
        fw_tagged_files_filtered = {}
        for field, file_entry in fw_tagged_files.items():
            if isinstance(file_entry, list):
                log.debug(
                    "number of files for tag '%s' before filtering: %s"
                    % (field, len(file_entry))
                )
                file_entry_filtered = [f for f in file_entry if f.type in filter_type]
                if len(file_entry_filtered) == 0:
                    raise ValueError(
                        "No file found for tag '%s' with type '%s'."
                        % (field, filter_type)
                    )
                log.debug(
                    "number of files for tag '%s' after filtering: %s"
                    % (field, len(file_entry_filtered))
                )
                fw_tagged_files_filtered[field] = file_entry_filtered
            else:
                log.debug(
                    "Checking if file_entry.type '%s' is in filter_type '%s'"
                    % (file_entry.type, filter_type)
                )
                if file_entry.type not in filter_type:
                    raise ValueError(
                        "No file found for tag '%s' with type '%s'."
                        % (field, filter_type)
                    )
                log.debug(
                    "file_entry.type '%s' is in filter_type '%s'"
                    % (file_entry.type, filter_type)
                )
                fw_tagged_files_filtered[field] = file_entry
        return fw_tagged_files_filtered

    @staticmethod
    def filter_nifti_files(synced_files: dict):
        """
        Get only the nifti files from the synced files.
        :param synced_files:
        :return:
        """
        synced_nifti_files = {}
        for field, paths in synced_files.items():
            nifti_paths = []
            for file_path in paths:
                if file_path.endswith(".nii.gz"):
                    nifti_paths.append(file_path)
            synced_nifti_files[field] = nifti_paths
        return synced_nifti_files

    def create_tags_file_in_file(
        self, synced_files: dict, dest: Union[os.PathLike, str]
    ) -> Union[os.PathLike, str]:
        """
        Create the tags_file_in.yaml file and return its path.

        Args
        ----
        synced_files (dict): A dictionary containing the field names and the
            corresponding paths of the files that were synced. The paths are relative
            to the dest directory.
        dest (Union[os.PathLike, str]): The directory in which to save the
            tags_file_in.yaml file.
        """
        # Instantiate the TagsFileIn model with the synced files
        tags_file_in = self.tags_file_in_model(**synced_files)

        # Save the tags_file_in.yaml file to the dest directory
        tags_file_in_path = os.path.join(dest, "tags_file_in.yaml")
        TagsFileManager.save_tags_file_instance_to_yaml(
            tags_file_instance=tags_file_in,
            yaml_dir_path=dest,
            yaml_file_name="tags_file_in.yaml",
        )
        return tags_file_in_path

    def sync_file(
        self,
        fw_cli: FWCLI,
        file_entry: FileEntry,
        project_path: str,
        dest: Union[os.PathLike, str],
        params: str,
    ):
        # Create path to audit log and add it as a parameter to fw sync
        filename = uuid4().hex + ".csv"
        audit_log_path = os.path.join(dest, filename)
        params = params + f" --save-audit-logs {audit_log_path}"

        # Create the sync suffix params for the file, i.e., how to filter which
        # files to sync from the parent acquisition of the file
        self.create_sync_suffix_params_for_file(
            file_entry=file_entry,
            params=params,
        )

        # Sync the files to the gear's input directory
        fw_cli.sync(project_path=project_path, dest=dest, params=params)

        # Get the paths of the files that were synced to the gear's input
        # directory
        synced_files = self.get_paths_synced_files(audit_log_path=audit_log_path)

        return synced_files

    def create_sync_suffix_params_for_file(
        self,
        file_entry: FileEntry,
        params: str,
    ) -> str:
        # get the parent container of the file
        parent_container = self.gear_context.client.get(file_entry.parent_ref["id"])
        log.debug(
            "parent_container id: %s, label: %s, type: %s"
            % (
                parent_container.id,
                parent_container.label,
                parent_container.container_type,
            )
        )

        # Tag the parent container with its own id if it doesn't have it already
        if parent_container.id not in parent_container.tags:
            log.info(
                "Tagging parent container '%s' with its own id" % parent_container.id
            )
            PrepareSync.add_uuid_tag_to_container(
                container=parent_container, uuid_tag=parent_container.id
            )
        else:
            log.warning(
                "Parent container '%s' already has its own id as a tag. This means "
                "that this container was used for a previous sync."
                % parent_container.id
            )

        # Filter only acquisitions with the acquisition tag
        params = (
            params
            + ' --include-container-tags \'{"acquisition": ["%s"]}\''
            % parent_container.id
        )

        log.debug("params: %s" % params)

        return params

    @staticmethod
    def get_paths_synced_files(audit_log_path: Union[str, os.PathLike]):
        """
        Get the paths of the files that were synced to the gear's input directory.

        Args
        ----
        audit_log_path (Union[str, os.PathLike]): The path to the audit log file.

        Returns
        -------
        synced_files (List[str]): A list of the paths of the files that were synced. The
            paths are relative to a temporary directory within the gear.
        """
        # Read the audit log into a pandas dataframe
        audit_log = pd.read_csv(audit_log_path)

        # Get the paths of the files that were synced to the gear's input directory
        synced_files = audit_log["dest_path"].tolist()
        return synced_files


class GearInterface(ABC):
    def __init__(
        self,
        sync_instance: SyncInterface,
        gear_config_yaml: GearConfigYaml,
    ):
        self.sync_instance = sync_instance
        self.gear_config_yaml = gear_config_yaml

    @abstractmethod
    def get_algo_inputs(self, config_file_model: Type[BaseModel]) -> AlgoInputs:
        """
        This is the template method that calls prepares all the inputs of the
        algorithm.
        """
        raise NotImplementedError


class DefaultGearInterface(GearInterface):
    """
    Provide default implementations for only some of the methods in
    GearInterface. This gives flexibility to the user to only implement
    the methods they need.
    """

    def get_algo_inputs(self, config_file_model: Type[BaseModel]) -> AlgoInputs:
        # Generate the tags_file_in.yaml file by calling the main sync function
        tags_file_in_path = self.sync_instance.sync_main_function()

        # Get the config.yaml file and verify that it has the correct
        # parameters
        config_yaml_path = self.gear_config_yaml.get_and_verify_config_yaml(
            config_file_model=config_file_model
        )

        # Return the inputs of the algorithm
        algo_inputs = AlgoInputs(
            config_file_path=config_yaml_path,
            tags_file_in_path=tags_file_in_path,
        )
        return algo_inputs
