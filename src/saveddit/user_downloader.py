import coloredlogs
from colorama import Fore, Style
import logging
import verboselogs
import json
import os
import praw
from pprint import pprint
from saveddit.submission_downloader import SubmissionDownloader
from saveddit.configuration import ConfigurationLoader


class UserDownloader():
    app_config_dir = os.path.expanduser("~/.saveddit")
    if not os.path.exists(app_config_dir):
        os.makedirs(app_config_dir)

    config_file_location = os.path.expanduser("~/.saveddit/user_config.yaml")
    config = ConfigurationLoader.load(config_file_location)

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
    DEFAULT_POST_LIMIT = None

    def __init__(self, username):
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

        reddit = praw.Reddit(
            client_id=UserDownloader.REDDIT_CLIENT_ID,
            client_secret=UserDownloader.REDDIT_CLIENT_SECRET,
            user_agent="saveddit (by /u/p_ranav)",
            username=UserDownloader.REDDIT_USERNAME,
            password=UserDownloader.REDDIT_PASSWORD
        )
        self.username = username
        self.user = reddit.redditor(name=username)

    def download(self, output_path, post_limit=DEFAULT_POST_LIMIT, skip_videos=False, skip_meta=False, skip_comments=False, comment_limit=0):

        self.logger.notice("Downloading from /user/" + self.username)

        root_dir = os.path.join(os.path.join(os.path.join(
            output_path, "www.reddit.com"), "user"), self.username)

        # Try and download submissions
        try:
            self.download_submissions(root_dir, post_limit, skip_videos, skip_meta, skip_comments, comment_limit)
        except Exception as e:
            self.logger.error("Unable to download submissions for user `" + self.username + "` - " + str(e))

        # Try and download saved posts
        try:
            self.download_saved_posts(root_dir, post_limit, skip_videos, skip_meta, skip_comments, comment_limit)
        except Exception as e:
            self.logger.error("Unable to download saved posts/comments for user `" + self.username + "` - " + str(e))

    def download_submissions(self, output_path, post_limit, skip_videos, skip_meta, skip_comments, comment_limit):
        submissions_dir = os.path.join(output_path, "submissions")
        if not os.path.exists(submissions_dir):
            os.makedirs(submissions_dir)

        self.logger.notice("Downloading from /user/" + self.username + "/submissions/")

        categories = [ "hot", "new", "top", "controversial"]

        for c in categories:
            self.logger.verbose("Downloading submissions sorted by " + c)
            category_function = getattr(self.user.submissions, c)

            category_dir = os.path.join(submissions_dir, c)

            if category_function:
                for i, s in enumerate(category_function(limit=post_limit)):
                    prefix_str = '#' + str(i) + ' '
                    self.indent_1 = ' ' * len(prefix_str) + "* "
                    self.indent_2 = ' ' * len(self.indent_1) + "- "
                    SubmissionDownloader(s, i, self.logger, category_dir, skip_videos, skip_meta, skip_comments, comment_limit,
                                            {'imgur_client_id': UserDownloader.IMGUR_CLIENT_ID})

    def download_saved_posts(self, output_path, post_limit, skip_videos, skip_meta, skip_comments, comment_limit):
        saved_dir = os.path.join(output_path, "saved")
        if not os.path.exists(saved_dir):
            os.makedirs(saved_dir)

        for i, s in enumerate(self.user.saved(limit=post_limit)):
            prefix_str = '#' + str(i) + ' '
            self.indent_1 = ' ' * len(prefix_str) + "* "
            self.indent_2 = ' ' * len(self.indent_1) + "- "
            if isinstance(s, praw.models.Comment) and not skip_comments:
                self.logger.verbose(
                    prefix_str + "Comment `" + str(s.id) + "` by " + str(s.author))
                post_dir = str(i).zfill(4) + "_Comment_" + \
                    str(s.id) + "_by_" + str(s.author)
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