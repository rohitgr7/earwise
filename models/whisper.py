import subprocess
from pathlib import Path

import pysrt


def prepare_whisper_model():
    subprocess.call(["bash", "whisper_setup.sh"])


def whisper_recognize(audio_file_path):
    model_size = "base"

    commands = [
        "whisper_cpp/main",
        f"-m whisper_cpp/models/ggml-{model_size}.bin",
        f"'{str(audio_file_path)}'",
        "--output-srt",
    ]

    subprocess.call(" ".join(commands), shell=True)

    segments = []

    output_srt_filepath = audio_file_path.parents[0] / f"{Path(audio_file_path).stem}.wav.srt"
    subs = pysrt.open(output_srt_filepath)
    for index, sub in enumerate(subs):
        segments.append(
            {
                "id": index,
                "text": sub.text,
                "seek": sub.start.ordinal,
                "start": int(sub.start.ordinal / 1000),
                "end": int(sub.end.ordinal / 1000),
            }
        )

    return segments, output_srt_filepath
