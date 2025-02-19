import uvicorn
from fastapi import FastAPI
from sqlalchemy import create_engine
from fastapi.middleware.cors import CORSMiddleware
from rest_api.routers.dashboard_router import dashboard_router
from rest_api.routers.chatbot_router import chatbot_router
from rest_api.routers.sensitive_router import sensitive_router
from rest_api.routers.recommend_router import recommendation_router
# DB 접속 정보
host = "10.28.224.177"
port = 30634
database = "postgres"
username = "postgres"
password = "0104"

# SQLAlchemy 엔진 생성
engine = create_engine(f"postgresql+psycopg2://{username}:{password}@{host}:{port}/{database}")


def create_app() -> FastAPI:
    """
    FastAPI 애플리케이션을 생성하고 라우터를 등록합니다.
    """
    app = FastAPI(
        title="YouTube Channel Analytics API",
        version="1.0.0",
        description="APIs for analyzing YouTube channel profitability and audience engagement.",
    )

    # CORS 설정 추가 (필요에 따라 도메인 제한 가능)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 모든 도메인 허용 (보안 필요시 특정 도메인으로 제한)
        allow_credentials=True,
        allow_methods=["*"],  # 모든 HTTP 메서드 허용
        allow_headers=["*"],  # 모든 헤더 허용
    )

    # 라우터 등록
    app.include_router(dashboard_router, prefix="/dashboard", tags=["Dashboard"])
    app.include_router(chatbot_router, prefix="/chatbot", tags=["Chatbot"])
    app.include_router(sensitive_router, prefix="/sensitive", tags=["sensitive"])
    app.include_router(recommendation_router, prefix="/recommendation", tags=["Recommend"])

    # 앱 상태에 DB 엔진 저장 (라우터에서 접근 가능)
    app.state.db_engine = engine
    return app


# FastAPI 앱 인스턴스 생성
app = create_app()


@app.on_event("startup")
async def startup_event():
    """
    서버 시작 시 실행되는 작업 (예: 데이터베이스 연결, 초기화 작업)
    """
    # 여기에 필요한 초기화 작업을 추가
    print("Server is starting up...")


@app.on_event("shutdown")
async def shutdown_event():
    """
    서버 종료 시 실행되는 작업 (예: 리소스 정리)
    """
    print("Server is shutting down...")


if __name__ == "__main__":
    uvicorn.run(app, host="10.28.224.177", port=30635)
