FOLDER=whisper_cpp
URL=https://github.com/ggerganov/whisper.cpp

if [ ! -d "$FOLDER" ] ; then
    git clone "$URL" "$FOLDER"
fi

make base -C whisper_cpp
