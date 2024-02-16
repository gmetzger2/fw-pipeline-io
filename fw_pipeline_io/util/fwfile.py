"""
Utility functions for Flywheel files
"""

from typing import Union, Tuple, List
import os


def split_dicom_ext(filename: Union[str, os.PathLike]) -> Tuple[str, List[str]]:
    extensions = []
    file_name, ext = os.path.splitext(filename)
    extensions.append(ext)
    if '.dicom' not in file_name and '.dcm' not in file_name:
        return file_name, extensions

    num_loops = 2
    count = 0
    while extensions[-1] not in ['.dicom', '.dcm'] and count < num_loops:
        file_name, ext = os.path.splitext(file_name)
        extensions.append(ext)
        count += 1
    return file_name, extensions
