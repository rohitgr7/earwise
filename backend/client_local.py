import requests

URL = "http://localhost:8005"
HEADERS = {"Content-type": "application/json"}


def health_check():
    response = requests.get(f"{URL}/healthcheck", headers=HEADERS)
    print(response.json())


def transcribe():
    url = f"{URL}/transcribe"
    files = {"file_upload": open("tmp.wav", "rb")}
    response = requests.post(url, files=files)
    print(response.json())


def keyword_query():
    texts = [
        " It was boxing the blade and head off and kicking the blade and leg off.",
        " You was all sure you threw it to cause the distance.",
        " This is not over.",
        " If we had to take this, I'm sorry for him, it's all out of swear.",
        " We don't give our bollocks.",
        " He said that he believes that one of the kicks that he checked is what broke your leg.",
    ]
    search_query = "kicks"

    json_data = {
        "texts": texts,
        "search_query": search_query,
        "threshold": 0.1,
    }
    url = f"{URL}/keyword_query"
    response = requests.post(url, json=json_data)
    print(response.json())


def qna():
    context = [
        " It was boxing the blade and head off and kicking the blade and leg off.",
        " You was all sure you threw it to cause the distance.",
        " This is not over.",
        " If we had to take this, I'm sorry for him, it's all out of swear.",
        " We don't give our bollocks.",
        " He said that he believes that one of the kicks that he checked is what broke your leg.",
    ]
    context = "".join(context)
    question = "What does he believe in?"

    json_data = {
        "context": context,
        "question": question,
    }
    url = f"{URL}/question_query"
    response = requests.post(url, json=json_data)
    print(response.json())


if __name__ == "__main__":
    qna()
