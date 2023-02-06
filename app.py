import math
import os
from pathlib import Path

import streamlit as st

from models.nlp import prepare_similarity_model
from models.whisper import prepare_whisper_model, whisper_recognize
from utils.audio import convert_to_hz, extract_audio_from_video
from utils.text import get_top_timestamps
from utils.video import download_video, valid_link

stage = 1


def _display_input_type():
    file_type = st.selectbox(label="File type", options=["<select>", "Audio", "YT Video", "Existing sample"])
    return file_type


def _sample_upload():
    video_path = Path("assets") / "tmp.mp4"
    with open(video_path, "rb") as fp:
        video_bytes = fp.read()

    st.video(video_bytes, format="video/mp4")
    return video_path


def _audio_upload():
    uploaded_file = st.file_uploader("Choose an audio file", type=[".wav"], accept_multiple_files=False)

    if uploaded_file is not None:
        audio_fpath = uploaded_file.name
        with open(audio_fpath, "wb") as fp:
            fp.write(uploaded_file.getvalue())

        convert_to_hz(audio_fpath)

        st.audio(uploaded_file.getvalue(), format="audio/wav")
        return Path(audio_fpath)

    return None


@st.cache(show_spinner=False)
def _download_video(yt_link):
    return download_video(yt_link)


def _video_link_upload():
    yt_link = st.text_input("Youtube Link", value="")
    if yt_link:
        if valid_link(yt_link):
            with st.spinner("Downloading..."):
                video_path = _download_video(yt_link)

            with open(video_path, "rb") as fp:
                st.video(fp.read(), format="video/mp4")

            return video_path
        else:
            st.error("Youtube Link is not valid.")

    return None


@st.cache(show_spinner=False)
def _whisper_recognize(media_path, file_type):
    if file_type in ("YT Video", "Existing Sample"):
        audio_path = extract_audio_from_video(media_path)
    else:
        audio_path = media_path

    transcriptions, output_srt_filepath = whisper_recognize(audio_path)

    if file_type in ("YT Video", "Existing Sample"):
        os.remove(audio_path)

    os.remove(output_srt_filepath)

    return transcriptions


@st.cache(show_spinner=False)
def _setup():
    prepare_whisper_model()
    prepare_similarity_model()


def display_media(media_path, timestamps, media_type):
    def _display_media_at_timestamp(media_bytes, timestamp, media_type, st_obj):
        if media_type == "audio":
            st_obj.audio(media_bytes, format="audio/wav", start_time=timestamp)
        else:
            st_obj.video(media_bytes, format="video/mp4", start_time=timestamp)

    with open(media_path, "rb") as fp:
        media_bytes = fp.read()

    col1, col2 = st.columns(2)
    mid_timestamps = math.ceil(len(timestamps) / 2)

    for timestamp in timestamps[:mid_timestamps]:
        _display_media_at_timestamp(media_bytes, timestamp, media_type, col1)

    for timestamp in timestamps[mid_timestamps:]:
        _display_media_at_timestamp(media_bytes, timestamp, media_type, col2)


def _main():
    global stage

    file_type = None
    if stage == 1:
        _setup()
        st.header("Earwise")
        st.subheader("Search within Audio")
        st.info("To restart the app, please refresh :)")
        file_type = _display_input_type()
        stage = 2

    if stage == 2:
        media_path = None
        if file_type == "Audio":
            media_path = _audio_upload()
        elif file_type == "YT Video":
            media_path = _video_link_upload()
        elif file_type == "Existing sample":
            media_path = _sample_upload()

        if media_path:
            stage = 3

    if stage == 3:
        with st.spinner("Processing..."):
            transcriptions = _whisper_recognize(media_path, file_type)

        stage = 4

    if stage == 4:
        search_query = st.text_input(label="Search...")

        if search_query:
            with st.spinner("Searching audio..."):
                timestamps = get_top_timestamps(transcriptions, search_query, threshold=0.5)

            media_type = "video" if file_type in ("YT Video", "Existing Sample") else "audio"
            display_media(media_path, timestamps, media_type)


if __name__ == "__main__":
    _main()
