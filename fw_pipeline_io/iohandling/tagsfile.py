from typing import List, Tuple, Type, Union
from pydantic import BaseModel
import yaml
import os
import logging

log = logging.getLogger(__name__)


class TagsFileManager:
    """
    A manager class for handling Pydantic models representing tags files.

    This class provides static methods for retrieving field names and types
    from a Pydantic tags model, creating an instance of the model with
    specified field values, and saving a model instance to a YAML file.

    The methods in this class assume that the Pydantic tags model has fields
    of type str or typing.List[str]. If the model has fields of other types,
    a ValueError will be raised.
    """

    @staticmethod
    def get_model_fields_and_types(
        tags_file: Type[BaseModel],
    ) -> List[Tuple[str, type]]:
        """
        Get and return the fields and types of a pydantic TagsFileIn or
        TagsFileOut models.

        This can only handle models that have fields of type str or
        typing.List[str]. If the model has fields of other types, a ValueError
        will be raised. If the model has fields of type typing.List[str], the
        inner type must be str. If the inner type is not str, a ValueError will
        be raised.

        If the model has fields of type str, the field name and type will be
        returned as a tuple. If the model has fields of type typing.List[str],
        the field name and type will be returned as a tuple, and the type will
        be converted to list.

        Args
        ----
        tags_file: Type[BaseModel]
            A concrete class of pydantic.BaseModel that represents the input or
            output tags file. This is the uninstantiated class.
            Here's an example:
                class TagsFileIn(BaseModel):
                    # TSEs
                    t2_tse: List[str] = Field(...)

        Returns
        -------
        fields_and_types: List[Tuple[str, type]]
            A list of tuples containing the field names and types of the model.
        """
        # Get the annotations from the model
        model_annotations = tags_file.__annotations__

        # Create a list to store field names and types
        fields_and_types = []

        # Append field names and types to the list
        for field_name, field_type in model_annotations.items():
            # Convert typing.List[str] to list
            if hasattr(field_type, "__origin__") and field_type.__origin__ is list:
                # Verify the inner one is a str
                if field_type.__args__[0] is not str:
                    raise ValueError("The inner type of a list must be str.")
                # Convert the type to list
                field_type = list
                fields_and_types.append((field_name, field_type))
            # Append if type is a str
            elif field_type is str:
                fields_and_types.append((field_name, field_type))
            # Raise error if type is not str or typing.List[str]
            else:
                raise ValueError(
                    "The type of a field must be str or typing.List[str]."
                    " The type of field '%s' was %s." % (field_name, field_type)
                )
        return fields_and_types

    @staticmethod
    def create_tags_file_model(
        fields_and_types: List[Tuple[str, type]], tags_file: Type[BaseModel]
    ) -> BaseModel:
        """
        Create a pydantic TagsFileIn model with the specified field values.

        Args
        ----
        fields_and_types: List[Tuple[str, type]]
            A list of tuples containing the field names and types of the model.
            This can be obtained from get_model_fields_and_types().
        tags_file: Type[BaseModel]
            A concrete class of pydantic.BaseModel that represents the input or
            output tags file. This is the uninstantiated class.
            Here's an example:
                class TagsFileIn(BaseModel):
                    # TSEs
                    t2_tse: List[str] = Field(...)

        Returns
        -------
        tags_file_instance: BaseModel
            An instance of the TagsFileIn model with the specified field values.
        """
        # Create a dictionary to store field values
        model_data = {}

        # Iterate through the field values and types
        for field_name, field_type in fields_and_types:
            # Check if the field type is List
            if issubclass(field_type, list):
                # If it's a list, create a List field
                model_data[field_name] = []
            elif issubclass(field_type, str):
                # If it's a string, create a single-value field
                model_data[field_name] = ""
            else:
                # Handle other types accordingly
                print(f"Unsupported type for field {field_name}")

        # Instantiate the TagsFileIn model with the created data
        tags_file_instance = tags_file(**model_data)
        return tags_file_instance

    @staticmethod
    def save_tags_file_instance_to_yaml(
        tags_file_instance,
        yaml_dir_path: Union[str, os.PathLike],
        yaml_file_name: str = "tags_file.yaml",
    ):
        """
        Save a TagsFileIn or TagsFileOut instance to a YAML file.

        Args
        ----
        tags_file_instance: TagsFileIn or TagsFileOut
            An instance of a TagsFileIn or TagsFileOut model, which is a concrete
            class of pydantic.BaseModel.
        yaml_dir_path: Union[str, os.PathLike]
            The path to the directory where the YAML file will be saved.
        yaml_file_name: str, optional
            The name of the YAML file. Defaults to "tags_file.yaml".
        """
        yaml_file_path = os.path.join(yaml_dir_path, yaml_file_name)
        with open(yaml_file_path, "w") as yaml_file:
            yaml.dump(tags_file_instance.dict(), yaml_file)

        log.info("Tags file saved to %s" % yaml_file_path)
