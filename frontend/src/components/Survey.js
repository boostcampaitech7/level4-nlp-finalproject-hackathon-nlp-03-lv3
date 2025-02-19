import React, { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import "./Survey.css";

const questions = [
  { type: "multiple_choice", question: "유튜브 채널이 있으신가요?", options: ["예", "아니오"], key: "hasChannel" },
  { type: "text", question: "유튜브 채널 이름을 입력해주세요.", key: "channelName", condition: "예" },
  { type: "text", question: "채널 주 컨텐츠는 무엇인가요?", key: "contentCategory" },
  { type: "multiple_choice", question: "주 타겟 구독자 연령은?", options: ["10-20", "20-30", "30-40"], key: "targetAge" },
  { type: "multiple_choice", question: "주 타겟 구독자 성별은?", options: ["남성", "여성", "그 외"], key: "targetGender" }
];

const Survey = () => {
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
    setFormData(storedUserData.surveyResponses || {});
  }, []);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleAnswer = (answer) => {
    const currentQuestion = questions[currentQuestionIndex];
    const newFormData = { ...formData, [currentQuestion.key]: answer };

    let nextQuestionIndex = currentQuestionIndex + 1;

    // "아니오" 선택 시 "유튜브 채널 이름 입력" 질문 건너뛰기
    if (currentQuestion.key === "hasChannel" && answer === "아니오") {
      nextQuestionIndex += 1; // 다음 질문이 "채널 이름 입력"이므로 이를 스킵
    }

    setFormData(newFormData);

    const newMessages = [
      ...messages,
      { sender: "user", text: answer }
    ];

    if (nextQuestionIndex < questions.length) {
      newMessages.push({ sender: "bot", text: questions[nextQuestionIndex].question });
      setCurrentQuestionIndex(nextQuestionIndex);
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

      // 🔹 기존 데이터 유지하면서 `surveyResponses` 업데이트
      const updatedUserData = {
        ...existingData,
        newUser: false,
        surveyResponses: newFormData
      };

      // 🔹 업데이트된 데이터 저장
      localStorage.setItem(userEmail, JSON.stringify(updatedUserData));
      console.log(localStorage)

      newMessages.push({ sender: "bot", text: "설문이 완료되었습니다! 감사합니다. 😊" });

      setTimeout(() => navigate("/main"), 2000);
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
  const placeholderText = "답변을 입력하세요...";

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
        currentQuestion.type === "multiple_choice" ? (
          <div className="options">
            {currentQuestion.options.map((option, index) => (
              <button key={index} onClick={() => handleAnswer(option)}>
                {option}
              </button>
            ))}
          </div>
        ) : (
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
        )
      ) : null}
    </div>
  );
};

export default Survey;
