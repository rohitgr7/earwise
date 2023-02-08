import re
from pathlib import Path

import pytube
import requests
from pytube import YouTube


def download_video(link):
    file_id = pytube.extract.video_id(link).replace("-", "_")
    YouTube(link).streams.filter(progressive=True, file_extension="mp4").order_by("resolution").asc().first().download(
        output_path=".", filename=f"{file_id}.mp4"
    )
    path = Path(f"{file_id}.mp4")
    return path


def valid_link(link):
    return re.match(r"^(https?\:\/\/)?((www\.)?youtube\.com|youtu\.be)\/.+$", link) and not (
        "Video unavailable" in requests.get(link).text
    )
