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
                "{red}No configuration file found.\nCreating one. Would you like to edit it now?\n > Choose {purple}Y{red} for yes and {purple}N{red} for no.{white}".format(
                    red=ConfigurationLoader.RED,
                    path=path,
                    white=ConfigurationLoader.WHITE,
                    purple=ConfigurationLoader.PURPLE,
                )
            )
            getchoice = str(input("> "))
            if getchoice == "Y":
               reddit_client = str(input("Reddit Client ID: "))
               reddit_client_sec = str(input("Reddit Client Secret: "))
               reddit_user = str(input("Reddit Username: "))
               imgur_client = str(input("Imgur Client ID: "))
               STD_CONFIG = {
                   "reddit_client_id": "".format(reddit_client),
                   "reddit_client_secret": "".format(reddit_client_sec),
                   "reddit_username": "".format(reddit_user),
                   "imgur_client_id": "".format(imgur_client),
               }
               with open(path, "x") as f:
                   yaml.dump(STD_CONFIG, f)
               sys.exit(0)
            elif getchoice == "N":
               print(
                "{red}Alright.\nPlease edit {path} with valid credentials.\nExiting{white}".format(
                    red=ConfigurationLoader.RED,
                    path=path,
                    white=ConfigurationLoader.WHITE,
                )
            )
                _create_config(path)
            else:
                print("Invalid choice.")
                exit()

        with open(path, "r") as _f:
            return yaml.safe_load(_f.read())
