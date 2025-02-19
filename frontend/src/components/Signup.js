import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './Signup.css';

const Signup = () => {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    confirmPassword: '',
  });

  const navigate = useNavigate();

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  const handleSignup = (e) => {
    e.preventDefault();

    // 비밀번호 확인 로직
    if (formData.password !== formData.confirmPassword) {
      alert('비밀번호가 일치하지 않습니다.');
      return;
    }

    // 🔹 기존 유저 확인
    if (localStorage.getItem(formData.email)) {
      alert('이미 가입된 이메일입니다.');
      return;
    }

    // 🔹 새로운 유저 정보 생성
    const newUser = {
      name: formData.name,
      email: formData.email,
      password: formData.password,
      newUser: true, // 신규 유저 여부
      surveyResponses: {}, // 회원가입 설문
      identitySurveyResponses: {} // 정체성 설문
    };

    // 🔹 이메일을 키로 사용하여 저장
    localStorage.setItem(formData.email, JSON.stringify(newUser));

    alert('회원가입이 완료되었습니다.');
    navigate('/login');
  };

  return (
    <div className="signup-container">
      <h2>회원가입</h2>
      <form className="signup-form" onSubmit={handleSignup}>
        <input
          type="text"
          name="name"
          placeholder="이름"
          className="input-field"
          value={formData.name}
          onChange={handleChange}
          required
        />
        <input
          type="email"
          name="email"
          placeholder="이메일"
          className="input-field"
          value={formData.email}
          onChange={handleChange}
          required
        />
        <input
          type="password"
          name="password"
          placeholder="비밀번호"
          className="input-field"
          value={formData.password}
          onChange={handleChange}
          required
        />
        <input
          type="password"
          name="confirmPassword"
          placeholder="비밀번호 확인"
          className="input-field"
          value={formData.confirmPassword}
          onChange={handleChange}
          required
        />
        <button type="submit" className="signup-button">가입하기</button>
      </form>
      <a href="/login" className="back-to-home">로그인 페이지로 돌아가기</a>
    </div>
  );
};

export default Signup;
