import os
import subprocess
from pathlib import Path

import requests
import streamlit as st

from utils.audio import convert_to_hz, extract_audio_from_video
from utils.text import get_top_keywords, get_top_timestamp_for_question, get_top_timestamps_for_keyword
from utils.video import download_video, valid_link


@st.cache_data(show_spinner=False, ttl=None)
def _start_server():
    subprocess.call("uvicorn backend.main:app --host 0.0.0.0 --port 8000 &", shell=True)


def _display_input_type():
    file_type = st.selectbox(label="File type", options=["<select>", "Audio", "YT Video", "Existing Sample"])
    return file_type if file_type != "<select>" else None


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


@st.cache_data(show_spinner=False, ttl=3600 * 6)
def _download_video(yt_link):
    return download_video(yt_link)


def _video_link_upload():
    yt_link = st.text_input("Youtube Link", value="")
    if yt_link:
        if valid_link(yt_link):
            with st.spinner("Downloading..."):
                video_path = _download_video(yt_link)

            if isinstance(video_path, dict) and "error" in video_path:
                st.error(video_path["error"])
                return None

            with open(video_path, "rb") as fp:
                st.video(fp.read(), format="video/mp4")

            return video_path
        else:
            st.error("Youtube Link is not valid.")

    return None


@st.cache_data(show_spinner=False, ttl=3600 * 6)
def _whisper_recognize(url, media_path, file_type):
    if file_type in ("YT Video", "Existing Sample"):
        audio_path = extract_audio_from_video(media_path)
    else:
        audio_path = media_path

    files = {"file_upload": open(audio_path, "rb")}
    response = requests.post(url, files=files)
    transcriptions = response.json()["result"]

    if file_type in ("YT Video", "Existing Sample") and os.path.exists(audio_path):
        os.remove(audio_path)

    return transcriptions


def display_media(media_path, timestamps, media_type, placeholder):
    def _display_media_at_timestamp(media_bytes, timestamp, media_type, st_obj):
        if media_type == "audio":
            st_obj.audio(media_bytes, format="audio/wav", start_time=timestamp)
        else:
            st_obj.video(media_bytes, format="video/mp4", start_time=timestamp)

    with open(media_path, "rb") as fp:
        media_bytes = fp.read()

    # with st.empty():
    with placeholder.container():
        col1, col2 = st.columns(2)

        for timestamp in timestamps[::2]:
            _display_media_at_timestamp(media_bytes, timestamp, media_type, col1)

        for timestamp in timestamps[1::2]:
            _display_media_at_timestamp(media_bytes, timestamp, media_type, col2)


def _initialize_session_state():
    if "stage" not in st.session_state:
        st.session_state["stage"] = 1

    if "search_query" not in st.session_state:
        st.session_state["search_query"] = ""

    if "search_type" not in st.session_state:
        st.session_state["search_type"] = ""


def _main():
    _start_server()

    file_type = None
    if st.session_state["stage"] >= 1:
        st.header("Earwise (Only English)")
        st.subheader("Search within Audio")
        st.info("To restart the app, please refresh :)")
        st.warning("Please don't overuse, it's running on free-tier :)")
        file_type = _display_input_type()

        if file_type:
            st.session_state["stage"] = 2

    if st.session_state["stage"] >= 2:
        media_path = None
        if file_type == "Audio":
            media_path = _audio_upload()
        elif file_type == "YT Video":
            media_path = _video_link_upload()
        elif file_type == "Existing Sample":
            media_path = _sample_upload()

        if media_path:
            st.session_state["stage"] = 3

    if st.session_state["stage"] >= 3:
        with st.spinner("Processing..."):
            url = f"{st.secrets['URL']}/transcribe"
            transcriptions = _whisper_recognize(url, media_path, file_type)

        st.session_state["stage"] = 4

    if st.session_state["stage"] >= 4:
        if not st.session_state["search_query"]:
            search_type = st.selectbox(
                label="What do you want to do?", options=["<select>", "Keyword Search", "Ask a question"]
            )
            st.session_state["search_type"] = search_type

        if st.session_state["search_type"] == "Keyword Search":
            # Set up some sample tags
            selected_tag = ""
            if not st.session_state["search_query"]:
                url = f"{st.secrets['URL']}/extract_keywords"
                keywords = get_top_keywords(url, transcriptions)
                num_cols = len(keywords)
                container = st.container()
                cols = container.columns(num_cols)

                for i, tag in enumerate(keywords):
                    col_idx = i % num_cols
                    button = cols[col_idx].button(tag)
                    if button:
                        selected_tag = tag
                        st.session_state["search_query"] = selected_tag
                        st.experimental_rerun()

            search_query = ""
            if not st.session_state["search_query"]:
                search_query = st.text_input(label="Search a keyword", placeholder="weekend routine")

            placeholder = st.empty()
            if st.session_state["search_query"]:
                clear = st.button("Clear results")
                if clear:
                    placeholder.empty()
                    st.session_state["search_query"] = ""
                    st.session_state["search_type"] = ""
                    st.experimental_rerun()

            if search_query:
                st.session_state["search_query"] = search_query
                st.experimental_rerun()

            if st.session_state["search_query"] and not clear:
                with st.spinner("Searching audio..."):
                    url = f"{st.secrets['URL']}/keyword_query"
                    timestamps = get_top_timestamps_for_keyword(
                        url, transcriptions, st.session_state["search_query"], threshold=0.5
                    )

                if not timestamps:
                    st.text("No result. Please try something else :)")
                else:
                    media_type = "video" if file_type in ("YT Video", "Existing Sample") else "audio"
                    display_media(media_path, timestamps, media_type, placeholder)

        elif st.session_state["search_type"] == "Ask a question":
            search_query = ""
            if not st.session_state["search_query"]:
                search_query = st.text_input(label="Ask a question", placeholder="What do you do on weekend?")

            placeholder = st.empty()
            if st.session_state["search_query"]:
                clear = st.button("Clear results")
                if clear:
                    placeholder.empty()
                    st.session_state["search_query"] = ""
                    st.session_state["search_type"] = ""
                    st.experimental_rerun()

            if search_query:
                st.session_state["search_query"] = search_query
                st.experimental_rerun()

            if st.session_state["search_query"] and not clear:
                with st.spinner("Searching audio..."):
                    url = f"{st.secrets['URL']}/question_query"
                    timestamp = get_top_timestamp_for_question(
                        url, transcriptions, st.session_state["search_query"], threshold=0.1
                    )

                if not timestamp:
                    st.text("No result. Please try something else :)")
                else:
                    media_type = "video" if file_type in ("YT Video", "Existing Sample") else "audio"
                    display_media(media_path, [timestamp], media_type, placeholder)


if __name__ == "__main__":
    _initialize_session_state()
    _main()
