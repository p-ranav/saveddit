from datetime import datetime
import os
import praw
import re
import urllib.request
from pprint import pprint
from saveddit.imgur_downloader import get_imgur_album_images_count, download_imgur_album, get_imgur_image_meta

def download_subreddit(subreddit_name, output_path, limit=None):
  reddit = praw.Reddit(
    client_id="aCjKJeNwZw_Efg",
    client_secret="1Hul2-xgH_11r6limxcdtnPFQ4V5AQ",
    user_agent="saveddit:v1.0.0 (by /u/p-ranav)",
  )
  subreddit = reddit.subreddit(subreddit_name)

  root_dir = os.path.join(os.path.join(os.path.join(output_path, "www.reddit.com"), "r"), subreddit_name)
  print(root_dir)
  categories = ["hot", "new", "rising", "controversial", "top", "gilded"]
  supported_file_formats = [".png", ".jpg", ".jpeg", ".mp4", ".gif"]

  for c in categories:
    category_dir = os.path.join(root_dir, c)
    if not os.path.exists(category_dir):
      os.makedirs(category_dir)
    category_function = getattr(subreddit, c)

    for i, submission in enumerate(category_function(limit=limit)):
      has_url = getattr(submission, "url", None)
      if has_url:
        filename = str(i).zfill(4) + "_" + submission.url.split("/")[-1]
        if any([i in filename for i in supported_file_formats]) and ".gifv" not in filename:
          save_path = os.path.join(category_dir, filename)
          try:
            urllib.request.urlretrieve(submission.url, save_path)
          except Exception as e:
            pass
        elif "reddit.com/gallery" in submission.url:
          # Reddit gallery
          gallery_id = filename

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
              if "image" in item_format:
                gallery_dir = os.path.join(category_dir, gallery_id)
                if not os.path.exists(gallery_dir):
                  os.makedirs(gallery_dir)
                item_format = item_format.split("image/")[-1] # TODO: Is "video/" a possibility?
                item_filename = str(j).zfill(4) + "_" + media_id + "." + item_format
                item_url = item_metadata["s"]["u"]
                save_path = os.path.join(gallery_dir, item_filename)
                try:
                  urllib.request.urlretrieve(item_url, save_path)
                except Exception as e:
                  print(e)
        elif "gfycat.com/" in submission.url or "redgifs.com/" in submission.url:
          # Gfycat/Redgifs link
          if "reddit_video_preview" in submission.preview:
            if "fallback_url" in submission.preview["reddit_video_preview"]:
              fallback_url = submission.preview["reddit_video_preview"]["fallback_url"]
              file_format = fallback_url.split(".")[-1]
              filename = str(i).zfill(4) + "_" + submission.url.split("/")[-1] + "." + file_format
              save_path = os.path.join(category_dir, filename)
              try:
                urllib.request.urlretrieve(fallback_url, save_path)
              except Exception as e:
                pass
        elif "imgur.com/a/" in submission.url or "imgur.com/gallery/" in submission.url:
          # Imgur album
          album_id = ""
          if "imgur.com/a/" in submission.url:
            album_id = submission.url.split("imgur.com/a/")[-1]
          elif "imgur.com/gallery/" in submission.url:
            album_id = submission.url.split("imgur.com/gallery/")[-1]

          images_count = get_imgur_album_images_count(album_id)
          if images_count > 0:
            album_dir = str(i).zfill(4) + "_" + album_id
            save_path = os.path.join(category_dir, album_dir)
            download_imgur_album(album_id, save_path)
        elif "imgur.com" in submission.url:
          # Other imgur content, e.g., .gifv, '.mp4', '.jpg', etc.
          url_leaf = submission.url.split("/")[-1]
          if "." in url_leaf:
            image_id = url_leaf.split(".")[0]
          else:
            image_id = url_leaf
          data = get_imgur_image_meta(image_id)
          url = data["link"]
          image_type = data["type"]
          if "video/" in image_type:
            image_type = image_type.split("video/")[-1]
          elif "image/" in image_type:
            image_type = image_type.split("image/")[-1]

          filename = str(i).zfill(4) + "_" + image_id + "." + image_type
          save_path = os.path.join(category_dir, filename)

          try:
            urllib.request.urlretrieve(url, save_path)
          except Exception as e:
            print(e)
        else:
          title = submission.title
          title = title.translate({ord(c): " " for c in "!@#$%^&*()[]{};:,./<>?\|`~-=_+"})
          post_dir = str(i).zfill(4) + "_" + title.replace(" ", "_")
          save_dir = os.path.join(category_dir, post_dir)
          if not os.path.exists(save_dir):
            os.makedirs(save_dir)

          with open(os.path.join(save_dir, 'selftext.txt'), 'w') as selftext_file:
            selftext_file.write(submission.selftext)

          # Save comments - Breath first unwrap of comment forest
          with open(os.path.join(save_dir, 'comments.txt'), 'w') as comment_file:
            submission.comments.replace_more(limit=None)
            count = 0
            for comment in submission.comments.list():
              comment_str = ""
              try:
                if count > 0:
                  comment_str += "\n"
                comment_timestamp = datetime.utcfromtimestamp(comment.created_utc).strftime('%Y.%m.%d %H:%M:%S')
                comment_str += "[" + comment.author.name + "] " + str(comment.score) + " points " + str(comment_timestamp) + "\n"
                comment_str += comment.body + "\n"
              except Exception as e:
                pass
              comment_file.write(comment_str)
              count += 1

download_subreddit("CasualConversation", "/Users/pranav/Downloads/Reddit/")