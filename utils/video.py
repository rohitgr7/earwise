import re
from pathlib import Path

import requests
from yt_dlp import YoutubeDL


def download_video(link):
    with YoutubeDL(
        {
            "format": "best",
            "outtmpl": "%(title)s.%(ext)s",
            "postprocessors": [
                {
                    "key": "FFmpegVideoConvertor",
                    "preferedformat": "mp4",
                }
            ],
            "postprocessor_args": ["-ar", "16000"],
        }
    ) as ydl:
        file = ydl.extract_info(link)
    path = Path(f"{file['title']}.mp4")
    return path


def valid_link(link):
    return re.match(r"^(https?\:\/\/)?((www\.)?youtube\.com|youtu\.be)\/.+$", link) and not (
        "Video unavailable" in requests.get(link).text
    )
