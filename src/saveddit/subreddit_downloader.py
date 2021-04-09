import coloredlogs
from colorama import Fore
import logging
import verboselogs
import os
import praw
from saveddit.configuration import ConfigurationLoader
from saveddit.submission_downloader import SubmissionDownloader
from saveddit.subreddit_downloader_config import SubredditDownloaderConfig

class SubredditDownloader:
    app_config_dir = os.path.expanduser("~/.saveddit")
    if not os.path.exists(app_config_dir):
        os.makedirs(app_config_dir)

    config_file_location = os.path.expanduser("~/.saveddit/user_config.yaml")
    config = ConfigurationLoader.load(config_file_location)

    REDDIT_CLIENT_ID = config['reddit_client_id']
    REDDIT_CLIENT_SECRET = config['reddit_client_secret']
    IMGUR_CLIENT_ID = config['imgur_client_id']

    def __init__(self, subreddit_name):
        self.subreddit_name = subreddit_name
        reddit = praw.Reddit(
            client_id=SubredditDownloader.REDDIT_CLIENT_ID,
            client_secret=SubredditDownloader.REDDIT_CLIENT_SECRET,
            user_agent="saveddit (by /u/p_ranav)",
        )
        self.subreddit = reddit.subreddit(subreddit_name)

        self.logger = verboselogs.VerboseLogger(__name__)
        level_styles = {
            'critical': {'bold': True, 'color': 'red'},
            'debug': {'color': 'green'},
            'error': {'color': 'red'},
            'info': {'color': 'white'},
            'notice': {'color': 'magenta'},
            'spam': {'color': 'white', 'faint': True},
            'success': {'bold': True, 'color': 'green'},
            'verbose': {'color': 'blue'},
            'warning': {'color': 'yellow'}
        }
        coloredlogs.install(level='SPAM', logger=self.logger,
                            fmt='%(message)s', level_styles=level_styles)

    def download(self, output_path, categories=SubredditDownloaderConfig.DEFAULT_CATEGORIES, post_limit=SubredditDownloaderConfig.DEFAULT_POST_LIMIT, skip_videos=False, skip_meta=False, skip_comments=False, comment_limit=0):
        '''
        categories: List of categories within the subreddit to download (see SubredditDownloaderConfig.DEFAULT_CATEGORIES)
        post_limit: Number of posts to download (default: None, i.e., all posts)
        comment_limit: Number of comment levels to download from submission (default: `0`, i.e., only top-level comments)
          - to get all comments, set comment_limit to `None`
        '''
        root_dir = os.path.join(os.path.join(os.path.join(
            output_path, "www.reddit.com"), "r"), self.subreddit_name)
        categories = categories

        for c in categories:
            self.logger.notice("Downloading from /r/" +
                               self.subreddit_name + "/" + c + "/")
            category_dir = os.path.join(root_dir, c)
            if not os.path.exists(category_dir):
                os.makedirs(category_dir)
            category_function = getattr(self.subreddit, c)

            for i, submission in enumerate(category_function(limit=post_limit)):
                SubmissionDownloader(submission, i, self.logger, category_dir,
                    skip_videos, skip_meta, skip_comments, comment_limit,
                    {'imgur_client_id': SubredditDownloader.IMGUR_CLIENT_ID})
