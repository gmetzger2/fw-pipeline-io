import argparse


def create_args_parser():
    """
        Returns a parser that can be either called by the algorithm or by the gear.

        This standardizes the two input paths that are required for every algorithm
        in the pipeline: a config_file_path and the tags_file_in file.

        If using it in the algorithm, it can be called as follows:

    `        #Create the args and parser
            >>> parser = create_args_parser()

            # Parse args from the command line
            >>> args_main = parser.parse_args()

            # The command line will take the two positional arguments when main
            is called, for example:
            >>> python main.py "<path_to_config_file>" "<path_to_tags_file_in>"

        If using it in the gear, it can be called as follows:

                #Create the args and parser
                >>> parser = create_args_parser()

                # Parse args from the command line
                >>> args_main = parser.parse_args(["<path_to_config_file>", "<path_to_tags_file_in>"])
    """
    parser = argparse.ArgumentParser(description="Perform T2 mapping from TSE images")
    parser.add_argument(
        "config_file_path",
        help="The file path to the config.yml file that will be used for " "this run.",
    )
    parser.add_argument(
        "tags_file_in_path",
        help="The file path to the tags_file_in.yml file. This files contains "
        "all the input file paths that the algorithm needs to run.",
    )

    return parser
