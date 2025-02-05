from fastapi import APIRouter, HTTPException, Depends, Request
import time
import requests
from typing import Dict, Any

HYPERCLOVA_API_URL = "https://clovastudio.stream.ntruss.com"
HYPERCLOVA_API_KEY = "Bearer nv-f5786fde571f424786ed0823986ca992h3P1"

recommendation_router = APIRouter()

class CompletionExecutor:
    def __init__(self, host, api_key, request_id):
        self._host = host
        self._api_key = api_key
        self._request_id = request_id
        self._max_retries = 5

    def execute(self, completion_request):
        headers = {
            "Authorization": self._api_key,
            "X-NCP-CLOVASTUDIO-REQUEST-ID": self._request_id,
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

PROMPT_identity = [{
        "role": "system",
        "content": """이제 막 유튜버의 꿈을 펼치려고 하는 사람이 있습니다. 이 초보 유튜버는 어떤 영상을 만들어야 할지, 채널의 방향을 어떻게 잡아야 할지 고민하고 있습니다. 초보 유튜버의 성공이 당신의 분석에 달렸습니다. 이 사람에게 맞는 채널 방향성과 정체성을 추천해주세요.
        아래 입력 정보를 바탕으로 이 사람에게 적합한 유튜브 채널 방향성과 정체성을 구체적으로 제안해주세요.
        ### 입력 정보:
        - 관심사 및 취미
        - 선호 콘텐츠 유형
        - 목표 시청자층
        - 영상 제작 가능 시간
        - 장비 및 예산
        - 콘텐츠 아이디어
        - 장기적인 목표
        
        ### 요청 사항:
        - 입력 정보를 종합적으로 분석하고, 각 항목에 초점을 맞추어 구체적인 제안을 작성하세요.
        - 각 정보가 서로 어떻게 연결되는지 고려하여 통합적인 방향성을 제시하세요.
        - 답변은 자연스러운 문장 서술 형태로 작성하되, 모든 입력 정보를 반영하세요.
        
        ### 출력 형식:
        만약 입력 내용이 다음에 해당하면 콘텐츠 추천을 거부합니다:
            - 해피벌룬, 카지노, 도박, 마약, 범죄, 폭력적인 주제 등 불법적이거나 사회적으로 부적절한 요소를 포함하는 경우
            - **금지된 콘텐츠 감지 시 응답 예시:**  
                입력하신 콘텐츠는 유해하거나 법적으로 문제가 될 수 있어 추천해 드릴 수 없습니다. 건전하고 창의적인 유튜브 콘텐츠를 추천해 드릴 수 있도록 다시 입력해 주세요.        
        정보가 부족하거나 명확하지 않다면 다음과 같은 메세지를 출력합니다.:
            - "입력을 다시 확인해 주세요. 모든 항목을 정확히 입력해야 합니다."
        그 외에는 답변에 다음 내용을 반드시 정확히 포함하세요:
            - 관심사와 선호 콘텐츠 유형, 목표 시청자층을 기반으로 한 채널 정체성 제안
            - 영상 제작 가능 시간을 고려한 업로드 일정 추천
            - 장비 및 예산 활용 방안 (제품 추천 포함)
            - 콘텐츠 아이디어의 구체적 활용법
            - 장기적인 목표 달성을 위한 조언"""
    },
    {
        "role": "user", 
        "content": """관심사 및 취미 : {}
        선호 콘텐츠 유형 : {}
        목표 시청자층 : {}
        영상 제작 가능 시간 : {}
        장비 및 예산 : {}
        콘텐츠 아이디어 : {}
        장기적인 목표 : {}
        
        이 정보를 바탕으로 적합한 유튜브 채널 방향성과 정체성을 제안해주세요. 제공된 정보 중 부적절한 내용이 포함되어 있다면 분석을 거부하세요.
        """
    }]
PROMPT_content = [{
        "role": "system",
        "content": """당신은 유튜브 콘텐츠 추천 전문가입니다. 사용자의 입력을 검토한 후, 유효한 경우 최대한 구체적인 3개의 유튜브 콘텐츠 아이디어를 제시하세요.
        출력 형식과 조건은 다음과 같습니다.

        ## 입력 형식
        사용자가 아래 정보를 입력합니다:

        - 영상 제작 분야: (예시: 요리, 여행, 게임, 뷰티 등)
        - 영상 콘텐츠 유형: (예시: 브이로그, 리뷰, 튜토리얼, 예능 등)
        - 주 타겟: (예시: 10-20대 남성, 20-30대 여성)
        영상 주기: (예시: 1주일 3회)
        - 보유 장비 및 예산: (예시: 고프로 1대, 일주일 예산 100만 원 등)
        - 평소에 생각했던 아이디어: (예시: 소개팅 상황극, 일본 여행 브이로그)
        - 유튜버 목표: (예시: 실버 버튼 받기)

        ## 출력 조건
        입력이 적절하지 않을 경우
        - 정보가 부족하거나 명확하지 않다면: "입력을 다시 확인해 주세요. 모든 항목을 정확히 입력해야 합니다."
        - 유해한 콘텐츠(**도박, 마약, 불법 행위, 성인 콘텐츠) 등 유해하거나 법적으로 문제가 될 수 있는 주제는 추천해 드릴 수 없습니다.**  유튜브의 커뮤니티 가이드라인을 준수하는 콘텐츠만 제공됩니다.
        - 만약 입력 내용이 다음에 해당하면 콘텐츠 추천을 거부합니다:
        - 해피벌룬, 카지노, 도박, 마약, 범죄, 폭력적인 주제 등  
        - 불법적이거나 사회적으로 부적절한 요소를 포함하는 경우

        🚫 **금지된 콘텐츠 감지 시 응답 예시:**  
        "입력하신 콘텐츠는 유해하거나 법적으로 문제가 될 수 있어 추천해 드릴 수 없습니다. 건전하고 창의적인 유튜브 콘텐츠를 추천해 드릴 수 있도록 다시 입력해 주세요."

        - 입력이 적절할 경우
        이 외에는 입력된 정보를 바탕으로 가능한 한 **구체적인 콘텐츠 아이디어 3개**를 제공합니다.

        - 주어진 7개 입력 정보를 모두 고려하여 최대한 구체적인 3개의 유튜브 콘텐츠 아이디어를 추천합니다.
        - 콘텐츠는 넘버링하여 제시하고(예: 1. 2. 3.), 콘텐츠 제목을 먼저 적고, **입력된 정보를 바탕**으로 한 근거를 함께 설명합니다.
        - 아이디어는 일반적인 추천이 아니라, 가능한 한 구체적인 주제여야 합니다.
        ❌ "현지인과 인터뷰하기" → ✅ "이집트 카이로 피라미드 앞에서 기념품을 파는 현지인과 인터뷰하기"
        ❌ "음식 리뷰" → ✅ "서울에서 가장 오래된 50년 전통 국밥집 5곳 비교 리뷰"

        이 가이드를 따라, 사용자에게 맞춤형 콘텐츠 아이디어를 제공하세요."""
    },
    {
        "role": "user", 
        "content": """관심사 및 취미 : {}
        선호 콘텐츠 유형 : {}
        목표 시청자층 : {}
        영상 제작 가능 시간 : {}
        장비 및 예산 : {}
        콘텐츠 아이디어 : {}
        장기적인 목표 : {}
        
        이 정보를 바탕으로 적합한 유튜브 채널 방향성과 정체성을 제안해주세요. 제공된 정보 중 부적절한 내용이 포함되어 있다면 분석을 거부하세요.
        """
    }]

def call_hyperclova(answers, PROMPT):
    completion_executor = CompletionExecutor(
        host=HYPERCLOVA_API_URL,
        api_key=HYPERCLOVA_API_KEY,
        request_id='309fa53d16a64d7c9c2d8f67f74ac70d'
    )
    prompt = [PROMPT[0], {"role": "user", "content": PROMPT[1]['content'].format(answers["interest"], answers['contents'], answers['target'], answers['time'], answers['budget'], answers['creativity'], answers['goal'])}]
    request_data = {
                'messages': prompt,
                'topP': 0.8,
                'topK': 0,
                'maxTokens': 1024,
                'temperature': 0.35,
                'repeatPenalty': 5.0,
                'stopBefore': [],
                'includeAiFilters': False,
                'seed': 0
            }
    return completion_executor.execute(request_data)


def identity(answers):
    return call_hyperclova(answers, PROMPT_identity)

def contents(answers):
    return call_hyperclova(answers, PROMPT_content)

@recommendation_router.post("/")
async def recommendation(answers: Dict[str, Any]):
    """
    채널 정체성 컨설팅, 콘텐츠 추천 HCX 답변 출력
    Parameters:
        7가지 질문에 대한 답변(관심사 및 취미, 선호 콘텐츠 유형, 목표 시청자층, 영상 제작 가능 시간, 장비 및 예산, 콘텐츠 아이디어, 장기적인 목표)
    Returns:
        [{
            '정체성 추천':,
            ' 콘텐츠 추천':            
        }]
    """
    try:
        recommended_identity = identity(answers)
        recommended_contents = contents(answers)
        result = {
            '정체성 추천': recommended_identity,
            '콘텐츠 추천': recommended_contents
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

    return result