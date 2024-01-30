import os
import tempfile
from typing import List, Tuple
from pydantic import BaseModel
from fw_pipeline_io.iohandling.tagsfile import TagsFileManager
import unittest
import yaml


class TagsFileIn(BaseModel):
    field1: str
    field2: List[str]


class TestTagsFileManager:
    def setup_method(self):
        self.tags_file_manager = TagsFileManager()

    def test_get_model_fields_and_types(self):
        """
        Test the get_model_fields_and_types method of TagsFileManager.
        """
        fields_and_types = self.tags_file_manager.get_model_fields_and_types(TagsFileIn)
        assert fields_and_types == [("field1", str), ("field2", list)]

    def test_create_tags_file_model(self):
        """
        Test the create_tags_file_model method of TagsFileManager.
        """
        fields_and_types = [("field1", str), ("field2", list)]
        tags_file_instance = self.tags_file_manager.create_tags_file_model(
            fields_and_types, TagsFileIn
        )
        assert isinstance(tags_file_instance, TagsFileIn)
        assert tags_file_instance.field1 == ""
        assert tags_file_instance.field2 == []

    def test_save_tags_file_instance_to_yaml(self):
        """
        Test the save_tags_file_instance_to_yaml method of TagsFileManager.
        """
        fields_and_types = [("field1", str), ("field2", list)]
        tags_file_instance = self.tags_file_manager.create_tags_file_model(
            fields_and_types, TagsFileIn
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            yaml_file_path = os.path.join(temp_dir, "test_tags_file.yaml")
            self.tags_file_manager.save_tags_file_instance_to_yaml(
                tags_file_instance, temp_dir, "test_tags_file.yaml"
            )

            assert os.path.exists(yaml_file_path)
            with open(yaml_file_path, "r") as yaml_file:
                yaml_content = yaml.load(yaml_file, Loader=yaml.FullLoader)
                assert yaml_content["field1"] == ""
                assert yaml_content["field2"] == []


if __name__ == "__main__":
    unittest.main()
