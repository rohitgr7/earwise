import torch
import torch.nn.functional as F
from keybert import KeyBERT
from transformers import AutoModel, AutoTokenizer, pipeline


def prepare_similarity_model():
    tokenizer = AutoTokenizer.from_pretrained("sentence-transformers/all-MiniLM-L6-v2")
    model = AutoModel.from_pretrained("sentence-transformers/all-MiniLM-L6-v2")
    model.eval()
    return model, tokenizer


def prepare_qna_pipeline():
    question_answerer = pipeline("question-answering", model="distilbert-base-cased-distilled-squad")
    return question_answerer


def prepare_keyword_extractor():
    return KeyBERT()


def _mean_pooling(model_output, attention_mask):
    token_embeddings = model_output[0]  # First element of model_output contains all token embeddings
    input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
    return torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(input_mask_expanded.sum(1), min=1e-9)


def predict_top_timestamps_for_keyword(texts, search_query, threshold, model, tokenizer):
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
    return pred_ixs


def predict_top_timestamp_for_question(context, question, pipeline):
    result = pipeline(question=question, context=context)
    return result


def predict_keywords(docs, model):
    return model.extract_keywords(docs, keyphrase_ngram_range=(1, 2), stop_words="english", use_mmr=True, diversity=0.6)
