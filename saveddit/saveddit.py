import argparse
from saveddit.subreddit_downloader import SubredditDownloader

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
    raise argparse.ArgumentTypeError("%s is an invalid positive int value" % value)
  return ivalue

def main(args):
  downloader = SubredditDownloader(args.subreddit)
  downloader.download("/Users/pranav/Downloads/Reddit", categories=args.categories, post_limit=args.post_limit)

if __name__ == "__main__":
  print(asciiart())

  parser = argparse.ArgumentParser(prog="saveddit")
  parser.add_argument('subreddit', metavar='subreddit', type=str, help='Name of a subreddit, e.g., AskReddit')
  parser.add_argument('-c', '--categories',
                      default=SubredditDownloader.DEFAULT_CATEGORIES,
                      nargs='+',
                      help='Categories of posts to download (default: %(default)s)')
  parser.add_argument('-pl', '--post-limit',
                      default=SubredditDownloader.DEFAULT_POST_LIMIT,
                      metavar='post_limit',
                      type=check_positive,
                      help='Limit the number of submissions downloaded in each category (default: %(default)s, i.e., all submissions)')
  args = parser.parse_args()
  main(args)