import argparse
from saveddit.subreddit_downloader import SubredditDownloader

def main(subreddit_name):
  downloader = SubredditDownloader(subreddit_name)
  downloader.download("/Users/pranav/Downloads/Reddit", category="top", post_limit=10)

if __name__ == "__main__":
  parser = argparse.ArgumentParser(
    prog="saveddit",
    description="Downloader for Reddit")
  parser.add_argument('subreddit', metavar='subreddit', type=str, help='Name of a subreddit, e.g., pics')
  args = parser.parse_args()
  main(args.subreddit)