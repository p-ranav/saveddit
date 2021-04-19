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
import sys
from tqdm import tqdm

class UserDownloader:
    config = SubredditDownloader.config

    REDDIT_CLIENT_ID = config['reddit_client_id']
    REDDIT_CLIENT_SECRET = config['reddit_client_secret']
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

    IMGUR_CLIENT_ID = config['imgur_client_id']

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

        if not UserDownloader.REDDIT_USERNAME:
            self.logger.error("`reddit_username` in user_config.yaml is empty")
            self.logger.error("If you plan on using the user API of saveddit, then add your username to user_config.yaml")
            print("Exiting now")
            exit()
        else:
            if not len(UserDownloader.REDDIT_PASSWORD):
                if sys.stdin.isatty():
                    print("Username: " + UserDownloader.REDDIT_USERNAME)
                    REDDIT_PASSWORD = getpass.getpass("Password: ")
                else:
                    # echo "foobar" > password
                    # saveddit user .... < password
                    REDDIT_PASSWORD = sys.stdin.readline().rstrip()

        self.reddit = praw.Reddit(
            client_id=UserDownloader.REDDIT_CLIENT_ID,
            client_secret=UserDownloader.REDDIT_CLIENT_SECRET,
            user_agent="saveddit (by /u/p_ranav)",
            username=UserDownloader.REDDIT_USERNAME,
            password=UserDownloader.REDDIT_PASSWORD
        )

    def download_user_meta(self, args):
        output_path = args.o

        for username in args.users:
            user = self.reddit.redditor(name=username)

            root_dir = os.path.join(os.path.join(os.path.join(
                output_path, "www.reddit.com"), "u"), username)

            if not os.path.exists(root_dir):
                os.makedirs(root_dir)

            with open(os.path.join(root_dir, 'user.json'), 'w') as file:
                user_dict = {}
                user_dict["comment_karma"] = user.comment_karma
                user_dict["created_utc"] = int(user.created_utc)
                user_dict["has_verified_email"] = user.has_verified_email
                user_dict["icon_img"] = user.icon_img
                user_dict["id"] = user.id
                user_dict["is_employee"] = user.is_employee
                user_dict["is_friend"] = user.is_friend
                user_dict["is_mod"] = user.is_mod
                user_dict["is_gold"] = user.is_gold
                try:
                    user_dict["is_suspended"] = user.is_suspended
                except Exception as e:
                    user_dict["is_suspended"] = None
                user_dict["link_karma"] = user.link_karma
                user_dict["name"] = user.name

                file.write(json.dumps(user_dict, indent=2))

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

    def download_multireddits(self, args):
        output_path = args.o

        for username in args.users:
            user = self.reddit.redditor(name=username)

            root_dir = os.path.join(os.path.join(os.path.join(os.path.join(
                output_path, "www.reddit.com"), "u"), username), "m")

            try:
                post_limit = args.l
                names = args.n
                categories = args.f
                skip_meta = args.skip_meta
                skip_videos = args.skip_videos
                skip_comments = args.skip_comments
                comment_limit = 0 # top-level comments ONLY

                # If names is None, download all multireddits from user's page
                if not names:
                    names = [m.name.lower() for m in user.multireddits()]
                else:
                    names = [n.lower() for n in names]

                for multireddit in user.multireddits():
                    if multireddit.name.lower() in names:
                        name = multireddit.name
                        self.logger.notice("Downloading from /u/" + username + "/m/" + name)
                        multireddit_dir = os.path.join(root_dir, name)
                        if not os.path.exists(multireddit_dir):
                            os.makedirs(multireddit_dir)

                        for category in categories:

                            self.logger.verbose("Downloading submissions sorted by " + category)
                            category_function = getattr(multireddit, category)

                            category_dir = os.path.join(multireddit_dir, category)

                            if category_function:
                                for i, s in enumerate(category_function(limit=post_limit)):
                                    try:
                                        prefix_str = '#' + str(i).zfill(3) + ' '
                                        self.indent_1 = ' ' * len(prefix_str) + "* "
                                        self.indent_2 = ' ' * len(self.indent_1) + "- "
                                        SubmissionDownloader(s, i, self.logger, category_dir, skip_videos, skip_meta, skip_comments, comment_limit,
                                                                {'imgur_client_id': UserDownloader.IMGUR_CLIENT_ID})
                                    except Exception as e:
                                        self.logger.error(self.indent_2 + "Unable to download post #" + str(i) + " for user `" + username + "` from multireddit " + name + " - " + str(e))
            except Exception as e:
                self.logger.error(self.indent_1 + "Unable to download multireddit posts for user `" + username + "` - " + str(e))

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
                        try:
                            prefix_str = '#' + str(i).zfill(3) + ' '
                            self.indent_1 = ' ' * len(prefix_str) + "* "
                            self.indent_2 = ' ' * len(self.indent_1) + "- "
                            SubmissionDownloader(s, i, self.logger, category_dir, skip_videos, skip_meta, skip_comments, comment_limit,
                                                    {'imgur_client_id': UserDownloader.IMGUR_CLIENT_ID})
                        except Exception as e:
                            self.logger.error(self.indent_2 + "Unable to download post #" + str(i) + " for user `" + username + "` - " + str(e))
            except Exception as e:
                self.logger.error(self.indent_1 + "Unable to download submitted posts for user `" + username + "` - " + str(e))

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
                    try:
                        prefix_str = '#' + str(i).zfill(3) + ' '
                        self.indent_1 = ' ' * len(prefix_str) + "* "
                        self.indent_2 = ' ' * len(self.indent_1) + "- "
                        SubmissionDownloader(s, i, self.logger, upvoted_dir, skip_videos, skip_meta, skip_comments, comment_limit,
                                                {'imgur_client_id': UserDownloader.IMGUR_CLIENT_ID})
                    except Exception as e:
                        self.logger.error(self.indent_2 + "Unable to download post #" + str(i) + " for user `" + username + "` - " + str(e))
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
                    try:
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
                        self.logger.error(self.indent_2 + "Unable to download #" + str(i) + " for user `" + username + "` - " + str(e))
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
                    try:
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
                        self.logger.error(self.indent_2 + "Unable to download #" + str(i) + " for user `" + username + "` - " + str(e))
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