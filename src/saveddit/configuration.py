import os
from typing import Union
import yaml
import pathlib
import colorama
import sys


class ConfigurationLoader:
    PURPLE = colorama.Fore.MAGENTA
    WHITE = colorama.Style.RESET_ALL
    RED = colorama.Fore.RED

    @staticmethod
    def load(path):
        """
        Loads Saveddit configuration from a configuration file.
        If ifle is not found, create one and exit.

        Arguments:
            path: path to user_config.yaml file

        Returns:
            A Python dictionary with Saveddit configuration info
        """

        def _create_config(_path):
            _STD_CONFIG = {
                "reddit_client_id": "",
                "reddit_client_secret": "",
                "reddit_username": "",
                "imgur_client_id": "",
            }
            with open(_path, "x") as _f:
                yaml.dump(_STD_CONFIG, _f)
            sys.exit(0)

        # Explicitly converting path to POSIX-like path (to avoid '\\' hell)
        print(
            "{notice}Retrieving configuration from {path} file{white}".format(
                path=path,
                notice=ConfigurationLoader.PURPLE,
                white=ConfigurationLoader.WHITE,
            )
        )
        path = pathlib.Path(path).absolute().as_posix()

        # Check if file exists. If not, create one and fill it with std config template
        if not os.path.exists(path):
            print(
                "{red}No configuration file found.\nCreating one. Please edit {path} with valid credentials.\nExiting{white}".format(
                    red=ConfigurationLoader.RED,
                    path=path,
                    white=ConfigurationLoader.WHITE,
                )
            )
            _create_config(path)

        with open(path, "r") as _f:
            return yaml.safe_load(_f.read())
