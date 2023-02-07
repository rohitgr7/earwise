from transformers import AutoModel, AutoTokenizer, pipeline


def prepare_similarity_model():
    tokenizer = AutoTokenizer.from_pretrained("sentence-transformers/all-MiniLM-L6-v2")
    model = AutoModel.from_pretrained("sentence-transformers/all-MiniLM-L6-v2")
    model.eval()
    return model, tokenizer


def prepare_qna_pipeline():
    question_answerer = pipeline("question-answering", model="distilbert-base-cased-distilled-squad")
    return question_answerer
