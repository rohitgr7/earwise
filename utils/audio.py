from pathlib import Path

from moviepy.editor import VideoFileClip
from pydub import AudioSegment


def convert_to_hz(audio_fpath, hz=16000):
    sound = AudioSegment.from_wav(audio_fpath)
    new_sound = sound.set_frame_rate(hz)
    new_sound.export(audio_fpath, format="wav")


def extract_audio_from_video(video_path, hz=16000):
    audio_path = Path(f"{video_path.stem}.wav")
    video = VideoFileClip(str(video_path))
    audio = video.audio
    audio = audio.set_fps(hz)
    audio.write_audiofile(str(audio_path), fps=hz)
    return audio_path
