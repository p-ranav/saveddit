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
from saveddit.search_config import SearchConfig
import sys
from tqdm import tqdm

class SearchSubreddits:
    config = SubredditDownloader.config
    REDDIT_CLIENT_ID = config['reddit_client_id']
    REDDIT_CLIENT_SECRET = config['reddit_client_secret']
    IMGUR_CLIENT_ID = config['imgur_client_id']

    REDDIT_USERNAME = None
    try:
        REDDIT_USERNAME = config['reddit_username']
    except Exception as e:
        pass

    REDDIT_PASSWORD = None
    if REDDIT_USERNAME:
        if sys.stdin.isatty():
            print("Username: " + REDDIT_USERNAME)
            REDDIT_PASSWORD = getpass.getpass("Password: ")
        else:
            # echo "foobar" > password
            # saveddit user .... < password
            REDDIT_PASSWORD = sys.stdin.readline().rstrip()

    def __init__(self, subreddit_names):
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

        if not SearchSubreddits.REDDIT_USERNAME:
            self.logger.error("`reddit_username` in user_config.yaml is empty")
            self.logger.error("If you plan on using the user API of saveddit, then add your username to user_config.yaml")
            print("Exiting now")
            exit()
        else:
            if not len(SearchSubreddits.REDDIT_PASSWORD):
                if sys.stdin.isatty():
                    print("Username: " + REDDIT_USERNAME)
                    REDDIT_PASSWORD = getpass.getpass("Password: ")
                else:
                    # echo "foobar" > password
                    # saveddit user .... < password
                    REDDIT_PASSWORD = sys.stdin.readline().rstrip()

        self.reddit = praw.Reddit(
            client_id=SearchSubreddits.REDDIT_CLIENT_ID,
            client_secret=SearchSubreddits.REDDIT_CLIENT_SECRET,
            user_agent="saveddit (by /u/p_ranav)"
        )

        self.multireddit_name = "+".join(subreddit_names)
        self.subreddit = self.reddit.subreddit(self.multireddit_name)

    def download(self, args):
        output_path = args.o
        query = args.q
        sort = args.s
        syntax = SearchConfig.DEFAULT_SYNTAX
        time_filter = args.t
        include_nsfw = args.include_nsfw
        skip_comments = args.skip_comments
        skip_videos = args.skip_videos
        skip_meta = args.skip_meta
        comment_limit = 0 # top-level comments ONLY

        self.logger.verbose("Searching '" + query + "' in " + self.multireddit_name + ", sorted by " + sort)
        if include_nsfw:
            self.logger.spam("     * Including NSFW results")

        search_dir = os.path.join(os.path.join(os.path.join(os.path.join(os.path.join(
          output_path, "www.reddit.com"), "q"), query), self.multireddit_name), sort)

        if not os.path.exists(search_dir):
            os.makedirs(search_dir)

        search_results = None
        if include_nsfw:
            search_params = {"include_over_18": "on"}
            search_results = self.subreddit.search(query, sort, syntax, time_filter, params=search_params)
        else:
            search_results = self.subreddit.search(query, sort, syntax, time_filter)

        results_found = False
        for i, submission in enumerate(search_results):
            if not results_found:
                results_found = True
            SubmissionDownloader(submission, i, self.logger, search_dir,
                skip_videos, skip_meta, skip_comments, comment_limit,
                {'imgur_client_id': SubredditDownloader.IMGUR_CLIENT_ID})

        if not results_found:
            self.logger.spam("     * No results found")