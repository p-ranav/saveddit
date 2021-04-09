import argparse
from saveddit.subreddit_downloader import SubredditDownloader
from saveddit.user_downloader import UserDownloader
import sys


def asciiart():
    return r'''                                .___  .___.__  __
   ___________ ___  __ ____   __| _/__| _/|__|/  |_
  /  ___/\__  \\  \/ // __ \ / __ |/ __ | |  \   __\
  \___ \  / __ \\   /\  ___// /_/ / /_/ | |  ||  |
 /____  >(____  /\_/  \___  >____ \____ | |__||__|
      \/      \/          \/     \/    \/

 Downloader for Reddit
 version : v2.0.3
 URL     : https://github.com/p-ranav/saveddit
'''


def check_positive(value):
    ivalue = int(value)
    if ivalue <= 0:
        raise argparse.ArgumentTypeError(
            "%s is an invalid positive int value" % value)
    return ivalue

class UniqueAppendAction(argparse.Action):
    '''
    Class used to discard duplicates in list arguments
    https://stackoverflow.com/questions/9376670/python-argparse-force-a-list-item-to-be-unique
    '''
    def __call__(self, parser, namespace, values, option_string=None):
        unique_values = set(values)
        setattr(namespace, self.dest, unique_values)

def main():
    print(asciiart())
    argv = sys.argv[1:]

    parser = argparse.ArgumentParser(prog="saveddit")
    subparsers = parser.add_subparsers(dest="subparser_name")

    subreddit_parser = subparsers.add_parser('subreddit')
    subreddit_parser.add_argument('subreddits',
                        metavar='subreddits',
                        nargs='+',
                        action=UniqueAppendAction,
                        help='Names of subreddits to download, e.g., AskReddit')
    subreddit_parser.add_argument('-f',
                        metavar='categories',
                        default=SubredditDownloader.DEFAULT_CATEGORIES,
                        nargs='+',
                        action=UniqueAppendAction,
                        help='Categories of posts to download (default: %(default)s)')
    subreddit_parser.add_argument('-l',
                        default=SubredditDownloader.DEFAULT_POST_LIMIT,
                        metavar='post_limit',
                        type=check_positive,
                        help='Limit the number of submissions downloaded in each category (default: %(default)s, i.e., all submissions)')
    subreddit_parser.add_argument('--skip-comments',
                        default=False,
                        action='store_true',
                        help='When true, saveddit will not save comments to a comments.json file')
    subreddit_parser.add_argument('--skip-meta',
                        default=False,
                        action='store_true',
                        help='When true, saveddit will not save meta to a submission.json file on submissions')
    subreddit_parser.add_argument('--skip-videos',
                        default=False,
                        action='store_true',
                        help='When true, saveddit will not download videos (e.g., gfycat, redgifs, youtube, v.redd.it links)')
    subreddit_parser.add_argument('-o',
                        required=True,
                        type=str,
                        metavar='output_path',
                        help='Directory where saveddit will save downloaded content'
                        )

    user_parser = subparsers.add_parser('user')
    user_parser.add_argument('users',
                        metavar='users',
                        nargs='+',
                        help='Names of users to download, e.g., Poem_for_your_sprog')


    user_subparsers = user_parser.add_subparsers(dest="user_subparser_name")
    user_subparsers.required = True

    # user.saved subparser
    saved_parser = user_subparsers.add_parser('saved')
    saved_parser.add_argument('--skip-meta',
                        default=False,
                        action='store_true',
                        help='When true, saveddit will not save meta to a submission.json file on submissions')
    saved_parser.add_argument('--skip-comments',
                        default=False,
                        action='store_true',
                        help='When true, saveddit will not save comments to a comments.json file')
    saved_parser.add_argument('--skip-videos',
                        default=False,
                        action='store_true',
                        help='When true, saveddit will not download videos (e.g., gfycat, redgifs, youtube, v.redd.it links)')
    saved_parser.add_argument('-l',
                        default=UserDownloader.DEFAULT_POST_LIMIT,
                        metavar='post_limit',
                        type=check_positive,
                        help='Limit the number of saved submissions downloaded (default: %(default)s, i.e., all submissions)')
    saved_parser.add_argument('-o',
                        required=True,
                        type=str,
                        metavar='output_path',
                        help='Directory where saveddit will save downloaded content'
                        )

    # user.gilded subparser
    gilded_parser = user_subparsers.add_parser('gilded')
    gilded_parser.add_argument('--skip-meta',
                        default=False,
                        action='store_true',
                        help='When true, saveddit will not save meta to a submission.json file on submissions')
    gilded_parser.add_argument('--skip-comments',
                        default=False,
                        action='store_true',
                        help='When true, saveddit will not save comments to a comments.json file')
    gilded_parser.add_argument('--skip-videos',
                        default=False,
                        action='store_true',
                        help='When true, saveddit will not download videos (e.g., gfycat, redgifs, youtube, v.redd.it links)')
    gilded_parser.add_argument('-l',
                        default=UserDownloader.DEFAULT_POST_LIMIT,
                        metavar='post_limit',
                        type=check_positive,
                        help='Limit the number of saved submissions downloaded (default: %(default)s, i.e., all submissions)')
    gilded_parser.add_argument('-o',
                        required=True,
                        type=str,
                        metavar='output_path',
                        help='Directory where saveddit will save downloaded content'
                        )

    # user.submitted subparser
    submitted_parser = user_subparsers.add_parser('submitted')
    submitted_parser.add_argument('-s',
                        metavar='sort',
                        default=UserDownloader.DEFAULT_SORT,
                        choices=UserDownloader.DEFAULT_SORT_OPTIONS,
                        help='Download submissions sorted by this <sort> option (default: %(default)s, choices: [%(choices)s])')
    submitted_parser.add_argument('--skip-comments',
                        default=False,
                        action='store_true',
                        help='When true, saveddit will not save comments to a comments.json file for the submissions')
    submitted_parser.add_argument('--skip-meta',
                        default=False,
                        action='store_true',
                        help='When true, saveddit will not save meta to a submission.json file on submissions')
    submitted_parser.add_argument('--skip-videos',
                        default=False,
                        action='store_true',
                        help='When true, saveddit will not download videos (e.g., gfycat, redgifs, youtube, v.redd.it links)')
    submitted_parser.add_argument('-l',
                        default=UserDownloader.DEFAULT_POST_LIMIT,
                        metavar='post_limit',
                        type=check_positive,
                        help='Limit the number of submissions downloaded (default: %(default)s, i.e., all submissions)')
    submitted_parser.add_argument('-o',
                        required=True,
                        type=str,
                        metavar='output_path',
                        help='Directory where saveddit will save downloaded posts'
                        )

    # user.upvoted subparser
    upvoted_parser = user_subparsers.add_parser('upvoted')
    upvoted_parser.add_argument('--skip-comments',
                        default=False,
                        action='store_true',
                        help='When true, saveddit will not save comments to a comments.json file for the upvoted submissions')
    upvoted_parser.add_argument('--skip-meta',
                        default=False,
                        action='store_true',
                        help='When true, saveddit will not save meta to a submission.json file on upvoted submissions')
    upvoted_parser.add_argument('--skip-videos',
                        default=False,
                        action='store_true',
                        help='When true, saveddit will not download videos (e.g., gfycat, redgifs, youtube, v.redd.it links)')
    upvoted_parser.add_argument('-l',
                        default=UserDownloader.DEFAULT_POST_LIMIT,
                        metavar='post_limit',
                        type=check_positive,
                        help='Limit the number of submissions downloaded (default: %(default)s, i.e., all submissions)')
    upvoted_parser.add_argument('-o',
                        required=True,
                        type=str,
                        metavar='output_path',
                        help='Directory where saveddit will save downloaded posts'
                        )

    # user.comments subparser
    comments_parser = user_subparsers.add_parser('comments')
    comments_parser.add_argument('-s',
                        metavar='sort',
                        default=UserDownloader.DEFAULT_SORT,
                        choices=UserDownloader.DEFAULT_SORT_OPTIONS,
                        help='Download comments sorted by this <sort> option (default: %(default)s, choices: [%(choices)s])')
    comments_parser.add_argument('-l',
                        default=UserDownloader.DEFAULT_COMMENT_LIMIT,
                        metavar='post_limit',
                        type=check_positive,
                        help='Limit the number of comments downloaded (default: %(default)s, i.e., all comments)')
    comments_parser.add_argument('-o',
                        required=True,
                        type=str,
                        metavar='output_path',
                        help='Directory where saveddit will save downloaded comments'
                        )

    args = parser.parse_args(argv)

    if args.subparser_name == "subreddit":
        for subreddit in args.subreddits:
            downloader = SubredditDownloader(subreddit)
            downloader.download(args.o,
                                categories=args.f, post_limit=args.l, skip_videos=args.skip_videos, skip_meta=args.skip_meta, skip_comments=args.skip_comments)
    elif args.subparser_name == "user":
        downloader = UserDownloader()
        if args.user_subparser_name == "comments":
            downloader.download_comments(args)
        elif args.user_subparser_name == "submitted":
            downloader.download_submitted(args)
        elif args.user_subparser_name == "saved":
            downloader.download_saved(args)
        elif args.user_subparser_name == "upvoted":
            downloader.download_upvoted(args)
        elif args.user_subparser_name == "gilded":
            downloader.download_gilded(args)

if __name__ == "__main__":
    main()

# saveddit user p_ranav saved --skip-comments --skip-videos -o ~/Desktop
# saveddit user p_ranav submitted --sort hot new controversial top --skip-videos -o ~/Desktop
# saveddit user p_ranav comments --sort hot new controversial top -o ~/Desktop