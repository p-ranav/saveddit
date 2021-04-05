import os
import requests
import urllib

IMGUR_CLIENT_ID = "33982ca3205a4a2"
IMGUR_CLIENT_SECRET = "731679375fb1f5753d8bec6ae8f97bb8bee09c09"

def get_imgur_album_images_count(album_id):
  request = "https://api.imgur.com/3/album/" + album_id
  res = requests.get(request, headers={"Authorization": "Client-ID " + IMGUR_CLIENT_ID})
  return res.json()["data"]["images_count"]

def download_imgur_album(album_id, output_path):
  request = "https://api.imgur.com/3/album/" + album_id
  res = requests.get(request, headers={"Authorization": "Client-ID " + IMGUR_CLIENT_ID})
  for i, image in enumerate(res.json()["data"]["images"]):
    url = image["link"]
    filename = str(i).zfill(4) + "_" + url.split("/")[-1]
    save_path = os.path.join(output_path, filename)
    try:
      if not os.path.exists(output_path):
        os.makedirs(output_path)
      urllib.request.urlretrieve(url, save_path)
    except Exception as e:
      print(e)