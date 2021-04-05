import coloredlogs, logging, verboselogs
from datetime import datetime
import os
import json
import ffmpeg
import praw
from pprint import pprint
import re
import requests
import urllib.request

class SubredditDownloader:
  REDDIT_CLIENT_ID = "aCjKJeNwZw_Efg"
  REDDIT_CLIENT_SECRET="1Hul2-xgH_11r6limxcdtnPFQ4V5AQ"
  IMGUR_CLIENT_ID = "33982ca3205a4a2"
  DEFAULT_CATEGORIES=["hot", "new", "rising", "controversial", "top", "gilded"]

  def __init__(self, subreddit_name):
    self.subreddit_name = subreddit_name
    reddit = praw.Reddit(
      client_id=SubredditDownloader.REDDIT_CLIENT_ID,
      client_secret=SubredditDownloader.REDDIT_CLIENT_SECRET,
      user_agent="saveddit:v1.0.0 (by /u/p_ranav)",
    )
    self.subreddit = reddit.subreddit(subreddit_name)

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
    coloredlogs.install(level='SPAM', logger=self.logger, fmt='%(message)s', level_styles=level_styles)

  def download(self, output_path, categories=DEFAULT_CATEGORIES, post_limit=None, comment_limit=0):
    '''
    categories: List of categories within the subreddit to download (see SubredditDownloader.DEFAULT_CATEGORIES)
    post_limit: Number of posts to download (default: None, i.e., all posts)
    comment_limit: Number of comment levels to download from submission (default: `0`, i.e., only top-level comments)
      - to get all comments, set comment_limit to `None`
    '''
    root_dir = os.path.join(os.path.join(os.path.join(output_path, "www.reddit.com"), "r"), self.subreddit_name)
    categories = categories

    for c in categories:
      self.logger.notice("Downloading from /r/" + self.subreddit_name + "/" + c + "/")
      category_dir = os.path.join(root_dir, c)
      if not os.path.exists(category_dir):
        os.makedirs(category_dir)
      category_function = getattr(self.subreddit, c)

      for i, submission in enumerate(category_function(limit=post_limit)):
        has_url = getattr(submission, "url", None)
        if has_url:
          title = submission.title
          title = title.translate({ord(c): " " for c in "!@#$%^&*()[]{};:,./<>?\|`~-=_+"})

          # Truncate title
          if len(title) > 127:
            title = title[0:124]
            title += "..."

          # Prepare directory for the submission
          post_dir = str(i).zfill(4) + "_" + title.replace(" ", "_")
          submission_dir = os.path.join(category_dir, post_dir)
          if not os.path.exists(submission_dir):
            os.makedirs(submission_dir)

          self.logger.spam("#" + str(i) + " Processing `" + submission.url + "`")

          success = False

          if self.is_direct_link_to_content(submission.url, [".png", ".jpg", ".jpeg", ".mp4", ".gif"]):
            files_dir = os.path.join(submission_dir, "files")
            if not os.path.exists(files_dir):
              os.makedirs(files_dir)

            filename = submission.url.split("/")[-1]
            self.logger.spam("#" + str(i) + " This is a direct link to a " + filename.split(".")[-1] + " file")
            save_path = os.path.join(files_dir, filename)
            self.download_direct_link(submission, save_path)
            success = True
          elif self.is_reddit_gallery(submission.url):
            self.logger.spam("#" + str(i) + " This is a reddit gallery")
            gallery_dir = "gallery"
            self.download_reddit_gallery(submission, os.path.join(submission_dir, gallery_dir))
            success = True
          elif self.is_reddit_video(submission.url):
            files_dir = os.path.join(submission_dir, "files")
            if not os.path.exists(files_dir):
              os.makedirs(files_dir)

            self.logger.spam("#" + str(i) + " This is a reddit video")
            self.download_reddit_video(submission, files_dir)
            success = True
          elif self.is_gfycat_link(submission.url) or self.is_redgifs_link(submission.url):
            if self.is_gfycat_link(submission.url):
              self.logger.spam("#" + str(i) + " This is a gfycat link")
            else:
              self.logger.spam("#" + str(i) + " This is a redgif link")
            self.download_gfycat_or_redgif(submission, submission_dir)
            success = True
          elif self.is_imgur_album(submission.url):
            self.logger.spam("#" + str(i) + " This is an imgur album")
            self.download_imgur_album(submission, submission_dir)
            success = True
          elif self.is_imgur_image(submission.url):
            self.logger.spam("#" + str(i) + " This is an imgur image or video")
            self.download_imgur_image(submission, submission_dir)
            success = True
          elif self.is_self_post(submission):
            self.logger.spam("#" + str(i) + " This is a self-post")
            success = True
          else:
            success = True

          # Download selftext and submission meta
          self.logger.spam("#" + str(i) + " Saving submission.json")
          self.download_submission_meta(submission, submission_dir)

          # Downlaod comments if requested
          if comment_limit == None:
            self.logger.spam("#" + str(i) + " Saving all comments to comments.json")
          else:
            self.logger.spam("#" + str(i) + " Saving top-level comments to comments.json")
          self.download_comments(submission, submission_dir, comment_limit)

          if success:
            self.logger.success("#" + str(i) + " Saved to " + submission_dir)

  def is_direct_link_to_content(self, url, supported_file_formats):
    url_leaf = url.split("/")[-1]
    return any([i in url_leaf for i in supported_file_formats]) and ".gifv" not in url_leaf

  def download_direct_link(self, submission, output_path):
    try:
      urllib.request.urlretrieve(submission.url, output_path)
    except Exception as e:
      self.logger.error(e)

  def is_reddit_gallery(self, url):
    return "reddit.com/gallery" in url

  def download_reddit_gallery(self, submission, output_path):
    gallery_data = getattr(submission, "gallery_data", None)
    media_metadata = getattr(submission, "media_metadata", None)

    if gallery_data == None and media_metadata == None:
      # gallery_data not in submission
      # could be a crosspost
      crosspost_parent_list = getattr(submission, "crosspost_parent_list", None)
      if crosspost_parent_list != None:
        first_parent = crosspost_parent_list[0]
        gallery_data = first_parent["gallery_data"]
        media_metadata = first_parent["media_metadata"]

    if gallery_data != None and media_metadata != None:
      for j, item in enumerate(gallery_data["items"]):
        media_id = item["media_id"]
        item_metadata = media_metadata[media_id]
        item_format = item_metadata['m']
        if "image/" in item_format or "video/" in item_format:
          if not os.path.exists(output_path):
            os.makedirs(output_path)
          if "image/" in item_format:
            item_format = item_format.split("image/")[-1]
          elif "video/" in item_format:
            item_format = item_format.split("video/")[-1]
          item_filename = media_id + "." + item_format
          item_url = item_metadata["s"]["u"]
          save_path = os.path.join(output_path, item_filename)
          try:
            urllib.request.urlretrieve(item_url, save_path)
          except Exception as e:
            print(e)

  def is_reddit_video(self, url):
    return "v.redd.it" in url

  def download_reddit_video(self, submission, output_path):
    media = getattr(submission, "media", None)
    media_id = submission.url.split("v.redd.it/")[-1]

    if media == None:
      # link might be a crosspost
      crosspost_parent_list = getattr(submission, "crosspost_parent_list", None)
      if crosspost_parent_list != None:
        first_parent = crosspost_parent_list[0]
        media = first_parent["media"]

    if media != None:
      self.logger.spam("   - Downloading video component")
      url = media["reddit_video"]["fallback_url"]
      video_save_path = os.path.join(output_path, media_id + "_video.mp4")
      try:
        urllib.request.urlretrieve(url, video_save_path)
      except Exception as e:
        print(e)

      # Download the audio
      self.logger.spam("   - Downloading audio component")
      audio_downloaded = False
      audio_save_path = os.path.join(output_path, media_id + "_audio.mp4")
      try:
        urllib.request.urlretrieve(submission.url + "/DASH_audio.mp4", audio_save_path)
        audio_downloaded = True
      except Exception as e:
        pass

      if audio_downloaded == True:
        # Merge mp4 files
        self.logger.spam("   - Merging video & audio components with ffmpeg")
        output_save_path = os.path.join(output_path, media_id + ".mp4")
        input_video = ffmpeg.input(video_save_path)
        input_audio = ffmpeg.input(audio_save_path)
        ffmpeg.concat(input_video, input_audio, v=1, a=1)\
          .output(output_save_path)\
            .global_args('-loglevel', 'error')\
              .global_args('-y')\
                .run()
        self.logger.spam("  - Done merging with ffmpeg")

  def is_gfycat_link(self, url):
    return "gfycat.com/" in url

  def is_redgifs_link(self, url):
    return "redgifs.com/" in url

  def download_gfycat_or_redgif(self, submission, output_dir):
    if "reddit_video_preview" in submission.preview:
      if "fallback_url" in submission.preview["reddit_video_preview"]:
        fallback_url = submission.preview["reddit_video_preview"]["fallback_url"]
        file_format = fallback_url.split(".")[-1]
        filename = submission.url.split("/")[-1] + "." + file_format
        save_path = os.path.join(output_dir, filename)
        try:
          urllib.request.urlretrieve(fallback_url, save_path)
        except Exception as e:
          self.logger.error(e)

  def is_imgur_album(self, url):
    return "imgur.com/a/" in url or "imgur.com/gallery/" in url

  def get_imgur_album_images_count(self, album_id):
    request = "https://api.imgur.com/3/album/" + album_id
    res = requests.get(request, headers={"Authorization": "Client-ID " + SubredditDownloader.IMGUR_CLIENT_ID})
    if res.status_code == 200:
      return res.json()["data"]["images_count"]
    else:
      return 0

  def get_imgur_image_meta(self, image_id):
    request = "https://api.imgur.com/3/image/" + image_id
    res = requests.get(request, headers={"Authorization": "Client-ID " + SubredditDownloader.IMGUR_CLIENT_ID})
    return res.json()["data"]

  def download_imgur_album(self, submission, output_dir):
    # Imgur album
    album_id = ""
    if "imgur.com/a/" in submission.url:
      album_id = submission.url.split("imgur.com/a/")[-1]
    elif "imgur.com/gallery/" in submission.url:
      album_id = submission.url.split("imgur.com/gallery/")[-1]

    images_count = self.get_imgur_album_images_count(album_id)
    if images_count > 0:
      album_dir = os.path.join(output_dir, "gallery")
      request = "https://api.imgur.com/3/album/" + album_id
      res = requests.get(request, headers={"Authorization": "Client-ID " + SubredditDownloader.IMGUR_CLIENT_ID})
      for i, image in enumerate(res.json()["data"]["images"]):
        url = image["link"]
        filename = str(i).zfill(4) + "_" + url.split("/")[-1]
        save_path = os.path.join(album_dir, filename)
        try:
          if not os.path.exists(album_dir):
            os.makedirs(album_dir)
          urllib.request.urlretrieve(url, save_path)
        except Exception as e:
          print(e)

  def is_imgur_image(self, url):
    return "imgur.com" in url

  def download_imgur_image(self, submission, output_dir):
    # Other imgur content, e.g., .gifv, '.mp4', '.jpg', etc.
    url_leaf = submission.url.split("/")[-1]
    if "." in url_leaf:
      image_id = url_leaf.split(".")[0]
    else:
      image_id = url_leaf
    data = self.get_imgur_image_meta(image_id)
    url = data["link"]
    image_type = data["type"]
    if "video/" in image_type:
      image_type = image_type.split("video/")[-1]
    elif "image/" in image_type:
      image_type = image_type.split("image/")[-1]

    filename = image_id + "." + image_type
    save_path = os.path.join(output_dir, filename)

    try:
      urllib.request.urlretrieve(url, save_path)
    except Exception as e:
      print(e)

  def download_comments(self, submission, output_dir, comment_limit):
    # Save comments - Breath first unwrap of comment forest
    comments_list = []
    with open(os.path.join(output_dir, 'comments.json'), 'w') as file:
      submission.comments.replace_more(limit=comment_limit)
      for comment in submission.comments.list():
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
          comment_dict["total_awards_received"] = comment_dict.total_awards_received
          comment_dict["ups"] = comment.ups
          comment_dict["upvote_ratio"] = comment.upvote_ratio
        except Exception as e:
          pass
        comments_list.append(comment_dict)
      file.write(json.dumps(comments_list, indent=2))

  def is_self_post(self, submission):
    return submission.is_self

  def download_submission_meta(self, submission, submission_dir):
    submission_dict = {}
    if submission.author:
      submission_dict["author"] = submission.author.name
    submission_dict["author"] = None
    submission_dict["created_utc"] = int(submission.created_utc)
    submission_dict["distinguished"] = submission.distinguished
    submission_dict["downs"] = submission.downs
    submission_dict["edited"] = submission.edited
    submission_dict["id"] = submission.id
    submission_dict["link_flair_text"] = submission.link_flair_text
    submission_dict["locked"] = submission.locked
    submission_dict["num_comments"] = submission.num_comments
    submission_dict["num_crossposts"] = submission.num_crossposts
    submission_dict["permalink"] = submission.permalink
    submission_dict["selftext"] = submission.selftext
    submission_dict["selftext"] = submission.selftext
    submission_dict["selftext_html"] = submission.selftext_html
    submission_dict["send_replies"] = submission.send_replies
    submission_dict["spoiler"] = submission.spoiler
    submission_dict["stickied"] = submission.stickied
    submission_dict["subreddit_name_prefixed"] = submission.subreddit_name_prefixed
    submission_dict["subreddit_id"] = submission.subreddit_id
    submission_dict["subreddit_subscribers"] = submission.subreddit_subscribers
    submission_dict["subreddit_type"] = submission.subreddit_type
    submission_dict["title"] = submission.title
    submission_dict["total_awards_received"] = submission.total_awards_received
    submission_dict["ups"] = submission.ups
    submission_dict["upvote_ratio"] = submission.upvote_ratio
    submission_dict["url"] = submission.url

    with open(os.path.join(submission_dir, "submission.json"), 'w') as file:
      file.write(json.dumps(submission_dict, indent=2))