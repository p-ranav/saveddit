import coloredlogs
from colorama import Fore, Style
from datetime import datetime, timezone
import logging
import verboselogs
import json
import os
import praw
from pprint import pprint
import re
from saveddit.submission_downloader import SubmissionDownloader
from saveddit.subreddit_downloader import SubredditDownloader
from tqdm import tqdm


class UserDownloader():
    config = SubredditDownloader.config

    REDDIT_CLIENT_ID = config['reddit_client_id']
    REDDIT_CLIENT_SECRET = config['reddit_client_secret']
    try:
        REDDIT_USERNAME = config['reddit_username']
    except Exception as e:
        print(Fore.RED + 'ERROR: Failed to find value for "reddit_username" in user_config.yaml')
        print("Create an entry in user_config.yaml:")
        print("  'reddit_username': <YOUR_REDDIT_USERNAME>")
        print(Style.RESET_ALL, end="")
        print('Exiting now')
        exit()

    try:
        REDDIT_PASSWORD = config['reddit_password']
    except Exception as e:
        print(Fore.RED + 'ERROR: Failed to find value for "reddit_password" in user_config.yaml')
        print("Create an entry in user_config.yaml:")
        print("  reddit_password: '<YOUR_REDDIT_PASSWORD>'")
        print(Style.RESET_ALL, end="")
        print('Exiting now')
        exit()

    IMGUR_CLIENT_ID = config['imgur_client_id']
    DEFAULT_CATEGORIES = ["comments", "submitted", "saved"]
    DEFAULT_SORT = "hot"
    DEFAULT_SORT_OPTIONS = ["hot", "new", "top", "controversial"]
    DEFAULT_POST_LIMIT = None
    DEFAULT_COMMENT_LIMIT = None

    def __init__(self):
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
            client_id=UserDownloader.REDDIT_CLIENT_ID,
            client_secret=UserDownloader.REDDIT_CLIENT_SECRET,
            user_agent="saveddit (by /u/p_ranav)",
            username=UserDownloader.REDDIT_USERNAME,
            password=UserDownloader.REDDIT_PASSWORD
        )

    def download_comments(self, args):
        output_path = args.o

        for username in args.users:
            user = self.reddit.redditor(name=username)

            self.logger.notice("Downloading from /u/" + username + "/comments")

            root_dir = os.path.join(os.path.join(os.path.join(
                output_path, "www.reddit.com"), "u"), username)

            try:
                sort = args.s
                limit = args.l

                comments_dir = os.path.join(root_dir, "comments")
                if not os.path.exists(comments_dir):
                    os.makedirs(comments_dir)

                self.logger.verbose("Downloading comments sorted by " + sort)
                category_function = getattr(user.comments, sort)

                category_dir = os.path.join(comments_dir, sort)

                if category_function:
                    if not os.path.exists(category_dir):
                        os.makedirs(category_dir)
                    for i, comment in enumerate(category_function(limit=limit)):
                        prefix_str = '#' + str(i).zfill(3) + ' '
                        self.indent_1 = ' ' * len(prefix_str) + "* "
                        self.indent_2 = ' ' * len(self.indent_1) + "- "

                        comment_body = comment.body
                        comment_body = comment_body[0:32]
                        comment_body = re.sub(r'\W+', '_', comment_body)
                        comment_filename = str(i).zfill(3) + "_Comment_" + \
                            comment_body + "..." + ".json"
                        self.logger.spam(self.indent_1 + comment.id + ' - "' + comment.body[0:64].replace("\n", "").replace("\r", "")  + '..."')

                        with open(os.path.join(category_dir, comment_filename), 'w') as file:
                            comment_dict = {}
                            try:
                                if comment.author:
                                    comment_dict["author"] = comment.author.name
                                else:
                                    comment_dict["author"] = None
                                comment_dict["body"] = comment.body
                                comment_dict["created_utc"] = int(comment.created_utc)
                                comment_dict["distinguished"] = comment.distinguished
                                comment_dict["downs"] = comment.downs
                                comment_dict["edited"] = comment.edited
                                comment_dict["id"] = comment.id
                                comment_dict["is_submitter"] = comment.is_submitter
                                comment_dict["link_id"] = comment.link_id
                                comment_dict["parent_id"] = comment.parent_id
                                comment_dict["permalink"] = comment.permalink
                                comment_dict["score"] = comment.score
                                comment_dict["stickied"] = comment.stickied
                                comment_dict["subreddit_name_prefixed"] = comment.subreddit_name_prefixed
                                comment_dict["subreddit_id"] = comment.subreddit_id
                                comment_dict["total_awards_received"] = comment.total_awards_received
                                comment_dict["ups"] = comment.ups
                                file.write(json.dumps(comment_dict, indent=2))
                            except Exception as e:
                                self.print_formatted_error(e)
            except Exception as e:
                self.logger.error("Unable to download comments for user `" + username + "` - " + str(e))

    def download_submitted(self, args):
        output_path = args.o

        for username in args.users:
            user = self.reddit.redditor(name=username)

            self.logger.notice("Downloading from /u/" + username + "/submitted")

            root_dir = os.path.join(os.path.join(os.path.join(
                output_path, "www.reddit.com"), "u"), username)

            try:
                post_limit = args.l
                sort = args.s
                skip_meta = args.skip_meta
                skip_videos = args.skip_videos
                skip_comments = args.skip_comments
                comment_limit = 0 # top-level comments ONLY

                submitted_dir = os.path.join(root_dir, "submitted")
                if not os.path.exists(submitted_dir):
                    os.makedirs(submitted_dir)

                self.logger.verbose("Downloading submissions sorted by " + sort)
                category_function = getattr(user.submissions, sort)

                category_dir = os.path.join(submitted_dir, sort)

                if category_function:
                    for i, s in enumerate(category_function(limit=post_limit)):
                        prefix_str = '#' + str(i).zfill(3) + ' '
                        self.indent_1 = ' ' * len(prefix_str) + "* "
                        self.indent_2 = ' ' * len(self.indent_1) + "- "
                        SubmissionDownloader(s, i, self.logger, category_dir, skip_videos, skip_meta, skip_comments, comment_limit,
                                                {'imgur_client_id': UserDownloader.IMGUR_CLIENT_ID})
            except Exception as e:
                self.logger.error("Unable to download submitted posts for user `" + username + "` - " + str(e))

    def download_upvoted(self, args):
        output_path = args.o

        for username in args.users:
            user = self.reddit.redditor(name=username)

            self.logger.notice("Downloading from /u/" + username + "/upvoted")

            root_dir = os.path.join(os.path.join(os.path.join(
                output_path, "www.reddit.com"), "u"), username)

            try:
                post_limit = args.l
                skip_meta = args.skip_meta
                skip_videos = args.skip_videos
                skip_comments = args.skip_comments
                comment_limit = 0 # top-level comments ONLY

                upvoted_dir = os.path.join(root_dir, "upvoted")
                if not os.path.exists(upvoted_dir):
                    os.makedirs(upvoted_dir)

                for i, s in enumerate(user.upvoted(limit=post_limit)):
                    prefix_str = '#' + str(i).zfill(3) + ' '
                    self.indent_1 = ' ' * len(prefix_str) + "* "
                    self.indent_2 = ' ' * len(self.indent_1) + "- "
                    SubmissionDownloader(s, i, self.logger, upvoted_dir, skip_videos, skip_meta, skip_comments, comment_limit,
                                            {'imgur_client_id': UserDownloader.IMGUR_CLIENT_ID})
            except Exception as e:
                self.logger.error("Unable to download upvoted posts for user `" + username + "` - " + str(e))

    def download_saved(self, args):
        output_path = args.o

        for username in args.users:
            user = self.reddit.redditor(name=username)

            self.logger.notice("Downloading from /u/" + username + "/saved")

            root_dir = os.path.join(os.path.join(os.path.join(
                output_path, "www.reddit.com"), "u"), username)

            try:
                post_limit = args.l
                skip_meta = args.skip_meta
                skip_videos = args.skip_videos
                skip_comments = args.skip_comments
                comment_limit = 0 # top-level comments ONLY

                saved_dir = os.path.join(root_dir, "saved")
                if not os.path.exists(saved_dir):
                    os.makedirs(saved_dir)

                for i, s in enumerate(user.saved(limit=post_limit)):
                    prefix_str = '#' + str(i).zfill(3) + ' '
                    self.indent_1 = ' ' * len(prefix_str) + "* "
                    self.indent_2 = ' ' * len(self.indent_1) + "- "
                    if isinstance(s, praw.models.Comment) and not skip_comments:
                        self.logger.verbose(
                            prefix_str + "Comment `" + str(s.id) + "` by " + str(s.author) + " \"" + s.body[0:32].replace("\n", "").replace("\r", "") + "...\"")

                        comment_body = s.body
                        comment_body = comment_body[0:32]
                        comment_body = re.sub(r'\W+', '_', comment_body)
                        post_dir = str(i).zfill(3) + "_Comment_" + \
                            comment_body + "..."
                        submission_dir = os.path.join(saved_dir, post_dir)
                        self.download_saved_comment(s, submission_dir)
                    elif isinstance(s, praw.models.Comment):
                        self.logger.verbose(
                            prefix_str + "Comment `" + str(s.id) + "` by " + str(s.author))
                        self.logger.spam(self.indent_2 + "Skipping comment")
                    elif isinstance(s, praw.models.Submission):
                        SubmissionDownloader(s, i, self.logger, saved_dir, skip_videos, skip_meta, skip_comments, comment_limit,
                                            {'imgur_client_id': UserDownloader.IMGUR_CLIENT_ID})
                    else:
                        pass
            except Exception as e:
                self.logger.error("Unable to download saved for user `" + username + "` - " + str(e))

    def download_gilded(self, args):
        output_path = args.o

        for username in args.users:
            user = self.reddit.redditor(name=username)

            self.logger.notice("Downloading from /u/" + username + "/gilded")

            root_dir = os.path.join(os.path.join(os.path.join(
                output_path, "www.reddit.com"), "u"), username)

            try:
                post_limit = args.l
                skip_meta = args.skip_meta
                skip_videos = args.skip_videos
                skip_comments = args.skip_comments
                comment_limit = 0 # top-level comments ONLY

                saved_dir = os.path.join(root_dir, "gilded")
                if not os.path.exists(saved_dir):
                    os.makedirs(saved_dir)

                for i, s in enumerate(user.gilded(limit=post_limit)):
                    prefix_str = '#' + str(i).zfill(3) + ' '
                    self.indent_1 = ' ' * len(prefix_str) + "* "
                    self.indent_2 = ' ' * len(self.indent_1) + "- "
                    if isinstance(s, praw.models.Comment) and not skip_comments:
                        self.logger.verbose(
                            prefix_str + "Comment `" + str(s.id) + "` by " + str(s.author) + " \"" + s.body[0:32].replace("\n", "").replace("\r", "") + "...\"")

                        comment_body = s.body
                        comment_body = comment_body[0:32]
                        comment_body = re.sub(r'\W+', '_', comment_body)
                        post_dir = str(i).zfill(3) + "_Comment_" + \
                            comment_body + "..."
                        submission_dir = os.path.join(saved_dir, post_dir)
                        self.download_saved_comment(s, submission_dir)
                    elif isinstance(s, praw.models.Comment):
                        self.logger.verbose(
                            prefix_str + "Comment `" + str(s.id) + "` by " + str(s.author))
                        self.logger.spam(self.indent_2 + "Skipping comment")
                    elif isinstance(s, praw.models.Submission):
                        SubmissionDownloader(s, i, self.logger, saved_dir, skip_videos, skip_meta, skip_comments, comment_limit,
                                            {'imgur_client_id': UserDownloader.IMGUR_CLIENT_ID})
                    else:
                        pass
            except Exception as e:
                self.logger.error("Unable to download gilded for user `" + username + "` - " + str(e))

    def print_formatted_error(self, e):
        for line in str(e).split("\n"):
            self.logger.error(self.indent_2 + line)

    def download_saved_comment(self, comment, output_dir):
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        self.logger.spam(
            self.indent_2 + "Saving comment.json to " + output_dir)
        with open(os.path.join(output_dir, 'comments.json'), 'w') as file:
            comment_dict = {}
            try:
                if comment.author:
                    comment_dict["author"] = comment.author.name
                else:
                    comment_dict["author"] = None
                comment_dict["body"] = comment.body
                comment_dict["created_utc"] = int(comment.created_utc)
                comment_dict["distinguished"] = comment.distinguished
                comment_dict["downs"] = comment.downs
                comment_dict["edited"] = comment.edited
                comment_dict["id"] = comment.id
                comment_dict["is_submitter"] = comment.is_submitter
                comment_dict["link_id"] = comment.link_id
                comment_dict["parent_id"] = comment.parent_id
                comment_dict["permalink"] = comment.permalink
                comment_dict["score"] = comment.score
                comment_dict["stickied"] = comment.stickied
                comment_dict["subreddit_name_prefixed"] = comment.subreddit_name_prefixed
                comment_dict["subreddit_id"] = comment.subreddit_id
                comment_dict["total_awards_received"] = comment.total_awards_received
                comment_dict["ups"] = comment.ups
                file.write(json.dumps(comment_dict, indent=2))
                self.logger.spam(
                    self.indent_2 + "Successfully saved comment.json")
            except Exception as e:
                self.print_formatted_error(e)