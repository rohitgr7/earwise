import requests


def remove_close_timestamps(transcriptions, sec=30):
    result = [transcriptions[0]]
    i = 0

    while True:
        j = i + 1
        for trans in transcriptions[i + 1 :]:
            if trans["start"] <= (transcriptions[i]["start"] + sec):
                j += 1
                continue
            break

        i = j
        if i >= len(transcriptions):
            break
        else:
            result.append(transcriptions[i])

    return result


def get_top_timestamps_for_keyword(url, transcriptions, search_query, threshold=0.7):
    texts = [x["text"] for x in transcriptions]
    json_data = {
        "texts": texts,
        "search_query": search_query,
        "threshold": 0.5,
    }
    response = requests.post(url, json=json_data)
    pred_ixs = response.json()["result"]
    result = [transcriptions[i] for i in pred_ixs]
    result = sorted(result, key=lambda x: x["start"])

    if result:
        result = remove_close_timestamps(result)

    result = sorted(result, key=lambda x: x["start"])
    return [x["start"] for x in result]


def get_top_timestamp_for_question(url, transcriptions, question, threshold=0.4):
    start_time_map = []
    start_ix = 0
    context = ""
    for trans in transcriptions:
        end_ix = start_ix + len(trans["text"])
        start_time_map.append((trans["start"], start_ix))
        start_ix = end_ix
        context += trans["text"]

    json_data = {
        "context": context,
        "question": question,
    }
    response = requests.post(url, json=json_data)
    result = response.json()["result"]

    if result["score"] < threshold:
        return None

    timestamp = start_time_map[0][0]
    for x in start_time_map:
        if x[1] > result["start"]:
            break
        timestamp = x[0]

    return timestamp
