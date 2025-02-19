import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import "./Identity.css";
import Loader from "./Loader";

const Identity = () => {
  const [surveyCompleted, setSurveyCompleted] = useState(false);
  const [identityResult, setIdentityResult] = useState(null);
  const [recommendations, setRecommendations] = useState([]); // 🔹 초기값을 빈 배열로 설정
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        // 🔹 현재 로그인한 사용자 가져오기
        const currentUser = JSON.parse(localStorage.getItem("currentUser")) || {};
        if (!currentUser.email) {
          alert("로그인이 필요합니다.");
          navigate("/login");
          return;
        }

        // 🔹 해당 사용자의 데이터 가져오기
        const userData = JSON.parse(localStorage.getItem(currentUser.email)) || {};
        const surveyResponses = userData.surveyResponses || {};
        const identitySurveyResponses = userData.identitySurveyResponses || null;

        // 🔹 설문조사 여부 확인
        setSurveyCompleted(identitySurveyResponses && Object.keys(identitySurveyResponses).length > 0);

        if (identitySurveyResponses && Object.keys(identitySurveyResponses).length > 0) {
          // 🔹 API 요청 데이터 구성
          const requestData = {
            interest: identitySurveyResponses?.preferredContentType || "미입력",
            contents: surveyResponses?.contentCategory || "미입력",
            target: `${surveyResponses?.targetAge || "미입력"} ${surveyResponses?.targetGender || ""}`,
            time: identitySurveyResponses?.videoCreationTime || "미입력",
            budget: identitySurveyResponses?.equipmentBudget || "미입력",
            creativity: identitySurveyResponses?.contentIdeas || "미입력",
            goal: identitySurveyResponses?.longTermGoal || "미입력"
          };

          console.log("📤 API 요청 데이터:", requestData);

          // 🔹 Axios API 요청 (try-catch-finally 적용)
          try {
            const response = await axios.post("http://10.28.224.177:30635/recommendation/", requestData, {
              headers: { "Content-Type": "application/json" }
            });

            console.log("📥 API 응답:", response.data);

            setIdentityResult(response.data["정체성 추천"]);

            // 🔹 응답 데이터를 배열로 변환하여 저장
            const recs = response.data["콘텐츠 추천"];
            setRecommendations(Array.isArray(recs) ? recs : [recs]); // 🔥 배열이 아니면 배열로 변환
          } catch (error) {
            console.error("❌ API 요청 실패:", error);
          }
        }
      } catch (error) {
        console.error("❌ 데이터 가져오기 실패:", error);
      } finally {
        // 🔹 모든 작업이 끝난 후 로딩 상태 해제
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) {
    return <Loader message="데이터를 불러오는 중..." />;
  }

  return (
    <div className="identity-container">
      <div className="center-content">
        <button className="main-retry-button" onClick={() => navigate("/main/identity/survey")}>
          설문조사 다시하기
        </button>
      </div>

      {/* 블러 처리된 오버레이 (설문 미완료 시) */}
      {!surveyCompleted && (
        <div className="overlay">
          <p>정체성 파악을 위한 설문조사를 진행해주세요.</p>
          <button onClick={() => navigate("/main/identity/survey")}>설문조사 하러가기</button>
        </div>
      )}

      {/* 정체성 평가 결과 박스 */}

      <div className={`main-identity-result ${!surveyCompleted ? "blurred" : ""}`}>
        <h2>정체성 평가 결과</h2>
        {identityResult ? (
          identityResult.split("\n").map((line, index) => (
            <p key={index}>{line}</p>
          ))
        ) : (
          <p>정체성 평가 결과를 불러오는 중입니다...</p>
        )}
      </div>

      {/* 콘텐츠 추천 결과 제목 */}

      {/* 콘텐츠 추천 결과 박스 */}
      <div className="main-recommend-box">
        <h2>콘텐츠 추천 결과</h2>
        {recommendations.length > 0 ? (
          recommendations.map((line, index) => (
            <span key={index}>{line}</span>
          ))
        ) : (
          <p>콘텐츠 추천 결과를 불러오는 중입니다...</p>
        )}
      </div>
    </div>
  );
};

export default Identity;
