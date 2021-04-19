import coloredlogs
from colorama import Fore, Style
from datetime import datetime, timezone
import logging
import verboselogs
import getpass
import json
import os
import praw
from pprint import pprint
import re
from saveddit.submission_downloader import SubmissionDownloader
from saveddit.subreddit_downloader import SubredditDownloader
from saveddit.multireddit_downloader_config import MultiredditDownloaderConfig
import sys
from tqdm import tqdm

class MultiredditDownloader:
    config = SubredditDownloader.config
    REDDIT_CLIENT_ID = config['reddit_client_id']
    REDDIT_CLIENT_SECRET = config['reddit_client_secret']
    IMGUR_CLIENT_ID = config['imgur_client_id']

    def __init__(self, multireddit_names):
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

        self.reddit = praw.Reddit(
            client_id=MultiredditDownloader.REDDIT_CLIENT_ID,
            client_secret=MultiredditDownloader.REDDIT_CLIENT_SECRET,
            user_agent="saveddit (by /u/p_ranav)"
        )

        self.multireddit_name = "+".join(multireddit_names)
        self.multireddit = self.reddit.subreddit(self.multireddit_name)

    def download(self, output_path, categories=MultiredditDownloaderConfig.DEFAULT_CATEGORIES, post_limit=MultiredditDownloaderConfig.DEFAULT_POST_LIMIT, skip_videos=False, skip_meta=False, skip_comments=False, comment_limit=0):
        '''
        categories: List of categories within the multireddit to download (see MultiredditDownloaderConfig.DEFAULT_CATEGORIES)
        post_limit: Number of posts to download (default: None, i.e., all posts)
        comment_limit: Number of comment levels to download from submission (default: `0`, i.e., only top-level comments)
          - to get all comments, set comment_limit to `None`
        '''

        multireddit_dir_name = self.multireddit_name
        if len(multireddit_dir_name) > 64:
            multireddit_dir_name = multireddit_dir_name[0:63]
            multireddit_dir_name += "..."

        root_dir = os.path.join(os.path.join(os.path.join(
            output_path, "www.reddit.com"), "m"), multireddit_dir_name)
        categories = categories

        for c in categories:
            self.logger.notice("Downloading from /m/" +
                               self.multireddit_name + "/" + c + "/")
            category_dir = os.path.join(root_dir, c)
            if not os.path.exists(category_dir):
                os.makedirs(category_dir)
            category_function = getattr(self.multireddit, c)

            for i, submission in enumerate(category_function(limit=post_limit)):
                SubmissionDownloader(submission, i, self.logger, category_dir,
                    skip_videos, skip_meta, skip_comments, comment_limit,
                    {'imgur_client_id': MultiredditDownloader.IMGUR_CLIENT_ID})
