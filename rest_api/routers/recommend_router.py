from fastapi import APIRouter, HTTPException, Depends, Request
import time
import requests
from typing import Dict, Any
from prompts.recommend_prompt import PROMPT_identity, PROMPT_content
from rest_api.clova_api import call_hyperclova

recommendation_router = APIRouter()

def identity_prompt(answers):
    return [PROMPT_identity[0], {"role": "user", "content": PROMPT_identity[1]['content'].format(answers["interest"], answers['contents'], answers['target'], answers['time'], answers['budget'], answers['creativity'], answers['goal'])}]

def contents_prompt(answers):
    return [PROMPT_content[0], {"role": "user", "content": PROMPT_content[1]['content'].format(answers["interest"], answers['contents'], answers['target'], answers['time'], answers['budget'], answers['creativity'], answers['goal'])}]

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
    print('answrs : ', answers)
    try:
        recommended_identity = call_hyperclova(identity_prompt(answers), max_tokens=1024)
        recommended_contents = call_hyperclova(contents_prompt(answers), max_tokens=1024)
        result = {
            '정체성 추천': recommended_identity,
            '콘텐츠 추천': recommended_contents
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

    return result