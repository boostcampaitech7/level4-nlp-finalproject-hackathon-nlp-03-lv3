import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { GoogleLogin } from '@react-oauth/google';
import './LoginPopup.css';

const LoginPopup = ({ onClose }) => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    id: '',
    password: ''
  });
  const [errorMessage, setErrorMessage] = useState('');

  // 입력값 변경 핸들러
  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  // 로그인 버튼 클릭 핸들러
  const handleLogin = () => {
    const storedUser = JSON.parse(localStorage.getItem('user'));
  
    if (!storedUser || storedUser.id !== formData.email || storedUser.password !== formData.password) {
      console.log(storedUser)
      console.log(formData)
      setErrorMessage('잘못된 ID 혹은 비밀번호입니다.');
      return;
    }
  
    alert('로그인이 되었습니다!');
  
    if (storedUser.newUser) {
      alert('신규 이용자시군요?');
      navigate('/survey');  // 설문조사 페이지로 이동
    } else {
      navigate('/main');  // 메인 페이지로 이동
    }
  
    onClose();
  };

  // 구글 로그인 성공 및 실패 핸들러
  const handleGoogleSuccess = (response) => {
    console.log('구글 로그인 성공:', response);
    alert('구글 로그인 성공!');
    onClose();
  };

  const handleGoogleFailure = (error) => {
    console.error('구글 로그인 실패:', error);
    setErrorMessage('구글 로그인에 실패했습니다.');
  };

  return (
    <div className="popup-overlay">
      <div className="popup-content">
        <h2 className="popup-title">로그인</h2>

        {errorMessage && <p className="error-message">{errorMessage}</p>}

        <input
          type="text"
          name="id"
          placeholder="아이디"
          className="input-field"
          value={formData.id}
          onChange={handleChange}
        />
        <input
          type="password"
          name="password"
          placeholder="비밀번호"
          className="input-field"
          value={formData.password}
          onChange={handleChange}
        />

        <button className="login-button" onClick={handleLogin}>로그인</button>

        <div className="signup-section">
          아직 회원이 아니신가요? 
          <a onClick={() => navigate('/signup')} className="signup-link"> 회원가입하기</a>
        </div>

        <div className="social-login">
          <GoogleLogin
            onSuccess={handleGoogleSuccess}
            onError={handleGoogleFailure}
          />
        </div>

        <button className="close-button" onClick={onClose}>닫기</button>
      </div>
    </div>
  );
};

export default LoginPopup;
