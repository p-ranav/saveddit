<p align="center">
  <img height="70" src="images/logo.png"/>
</p>

`saveddit` is a bulk media downloader for reddit.

## Quick Start

```console
foo@bar:~$ git clone git@github.com:p-ranav/saveddit
foo@bar:~$ cd saveddit
foo@bar:~$ python3 -m saveddit.saveddit --help
                                .___  .___.__  __
   ___________ ___  __ ____   __| _/__| _/|__|/  |_
  /  ___/\__  \\  \/ // __ \ / __ |/ __ | |  \   __\
  \___ \  / __ \\   /\  ___// /_/ / /_/ | |  ||  |
 /____  >(____  /\_/  \___  >____ \____ | |__||__|
      \/      \/          \/     \/    \/

 Downloader for Reddit
 version : v1.0.0
 URL     : https://github.com/p-ranav/saveddit

usage: saveddit [-h] -r subreddits [subreddits ...] [-f categories [categories ...]] [-l post_limit] [--skip-comments] -o output_path

optional arguments:
  -h, --help            show this help message and exit
  -r subreddits [subreddits ...]
                        Names of subreddits to download, e.g., AskReddit
  -f categories [categories ...]
                        Categories of posts to download (default: ['hot', 'new', 'rising', 'controversial', 'top', 'gilded'])
  -l post_limit         Limit the number of submissions downloaded in each category (default: None, i.e., all submissions)
  --skip-comments       When true, saveddit will not save comments to a comments.json file
  -o output_path        Directory where saveddit will save downloaded content
```

### Example Usage

```console
foo@bar:~$ python3 -m saveddit.saveddit -r pics -f hot new -l 100 -o /home/pranav/Downloads/Reddit/.
```