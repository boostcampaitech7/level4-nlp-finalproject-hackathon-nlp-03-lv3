import React, { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import "./SurveyChatbot.css";

const questions = [
  { key: "preferredContentType", type: "text", question: "선호하는 콘텐츠 유형은 무엇인가요?", examples: "예: 브이로그, 리뷰, 튜토리얼, 예능 등" },
  { key: "videoCreationTime", type: "text", question: "영상 제작 가능 시간은 어느 정도인가요?", examples: "예: 주 5시간, 주 10시간 등" },
  { key: "equipmentBudget", type: "text", question: "보유하고 있는 장비 및 예산을 입력해주세요.", examples: "예: 편집 프로그램, 고프로, 캡쳐보드, 최신 스마트폰 등" },
  { key: "contentIdeas", type: "text", question: "평소 생각했던 콘텐츠 아이디어가 있나요?", examples: "예: 소개팅 상황극, 일본 여행 브이로그 등" },
  { key: "longTermGoal", type: "text", question: "유튜브 운영 목표는 무엇인가요?", examples: "예: 실버버튼 받기, 1년 내 수익 창출 허가받기, 협찬 유치하기 등" }
];

const SurveyChatbot = () => {
  const [messages, setMessages] = useState([]);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [formData, setFormData] = useState({});
  const [inputValue, setInputValue] = useState("");
  const chatEndRef = useRef(null);
  const navigate = useNavigate();

  useEffect(() => {
    setMessages([{ sender: "bot", text: questions[0].question }]);

    // 🔹 현재 로그인한 사용자 가져오기
    const currentUser = JSON.parse(localStorage.getItem("currentUser")) || {};
    if (!currentUser.email) {
      alert("로그인이 필요합니다.");
      navigate("/login");
      return;
    }

    // 🔹 기존 설문 응답 가져오기
    const storedUserData = JSON.parse(localStorage.getItem(currentUser.email)) || {};
    setFormData(storedUserData.identitySurveyResponses || {});
  }, []);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleAnswer = (answer) => {
    const currentQuestion = questions[currentQuestionIndex];
    const newFormData = { ...formData, [currentQuestion.key]: answer };

    setFormData(newFormData);

    let newMessages = [...messages, { sender: "user", text: answer }];

    if (currentQuestionIndex < questions.length - 1) {
      newMessages.push({ sender: "bot", text: questions[currentQuestionIndex + 1].question });
      setCurrentQuestionIndex(currentQuestionIndex + 1);
    } else {
      // 🔹 현재 로그인한 사용자 가져오기
      const currentUser = JSON.parse(localStorage.getItem("currentUser")) || {};
      const userEmail = currentUser.email;

      if (!userEmail) {
        alert("로그인이 필요합니다.");
        navigate("/login");
        return;
      }

      // 🔹 해당 사용자의 기존 데이터 가져오기
      const existingData = JSON.parse(localStorage.getItem(userEmail)) || {};

      // 🔹 기존 데이터 유지하면서 `identitySurveyResponses` 업데이트
      const updatedUserData = {
        ...existingData,
        identitySurveyResponses: newFormData
      };

      // 🔹 업데이트된 데이터 저장
      localStorage.setItem(userEmail, JSON.stringify(updatedUserData));

      newMessages.push({ sender: "bot", text: "설문이 완료되었습니다! 감사합니다. 😊" });

      setTimeout(() => navigate("/main/identity"), 2000);
    }

    setMessages(newMessages);
    setInputValue("");
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter" && inputValue.trim()) {
      handleAnswer(inputValue.trim());
    }
  };

  const currentQuestion = questions[currentQuestionIndex] || null;
  const placeholderText = currentQuestion?.examples || "메시지를 입력하세요...";

  return (
    <div className="chatbot-container">
      <div className="chat-window">
        {messages.map((msg, index) => (
          <div key={index} className={`chat-bubble ${msg.sender}`}>
            {msg.text}
          </div>
        ))}
        <div ref={chatEndRef} />
      </div>

      {currentQuestion ? (
        <div className="input-area">
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyPress}
            placeholder={placeholderText}
          />
          <button onClick={() => handleAnswer(inputValue)}>전송</button>
        </div>
      ) : null}
    </div>
  );
};

export default SurveyChatbot;
