import os
from pathlib import Path
from typing import List

from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.models.nlp import (
    predict_top_timestamp_for_question,
    predict_top_timestamps_for_keyword,
    prepare_qna_pipeline,
    prepare_similarity_model,
)
from backend.models.whisper import prepare_whisper_model, whisper_recognize

prepare_whisper_model()
sim_model, sim_tokenizer = prepare_similarity_model()
qna_pipeline = prepare_qna_pipeline()


app = FastAPI()
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class KeywordPayload(BaseModel):
    texts: List[str]
    search_query: str
    threshold: float


class QuestionPayload(BaseModel):
    context: str
    question: str


@app.get("/healthcheck")
async def pong():
    return {"status": "alive"}


@app.post("/transcribe")
async def transcribe(file_upload: UploadFile = File(...)):
    fpath = Path(file_upload.filename)
    # TODO: remove this
    fpath = Path("tmp2.wav")

    with open(fpath, "wb") as fp:
        fp.write(file_upload.file.read())

    transcriptions, srt_file = whisper_recognize(fpath)
    os.remove(srt_file)
    os.remove(fpath)
    return {"result": transcriptions}


@app.post("/keyword_query")
async def predict_keyword_timestamps(data: KeywordPayload):
    pred_ixs = predict_top_timestamps_for_keyword(
        data.texts, data.search_query, data.threshold, sim_model, sim_tokenizer
    )
    return {"result": pred_ixs}


@app.post("/question_query")
async def predict_question_timestamp(data: QuestionPayload):
    result = predict_top_timestamp_for_question(data.context, data.question, qna_pipeline)
    return {"result": result}
