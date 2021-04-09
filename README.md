<p align="center">
  <img height="50" src="images/logo.png"/>
</p>

`saveddit` is a bulk media downloader for reddit.

* Download from subreddits - submissions, comments, images, and videos
* Download from user pages - comments, submissions, gilded, upvoted, and saved posts

## Quick Start

```console
pip3 install saveddit
```

### Setting up authorization

* [Register an application with Reddit](https://ssl.reddit.com/prefs/apps/)
  - Write down your client ID and secret from the app
  - More about Reddit API access [here](https://ssl.reddit.com/wiki/api)
  - Wiki page about Reddit OAuth2 applications [here](https://github.com/reddit-archive/reddit/wiki/OAuth2)

<p align="left">
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<img height="300" src="images/reddit_app.png"/>
</p>

* [Register an application with Imgur](https://api.imgur.com/oauth2/addclient)
  - Write down the Imgur client ID from the app

<p align="left">
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<img height="600" src="images/imgur_app.png"/>
</p>

These registrations will authorize you to use the Reddit and Imgur APIs to download publicly available information.

### User configuration

The first time you run `saveddit`, you will see something like this:

```console
foo@bar:~$ saveddit
Retrieving configuration from ~/.saveddit/user_config.yaml file
No configuration file found.
Creating one. Please edit ~/.saveddit/user_config.yaml with valid credentials.
Exiting
```

* Open the generated `~/.saveddit/user_config.yaml`
* Update the client IDs and secrets from the previous step

```yaml
imgur_client_id: '<YOUR_IMGUR_CLIENT_ID>'
reddit_client_id: '<YOUR_REDDIT_CLIENT_ID>'
reddit_client_secret: '<YOUR_REDDIT_CLIENT_SECRET>'
```

* If you plan on using the `user` API, also add your username and password to the file.

```yaml
reddit_username: '<YOUR_REDDIT_USERNAME>'
reddit_password: '<YOUR_REDDIT_PASSWORD>'
```

### Download from Subreddit

```console
foo@bar:~$ saveddit subreddit -h
Retrieving configuration from /Users/pranav/.saveddit/user_config.yaml file

usage: saveddit subreddit [-h] [-f categories [categories ...]] [-l post_limit] [--skip-comments] [--skip-meta] [--skip-videos] -o output_path subreddits [subreddits ...]

positional arguments:
  subreddits            Names of subreddits to download, e.g., AskReddit

optional arguments:
  -h, --help            show this help message and exit
  -f categories [categories ...]
                        Categories of posts to download (default: ['hot', 'new', 'rising', 'controversial', 'top', 'gilded'])
  -l post_limit         Limit the number of submissions downloaded in each category (default: None, i.e., all submissions)
  --skip-comments       When true, saveddit will not save comments to a comments.json file
  --skip-meta           When true, saveddit will not save meta to a submission.json file on submissions
  --skip-videos         When true, saveddit will not download videos (e.g., gfycat, redgifs, youtube, v.redd.it links)
  -o output_path        Directory where saveddit will save downloaded content
```

#### Example Usage: Download the hottest 15 posts each from /r/pics and /r/aww

```console
foo@bar:~$ saveddit subreddit pics aww -f hot -l 5 -o ~/Desktop
```

You can download from multiple subreddits and use multiple filters:

```console
foo@bar:~$ saveddit subreddit funny AskReddit -f hot top new rising -l 5 -o ~/Downloads/Reddit/.
```

### Download from User's page

```console
foo@bar:~$ saveddit user -h
Retrieving configuration from /Users/pranav/.saveddit/user_config.yaml file

usage: saveddit user [-h] users [users ...] {saved,gilded,submitted,upvoted,comments} ...

positional arguments:
  users                 Names of users to download, e.g., Poem_for_your_sprog
  {saved,gilded,submitted,upvoted,comments}

optional arguments:
  -h, --help            show this help message and exit
```

#### Example Usage: Download gilded submissions by user

```console
saveddit user "Poem_for_your_sprog" gilded -o ~/Desktop
```

### Example Output

```console
foo@bar:~$ tree ~/Downloads/www.reddit.com
/Users/pranav/Downloads/www.reddit.com
├── r
│   └── aww
│       └── new
│           ├── 000_We_decided_to_foster_a_litter_of...
│           │   ├── comments.json
│           │   ├── files
│           │   │   └── 7fjt2gkp32s61.jpg
│           │   └── submission.json
│           ├── 001_Besties_
│           │   ├── comments.json
│           │   ├── files
│           │   │   └── zklpm1qo32s61.jpg
│           │   └── submission.json
│           ├── 002_My_cat_dice_with_his_best_friend...
│           │   ├── comments.json
│           │   ├── files
│           │   │   └── av3yrbmo32s61.jpg
│           │   └── submission.json
│           ├── 003_Digging_makes_her_the_happiest_
│           │   ├── comments.json
│           │   ├── files
│           │   │   └── zjw5f3yl32s61.jpg
│           │   └── submission.json
│           └── 004_Our_beloved_pup_needs_some_help_...
│               ├── comments.json
│               ├── files
│               │   ├── 66su4i9b32s61.mp4
│               │   ├── 66su4i9b32s61_audio.mp4
│               │   └── 66su4i9b32s61_video.mp4
│               └── submission.json
└── u
    └── Poem_for_your_sprog
        └── gilded
            ├── 000_Comment__The_guy_was_the_biggest_deal_an...
            │   └── comments.json
            ├── 001_Comment__tl_dr_life_is_long_Journey_s_h...
            │   └── comments.json
            ├── 002_Comment_From_Northwind_mine_to_Talos_shr...
            │   └── comments.json
            ├── 003_Comment__I_feel_terrible_having_people_j...
            │   └── comments.json
            └── 004_Comment_I_often_stop_a_time_or_two_At_...
                └── comments.json

21 directories, 22 files
(saveddit_prod) (base)
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
