def get_top_timestamps(transcriptions, search_query, threshold=0.7):
    return [x["start"] for x in transcriptions][:7]
