<p align="center">
  <img height="70" src="images/logo.png"/>
</p>

`saveddit` is a bulk media downloader for reddit.

## Quick Start

```console
foo@bar:~$ git clone git@github.com:p-ranav/saveddit
foo@bar:~$ cd saveddit
foo@bar:~$ python3 -m pip install -r requirements.txt
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

The following will:
* Download from the `/r/pics` subreddit
* Download submissions from the `/r/pics/hot`
* Limit to `5` submissions
* Save downloads to `/home/pranav/Downloads/Reddit/.`

```console
foo@bar:~$ python3 -m saveddit.saveddit -r pics -f hot -l 5 -o /home/pranav/Downloads/Reddit/.
```

You can download from multiple subreddits and use multiple filters:

```console
foo@bar:~$ python3 -m saveddit.saveddit -r funny AskReddit -f hot top new rising -l 5 -o /home/pranav/Downloads/Reddit/.
```

### Example Output

```console
foo@bar:~$ tree /Users/pranav/Downloads/Reddit
/Users/pranav/Downloads/Reddit
└── www.reddit.com
    └── r
        └── aww
            └── new
                ├── 0000_Squirrel_tickles
                │   ├── comments.json
                │   ├── files
                │   │   ├── 891cwv3f6gr61.mp4
                │   │   ├── 891cwv3f6gr61_audio.mp4
                │   │   └── 891cwv3f6gr61_video.mp4
                │   └── submission.json
                ├── 0001_meet_my_friend_Commando
                │   ├── comments.json
                │   ├── files
                │   │   └── ynutef1e6gr61.jpg
                │   └── submission.json
                ├── 0002_Got_a_surprise_when_I_got_home__�\237\220�
                │   ├── comments.json
                │   ├── files
                │   │   └── eeo7zrih6gr61.jpg
                │   └── submission.json
                ├── 0003_Reddit__meet_Atlas__Newest_member_of_the_fam
                │   ├── comments.json
                │   ├── files
                │   │   └── kl9aqogb6gr61.jpg
                │   └── submission.json
                ├── 0004_Cute_otter_with_cute_hats
                │   ├── comments.json
                │   ├── files
                │   │   ├── p485p64hhcr61.jpg
                │   │   ├── pso5vkihhcr61.jpg
                │   │   ├── rrxbx7ehhcr61.jpg
                │   │   └── uevyyqlhhcr61.jpg
                │   └── submission.json
                └── 0005_He_loves_this_strange_position_�\237\230\202
                    ├── comments.json
                    ├── files
                    │   └── u7q25wx86gr61.jpg
                    └── submission.json

16 directories, 23 files
```

## Supported Links:

* Direct links to images or videos, e.g., `.png`, `.jpg`, `.mp4`, `.gif` etc.
* Reddit galleries `reddit.com/gallery/...`
* Reddit videos `v.redd.it/...`
* Gfycat links `gfycat.com/...`
* Redgif links `redgifs.com/...`
* Imgur images `imgur.com/...`
* Imgur albums `imgur.com/a/...` and `imgur.com/gallery/...`
* Youtube links `youtube.com/...` and `yout.be/...`
* These [sites](https://ytdl-org.github.io/youtube-dl/supportedsites.html) supported by `youtube-dl`
* Self posts
* For all other cases, `saveddit` will simply fetch the HTML of the URL

## Contributing
Contributions are welcome, have a look at the [CONTRIBUTING.md](CONTRIBUTING.md) document for more information.

## License
The project is available under the [MIT](https://opensource.org/licenses/MIT) license.