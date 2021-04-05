import argparse
from saveddit.subreddit_downloader import SubredditDownloader

def main(args):
  downloader = SubredditDownloader(args.subreddit)
  downloader.download("/Users/pranav/Downloads/Reddit", categories=args.categories, post_limit=10)

if __name__ == "__main__":
  parser = argparse.ArgumentParser(
    prog="saveddit",
    description="Downloader for Reddit")
  parser.add_argument('subreddit', metavar='subreddit', type=str, help='Name of a subreddit, e.g., AskReddit')
  parser.add_argument('--categories',
                      default=SubredditDownloader.DEFAULT_CATEGORIES,
                      nargs='+',
                      help='Categories of posts to download (default: %(default)s)')
  args = parser.parse_args()
  main(args)