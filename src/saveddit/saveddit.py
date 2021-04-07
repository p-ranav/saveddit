import argparse
from saveddit.subreddit_downloader import SubredditDownloader
import sys


def asciiart():
    return r'''                                .___  .___.__  __
   ___________ ___  __ ____   __| _/__| _/|__|/  |_
  /  ___/\__  \\  \/ // __ \ / __ |/ __ | |  \   __\
  \___ \  / __ \\   /\  ___// /_/ / /_/ | |  ||  |
 /____  >(____  /\_/  \___  >____ \____ | |__||__|
      \/      \/          \/     \/    \/

 Downloader for Reddit
 version : v1.0.0
 URL     : https://github.com/p-ranav/saveddit
'''


def check_positive(value):
    ivalue = int(value)
    if ivalue <= 0:
        raise argparse.ArgumentTypeError(
            "%s is an invalid positive int value" % value)
    return ivalue

def main():
    print(asciiart())
    argv = sys.argv[1:]

    parser = argparse.ArgumentParser(prog="saveddit")
    parser.add_argument('-r',
                        metavar='subreddits',
                        nargs='+',
                        required=True,
                        help='Names of subreddits to download, e.g., AskReddit')
    parser.add_argument('-f',
                        metavar='categories',
                        default=SubredditDownloader.DEFAULT_CATEGORIES,
                        nargs='+',
                        help='Categories of posts to download (default: %(default)s)')
    parser.add_argument('-l',
                        default=SubredditDownloader.DEFAULT_POST_LIMIT,
                        metavar='post_limit',
                        type=check_positive,
                        help='Limit the number of submissions downloaded in each category (default: %(default)s, i.e., all submissions)')
    parser.add_argument('--skip-comments',
                        default=False,
                        action='store_true',
                        help='When true, saveddit will not save comments to a comments.json file')
    parser.add_argument('--skip-meta',
                        default=False,
                        action='store_true',
                        help='When true, saveddit will not save meta to a submission.json file')
    parser.add_argument('--skip-videos',
                        default=False,
                        action='store_true',
                        help='When true, saveddit will not download videos (e.g., gfycat, redgifs, youtube, v.redd.it links)')
    parser.add_argument('-o',
                        required=True,
                        type=str,
                        metavar='output_path',
                        help='Directory where saveddit will save downloaded content'
                        )
    args = parser.parse_args(argv)
    for subreddit in args.r:
        downloader = SubredditDownloader(subreddit)
        downloader.download(args.o,
                            categories=args.f, post_limit=args.l, skip_videos=args.skip_videos, skip_meta=args.skip_meta, skip_comments=args.skip_comments)

if __name__ == "__main__":
    main()