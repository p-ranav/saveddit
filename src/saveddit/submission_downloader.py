from bs4 import BeautifulSoup
import coloredlogs
from colorama import Fore
import contextlib
import logging
import verboselogs
from datetime import datetime
import os
from io import StringIO
import json
import mimetypes
import ffmpeg
import praw
from pprint import pprint
import re
import requests
from tqdm import tqdm
import urllib.request
import youtube_dl


class SubmissionDownloader:
    def __init__(self, submission, submission_index, logger, output_dir, skip_videos, skip_meta, skip_comments, comment_limit, config):
        self.IMGUR_CLIENT_ID = config["imgur_client_id"]

        self.logger = logger
        i = submission_index
        prefix_str = '#' + str(i).zfill(3) + ' '
        self.indent_1 = ' ' * len(prefix_str) + "* "
        self.indent_2 = ' ' * len(self.indent_1) + "- "

        has_url = getattr(submission, "url", None)
        if has_url:
            title = submission.title
            self.logger.verbose(prefix_str + '"' + title + '"')
            title = re.sub(r'\W+', '_', title)

            # Truncate title
            if len(title) > 32:
                title = title[0:32]
                title += "..."

            # Prepare directory for the submission
            post_dir = str(i).zfill(3) + "_" + title.replace(" ", "_")
            submission_dir = os.path.join(output_dir, post_dir)
            if not os.path.exists(submission_dir):
                os.makedirs(submission_dir)

            self.logger.spam(
                self.indent_1 + "Processing `" + submission.url + "`")

            success = False

            should_create_files_dir = True
            if skip_comments and skip_meta:
                should_create_files_dir = False

            def create_files_dir(submission_dir):
                if should_create_files_dir:
                    files_dir = os.path.join(submission_dir, "files")
                    if not os.path.exists(files_dir):
                        os.makedirs(files_dir)
                    return files_dir
                else:
                    return submission_dir

            if self.is_direct_link_to_content(submission.url, [".png", ".jpg", ".jpeg", ".gif"]):
                files_dir = create_files_dir(submission_dir)

                filename = submission.url.split("/")[-1]
                self.logger.spam(
                    self.indent_1 + "This is a direct link to a " + filename.split(".")[-1] + " file")
                save_path = os.path.join(files_dir, filename)
                self.download_direct_link(submission, save_path)
                success = True
            elif self.is_direct_link_to_content(submission.url, [".mp4"]):
                filename = submission.url.split("/")[-1]
                self.logger.spam(
                    self.indent_1 + "This is a direct link to a " + filename.split(".")[-1] + " file")
                if not skip_videos:
                    files_dir = create_files_dir(submission_dir)
                    save_path = os.path.join(files_dir, filename)
                    self.download_direct_link(submission, save_path)
                    success = True
                else:
                    self.logger.spam(self.indent_1 + "Skipping download of video content")
                    success = True
            elif self.is_reddit_gallery(submission.url):
                files_dir = create_files_dir(submission_dir)

                self.logger.spam(
                    self.indent_1 + "This is a reddit gallery")
                self.download_reddit_gallery(submission, files_dir, skip_videos)
                success = True
            elif self.is_reddit_video(submission.url):
                self.logger.spam(
                    self.indent_1 + "This is a reddit video")

                if not skip_videos:
                    files_dir = create_files_dir(submission_dir)
                    self.download_reddit_video(submission, files_dir)
                    success = True
                else:
                    self.logger.spam(self.indent_1 + "Skipping download of video content")
                    success = True
            elif self.is_gfycat_link(submission.url) or self.is_redgifs_link(submission.url):
                if self.is_gfycat_link(submission.url):
                    self.logger.spam(
                        self.indent_1 + "This is a gfycat link")
                else:
                    self.logger.spam(
                        self.indent_1 + "This is a redgif link")

                if not skip_videos:
                    files_dir = create_files_dir(submission_dir)
                    self.download_gfycat_or_redgif(submission, files_dir)
                    success = True
                else:
                    self.logger.spam(self.indent_1 + "Skipping download of video content")
                    success = True
            elif self.is_imgur_album(submission.url):
                files_dir = create_files_dir(submission_dir)

                self.logger.spam(
                    self.indent_1 + "This is an imgur album")
                self.download_imgur_album(submission, files_dir)
                success = True
            elif self.is_imgur_image(submission.url):
                files_dir = create_files_dir(submission_dir)

                self.logger.spam(
                    self.indent_1 + "This is an imgur image or video")
                self.download_imgur_image(submission, files_dir)
                success = True
            elif self.is_self_post(submission):
                self.logger.spam(self.indent_1 + "This is a self-post")
                success = True
            elif (not skip_videos) and (self.is_youtube_link(submission.url) or self.is_supported_by_youtubedl(submission.url)):
                if self.is_youtube_link(submission.url):
                    self.logger.spam(
                        self.indent_1 + "This is a youtube link")
                else:
                    self.logger.spam(
                        self.indent_1 + "This link is supported by a youtube-dl extractor")

                if not skip_videos:
                    files_dir = create_files_dir(submission_dir)
                    self.download_youtube_video(submission.url, files_dir)
                    success = True
                else:
                    self.logger.spam(self.indent_1 + "Skipping download of video content")
                    success = True
            else:
                success = True

            # Download submission meta
            if not skip_meta:
                self.logger.spam(self.indent_1 + "Saving submission.json")
                self.download_submission_meta(submission, submission_dir)
            else:
                self.logger.spam(
                    self.indent_1 + "Skipping submissions meta")

            # Downlaod comments if requested
            if not skip_comments:
                if comment_limit == None:
                    self.logger.spam(
                        self.indent_1 + "Saving all comments to comments.json")
                else:
                    self.logger.spam(
                        self.indent_1 + "Saving top-level comments to comments.json")
                self.download_comments(
                    submission, submission_dir, comment_limit)
            else:
                self.logger.spam(
                    self.indent_1 + "Skipping comments")

            if success:
                self.logger.spam(
                    self.indent_1 + "Saved to " + submission_dir + "\n")
            else:
                self.logger.warning(
                    self.indent_1 + "Failed to download from link " + submission.url + "\n"
                )

    def print_formatted_error(self, e):
        for line in str(e).split("\n"):
            self.logger.error(self.indent_2 + line)

    def is_direct_link_to_content(self, url, supported_file_formats):
        url_leaf = url.split("/")[-1]
        return any([i in url_leaf for i in supported_file_formats]) and ".gifv" not in url_leaf

    def download_direct_link(self, submission, output_path):
        try:
            urllib.request.urlretrieve(submission.url, output_path)
        except Exception as e:
            self.print_formatted_error(e)

    def is_youtube_link(self, url):
        return "youtube.com" in url or "youtu.be" in url

    def is_supported_by_youtubedl(self, url):
        try:
            # Since youtube-dl's quiet mode is amything BUT quiet
            # using contextlib to redirect stdout to a local StringIO variable
            local_stderr = StringIO()
            with contextlib.redirect_stderr(local_stderr):
                if "flickr.com/photos" in url:
                    return False

                # Try to extract info from URL
                try:
                    download_options = {
                        'quiet': True,
                        'warnings': True,
                        'ignoreerrors': True,
                    }
                    ydl = youtube_dl.YoutubeDL(download_options)
                    r = ydl.extract_info(url, download=False)
                except Exception as e:
                    # No media found through youtube-dl
                    self.logger.spam(self.indent_2 + "No media found in '" + url + "' that could be downloaded with youtube-dl")
                    return False

                extractors = youtube_dl.extractor.gen_extractors()
                for e in extractors:
                    if e.suitable(url) and e.IE_NAME != 'generic':
                        return True
                        self.logger.spam(self.indent_2 + "This link could potentially be downloaded with youtube-dl")
                self.logger.spam(self.indent_2 + "No media found in '" + url + "' that could be downloaded with youtube-dl")
                return False
        except Exception as e:
            return False

    def download_youtube_video(self, url, output_path):
        try:
            local_stderr = StringIO()
            with contextlib.redirect_stderr(local_stderr):
                download_options = {
                    'format': "299+bestaudio/298+bestaudio/137+bestaudio/136+bestaudio/best",
                    'quiet': True,
                    'warnings': True,
                    'ignoreerrors': True,
                    'nooverwrites': True,
                    'continuedl': True,
                    'outtmpl': output_path + '/%(id)s.%(ext)s'
                }
                self.logger.spam(self.indent_2 + "Downloading " +
                                url + " with youtube-dl")
                with youtube_dl.YoutubeDL(download_options) as ydl:
                    ydl.download([url])
                    errors = local_stderr.getvalue()
                    if not len(errors):
                        self.logger.spam(self.indent_2 + "Finished downloading video from " +
                                    url)
                    else:
                        self.logger.error(self.indent_2 + errors.strip())
        except Exception as e:
            self.logger.error(self.indent_2 + "Failed to download with youtube-dl")
            self.print_formatted_error(e)

    def is_reddit_gallery(self, url):
        return "reddit.com/gallery" in url

    def download_reddit_gallery(self, submission, output_path, skip_videos):
        gallery_data = getattr(submission, "gallery_data", None)
        media_metadata = getattr(submission, "media_metadata", None)
        self.logger.spam(
            self.indent_2 + "Looking for submission.gallery_data and submission.media_metadata")

        if gallery_data == None and media_metadata == None:
            # gallery_data not in submission
            # could be a crosspost
            crosspost_parent_list = getattr(
                submission, "crosspost_parent_list", None)
            if crosspost_parent_list != None:
                self.logger.spam(
                    self.indent_2 + "This is a crosspost to a reddit gallery")
                first_parent = crosspost_parent_list[0]
                gallery_data = first_parent["gallery_data"]
                media_metadata = first_parent["media_metadata"]

        if gallery_data != None and media_metadata != None:
            image_count = len(gallery_data["items"])
            self.logger.spam(self.indent_2 + "This reddit gallery has " +
                             str(image_count) + " images")
            for j, item in tqdm(enumerate(gallery_data["items"]), total=image_count, bar_format='%s%s{l_bar}{bar:20}{r_bar}%s' % (self.indent_2, Fore.WHITE + Fore.LIGHTBLACK_EX, Fore.RESET)):
                try:
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
                            # Skip video content if requested by user
                            if skip_videos:
                                continue
                        item_filename = media_id + "." + item_format
                        item_url = item_metadata["s"]["u"]
                        save_path = os.path.join(output_path, item_filename)
                        try:
                            urllib.request.urlretrieve(item_url, save_path)
                        except Exception as e:
                            self.print_formatted_error(e)
                except Exception as e:
                    self.print_formatted_error(e)

    def is_reddit_video(self, url):
        return "v.redd.it" in url

    def download_reddit_video(self, submission, output_path):
        media = getattr(submission, "media", None)
        media_id = submission.url.split("v.redd.it/")[-1]

        self.logger.spam(self.indent_2 + "Looking for submission.media")

        if media == None:
            # link might be a crosspost
            crosspost_parent_list = getattr(
                submission, "crosspost_parent_list", None)
            if crosspost_parent_list != None:
                self.logger.spam(
                    self.indent_2 + "This is a crosspost to a reddit video")
                first_parent = crosspost_parent_list[0]
                media = first_parent["media"]

        if media != None:
            self.logger.spam(self.indent_2 + "Downloading video component")
            url = media["reddit_video"]["fallback_url"]
            video_save_path = os.path.join(
                output_path, media_id + "_video.mp4")
            try:
                urllib.request.urlretrieve(url, video_save_path)
            except Exception as e:
                self.print_formatted_error(e)

            # Download the audio
            self.logger.spam(self.indent_2 + "Downloading audio component")
            audio_downloaded = False
            audio_save_path = os.path.join(
                output_path, media_id + "_audio.mp4")
            try:
                urllib.request.urlretrieve(
                    submission.url + "/DASH_audio.mp4", audio_save_path)
                audio_downloaded = True
            except Exception as e:
                pass

            if audio_downloaded == True:
                # Merge mp4 files
                self.logger.spam(
                    self.indent_2 + "Merging video & audio components with ffmpeg")
                output_save_path = os.path.join(output_path, media_id + ".mp4")
                input_video = ffmpeg.input(video_save_path)
                input_audio = ffmpeg.input(audio_save_path)
                ffmpeg.concat(input_video, input_audio, v=1, a=1)\
                    .output(output_save_path)\
                    .global_args('-loglevel', 'error')\
                      .global_args('-y')\
                    .run()
                self.logger.spam(self.indent_2 + "Done merging with ffmpeg")
            else:
                self.logger.spam(
                    self.indent_2 + "This video does not have an audio component")

            self.logger.spam(
                    self.indent_2 + "Sucessfully saved video")

    def is_gfycat_link(self, url):
        return "gfycat.com/" in url

    def is_redgifs_link(self, url):
        return "redgifs.com/" in url

    def get_gfycat_embedded_video_url(self, url):
        try:
            response  = requests.get(url)
            data = response.text
            soup = BeautifulSoup(data, features="html.parser")

            # Cycle through all links
            giant_url_found = False
            giant_url = ""
            thumbs_url_found = False
            thumbs_url = ""
            for link in soup.find_all():
                link_src = link.get('src')
                src_url = str(link_src)
                if ".mp4" in src_url:
                    # Looking for giant.gfycat.com
                    if "giant." in src_url:
                        giant_url_found = True
                        giant_url = src_url
                    elif "thumbs." in src_url:
                        thumbs_url_found = True
                        thumbs_url = src_url
        except Exception as e:
            self.print_formatted_error(e)
            return ""

        if giant_url_found:
            return giant_url
        elif thumbs_url_found:
            return thumbs_url
        else:
            return ""

    def guess_extension(self, url):
        response = requests.get(url)
        content_type = response.headers['content-type']
        return mimetypes.guess_extension(content_type)

    def get_redirect_url(self, url):
        r = requests.get(url)
        return r.url

    def download_gfycat_or_redgif(self, submission, output_dir):
        # Check if gfycat redirects to gifdeliverynetwork
        redirect_url = self.get_redirect_url(submission.url)
        if "gfycat.com" in submission.url and "gifdeliverynetwork.com" in redirect_url:
            self.logger.spam(
                self.indent_2 + "This is a gfycat link that redirects to gifdeliverynetwork.com")
            try:
                # Gfycat link that redirects to gifdeliverynetwork
                # True source in this case is hiding in redgifs.com
                response = requests.get(redirect_url)
                html = BeautifulSoup(response.content, features="html.parser")
                links = html.find_all()
                for i in links:
                    if "src" in str(i):
                        attrs = i.attrs
                        if "src" in attrs:
                            src = attrs["src"]
                            if "redgifs.com/" in src:
                                self.logger.spam(
                                    self.indent_2 + "Found embedded media at " + src)
                                filename = src.split("/")[-1]
                                save_path = os.path.join(output_dir, filename)
                                try:
                                    r = requests.get(src)
                                    with open(save_path, 'wb') as outfile:
                                        outfile.write(r.content)
                                except Exception as e:
                                    self.print_formatted_error(e)
            except Exception as e:
                self.print_formatted_error(e)

        self.logger.spam(
            self.indent_2 + "Looking for submission.preview.reddit_video_preview.fallback_url")

        preview = None
        try:
            preview = getattr(submission, "preview")
            if preview:
                if "reddit_video_preview" in preview:
                    if "fallback_url" in preview["reddit_video_preview"]:
                        self.logger.spam(self.indent_2 + "Found submission.preview.reddit_video_preview.fallback_url")
                        fallback_url = preview["reddit_video_preview"]["fallback_url"]
                        if "." in fallback_url.split("/")[-1]:
                            file_format = fallback_url.split(".")[-1]
                            filename = submission.url.split("/")[-1] + "." + file_format
                        else:
                            filename = submission.url.split("/")[-1] + ".mp4"
                        save_path = os.path.join(output_dir, filename)
                        try:
                            urllib.request.urlretrieve(fallback_url, save_path)
                            return
                        except Exception as e:
                            self.print_formatted_error(e)
                elif "images" in preview:
                    if "source" in preview["images"][0]:
                        self.logger.spam(self.indent_2 + "Found submission.preview.images instead")
                        source_url = preview["images"][0]["source"]["url"]
                        try:
                            extension = self.guess_extension(source_url)
                            filename = submission.url.split("/")[-1] + extension
                            save_path = os.path.join(output_dir, filename)
                            try:
                                urllib.request.urlretrieve(source_url, save_path)
                            except Exception as e:
                                self.print_formatted_error(e)
                        except Exception as e:
                            self.print_formatted_error(e)

        except Exception as e:
           self.print_formatted_error(e)

        try:
            self.logger.spam(
                self.indent_2 + "Looking for submission.media_embed")
            media_embed = getattr(submission, "media_embed")
            if media_embed:
                content = media_embed["content"]
                self.logger.spam(
                    self.indent_2 + "Found submission.media_embed")
                if "iframe" in content:
                    if "gfycat.com" in submission.url:
                        self.logger.spam(
                            self.indent_2 + "This is an embedded video in gfycat.com")
                        # This is likely an embedded video in gfycat
                        video_url = self.get_gfycat_embedded_video_url(submission.url)
                        if video_url:
                            filename = video_url.split("/")[-1]
                            save_path = os.path.join(output_dir, filename)

                            self.logger.spam(
                                self.indent_2 + "Embedded video URL: " + video_url)
                            try:
                                r = requests.get(video_url)
                                with open(save_path, 'wb') as outfile:
                                    outfile.write(r.content)
                            except Exception as e:
                                self.print_formatted_error(e)
        except Exception as e:
            self.print_formatted_error(e)

    def is_imgur_album(self, url):
        return "imgur.com/a/" in url or "imgur.com/gallery/" in url

    def get_imgur_album_images_count(self, album_id):
        request = "https://api.imgur.com/3/album/" + album_id
        res = requests.get(request, headers={
                           "Authorization": "Client-ID " + self.IMGUR_CLIENT_ID})
        if res.status_code == 200:
            return res.json()["data"]["images_count"]
        else:
            self.logger.spam(self.indent_2 + "This imgur album is empty")
            return 0

    def get_imgur_image_meta(self, image_id):
        request = "https://api.imgur.com/3/image/" + image_id
        res = requests.get(request, headers={
                           "Authorization": "Client-ID " + self.IMGUR_CLIENT_ID})
        return res.json()["data"]

    def download_imgur_album(self, submission, output_dir):
        # Imgur album
        album_id = ""
        if "imgur.com/a/" in submission.url:
            album_id = submission.url.split("imgur.com/a/")[-1]
        elif "imgur.com/gallery/" in submission.url:
            album_id = submission.url.split("imgur.com/gallery/")[-1]

        self.logger.spam(self.indent_2 + "Album ID " + album_id)

        images_count = self.get_imgur_album_images_count(album_id)
        if images_count > 0:
            request = "https://api.imgur.com/3/album/" + album_id
            res = requests.get(request, headers={
                               "Authorization": "Client-ID " + self.IMGUR_CLIENT_ID})
            self.logger.spam(self.indent_2 + "This imgur album has " +
                             str(images_count) + " images")
            for i, image in tqdm(enumerate(res.json()["data"]["images"]), total=images_count, bar_format='%s%s{l_bar}{bar:20}{r_bar}%s' % (self.indent_2, Fore.WHITE + Fore.LIGHTBLACK_EX, Fore.RESET)):
                url = image["link"]
                filename = str(i).zfill(3) + "_" + url.split("/")[-1]
                save_path = os.path.join(output_dir, filename)
                try:
                    if not os.path.exists(output_dir):
                        os.makedirs(output_dir)
                    urllib.request.urlretrieve(url, save_path)
                except Exception as e:
                    self.print_formatted_error(e)

    def is_imgur_image(self, url):
        return "imgur.com" in url

    def download_imgur_image(self, submission, output_dir):
        # Other imgur content, e.g., .gifv, '.mp4', '.jpg', etc.
        url_leaf = submission.url.split("/")[-1]
        if "." in url_leaf:
            image_id = url_leaf.split(".")[0]
        else:
            image_id = url_leaf

        try:
            data = self.get_imgur_image_meta(image_id)
            url = data["link"]
            image_type = data["type"]
            if "video/" in image_type:
                self.logger.spam(
                    self.indent_2 + "This is an imgur link to a video file")
                image_type = image_type.split("video/")[-1]
            elif "image/" in image_type:
                self.logger.spam(
                    self.indent_2 + "This is an imgur link to an image file")
                image_type = image_type.split("image/")[-1]

            filename = image_id + "." + image_type
            save_path = os.path.join(output_dir, filename)

            urllib.request.urlretrieve(url, save_path)
        except Exception as e:
            self.print_formatted_error(e)

    def download_comments(self, submission, output_dir, comment_limit):
        # Save comments - Breath first unwrap of comment forest
        comments_list = []
        with open(os.path.join(output_dir, 'comments.json'), 'w') as file:
            submission.comments.replace_more(limit=comment_limit)
            limited_comments = submission.comments.list()
            if not len(limited_comments):
                # No comments
                self.logger.spam(self.indent_2 + "No comments found")
                return

            for comment in tqdm(limited_comments, total=len(limited_comments), bar_format='%s%s{l_bar}{bar:20}{r_bar}%s' % (self.indent_2, Fore.WHITE + Fore.LIGHTBLACK_EX, Fore.RESET)):
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
                except Exception as e:
                    self.print_formatted_error(e)
                comments_list.append(comment_dict)
            file.write(json.dumps(comments_list, indent=2))

    def is_self_post(self, submission):
        return submission.is_self

    def download_submission_meta(self, submission, submission_dir):
        submission_dict = {}
        if submission.author:
            submission_dict["author"] = submission.author.name
        else:
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