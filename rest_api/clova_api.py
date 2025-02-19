# -*- coding: utf-8 -*-
import requests
import time
import json
from fastapi import HTTPException

HYPERCLOVA_API_URL = "enter your api url"
HYPERCLOVA_API_KEY = "enter your api key"

class CompletionExecutor:
    def __init__(self, host, api_key):
        self._host = host
        self._api_key = api_key
        self._max_retries = 5

    def execute(self, completion_request):
        headers = {
            "Authorization": self._api_key,
            "Content-Type": "application/json; charset=utf-8",
        }

        retries = 0  # 현재 재시도 횟수
        while retries < self._max_retries:
            # POST 요청 보내기
            response = requests.post(
                self._host + "/testapp/v1/chat-completions/HCX-003",
                headers=headers,
                json=completion_request
            )

            # 응답 상태 확인
            if response.status_code == 200:
                response_data = response.json()
                return response_data['result']["message"]["content"]
            elif response.status_code == 429:  # Too Many Requests
                print(f"Rate limit exceeded. Retrying after {1} seconds...")
                time.sleep(10)
                print(response.json())
                retries+=1
            else:
                raise HTTPException(status_code=response.status_code, detail=response.text)

def call_hyperclova(PROMPT, temperature: int = 0.35, max_tokens: int = 150):
    completion_executor = CompletionExecutor(
        host=HYPERCLOVA_API_URL,
        api_key=HYPERCLOVA_API_KEY,
    )
    request_data = {
                'messages': PROMPT,
                'topP': 0.8,
                'topK': 0,
                'maxTokens': max_tokens,
                'temperature': temperature,
                'repeatPenalty': 2.5,
                'stopBefore': [],
                'includeAiFilters': False,
                'seed': 0
            }
    return completion_executor.execute(request_data)

# CLOVA Speech API 요청
def clova_speech_stt(file_path):
    headers = {"X-CLOVASPEECH-API-KEY": "enter your api key"}
    files = {
        "media": open(file_path, "rb"),
        "params": (None, json.dumps({"language": "ko-KR", "completion": "sync"}).encode("UTF-8"), "application/json"),
    }
    response = requests.post(
        "https://clovaspeech-gw.ncloud.com/external/v1/10094/9409a0f5da32cf23f7c4ecb52ef04a38ea2e6612670a3a4207613b2523ecf473/recognizer/upload",
        headers=headers,
        files=files,
    )
    return response.json()
