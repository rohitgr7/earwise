import re
from pathlib import Path

import requests
from yt_dlp import YoutubeDL


def download_video(link):
    yt_opts = {
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
    with YoutubeDL(yt_opts) as ydl:
        file = ydl.extract_info(link, download=False)

    yt_opts["outtmpl"] = file["id"] + ".%(ext)s"
    with YoutubeDL(yt_opts) as ydl:
        file = ydl.extract_info(link, download=True)

    path = Path(f"{file['id']}.mp4")
    return path


def valid_link(link):
    return re.match(r"^(https?\:\/\/)?((www\.)?youtube\.com|youtu\.be)\/.+$", link) and not (
        "Video unavailable" in requests.get(link).text
    )
