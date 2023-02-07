import torch
import torch.nn.functional as F

from models.nlp import prepare_qna_pipeline, prepare_similarity_model


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


def _mean_pooling(model_output, attention_mask):
    token_embeddings = model_output[0]  # First element of model_output contains all token embeddings
    input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
    return torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(input_mask_expanded.sum(1), min=1e-9)


def get_top_timestamps_for_keyword(transcriptions, search_query, threshold=0.7):
    model, tokenizer = prepare_similarity_model()
    texts = [x["text"] for x in transcriptions]
    texts.append(search_query)

    encoded_input = tokenizer(texts, padding=True, truncation=True, return_tensors="pt")

    with torch.inference_mode():
        model_output = model(**encoded_input)

    # Perform pooling
    sentence_embeddings = _mean_pooling(model_output, encoded_input["attention_mask"])

    # Normalize embeddings
    sentence_embeddings = F.normalize(sentence_embeddings, p=2, dim=1)

    trans_embed = sentence_embeddings[:-1]
    query_embed = sentence_embeddings[-1]
    scores = trans_embed @ query_embed
    pred_ixs = scores.numpy().argsort()[::-1]
    scores = scores[pred_ixs.tolist()]
    pred_ixs = pred_ixs[scores > threshold].tolist()
    result = [transcriptions[i] for i in pred_ixs]
    result = sorted(result, key=lambda x: x["start"])

    if result:
        result = remove_close_timestamps(result)

    result = sorted(result, key=lambda x: x["start"])
    return [x["start"] for x in result]


def get_top_timestamp_for_question(transcriptions, question, threshold=0.4):
    pipeline = prepare_qna_pipeline()

    start_time_map = []
    start_ix = 0
    context = ""
    for trans in transcriptions:
        end_ix = start_ix + len(trans["text"])
        start_time_map.append((trans["start"], start_ix))
        start_ix = end_ix
        context += trans["text"]

    result = pipeline(question=question, context=context)
    if result["score"] < threshold:
        return None

    timestamp = start_time_map[0][0]
    for x in start_time_map:
        if x[1] > result["start"]:
            break
        timestamp = x[0]

    return timestamp
