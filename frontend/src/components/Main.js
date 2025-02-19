import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './Main.css';

const MainPage = () => {
  const [hasYouTubeChannel, setHasYouTubeChannel] = useState(null);

  useEffect(() => {
    // 🔹 현재 로그인한 사용자 가져오기
    const currentUser = JSON.parse(localStorage.getItem("currentUser")) || {};
    const user_email = currentUser.email; // 이메일 문자열 가져오기
    const userInfo = JSON.parse(localStorage.getItem(user_email)) || {};

    console.log(userInfo);

    setHasYouTubeChannel(userInfo.surveyResponses?.hasChannel === '예');
  }, []);

  return (
    <div className="main-container">
      <div className='main-title-container'>
        <h1>Hyper CLOVA X를 통한 여러 인사이트를 경험해보세요!</h1>
        <p>서비스를 선택해주세요!</p>
      </div>
      <div className="services">
        <ServiceCard
          title="맞춤형 채널 정체성 진단받아보기"
          description="신규 크리에이터라면, 
Hyper CLOVA X 챗봇과의 대화를 통해 
본인만의 채널정체성을 받아보세요. 
목표한 타겟층을 위해 어떤 방향으로 채널을 키워나갈지 방향성을 제공받아보세요!"
          link='/main/identity'
          imgSrc='/channel_identity.png'
        />
        {hasYouTubeChannel && (
          <ServiceCard
            title="내 유튜브 채널 SWOT 분석 받기"
            description="기존 크리에이터라면,
Hyper CLOVA X의 자료 분석을 통해
채널 분석을 받아보세요.
여러 지표에 대한 채널의 장,단점, 이를 
극복할 여러 기회 방법을 제공받아보세요!"
            link='/main/Swot'
            imgSrc='/channel_swot.png'

          />
        )}
        <ServiceCard
          title="영상 업로드 전 민감도 분석하기"
          description="영상 업로드전이라면,
Hyper CLOVA X의 민감도 분석을 통해
영상을 검사 받아보세요.
영상에서 발생할 수 있는 논란을 
카테고리에 맞춤형으로 검토받아보세요!"
          link='/main/sense'
          imgSrc='/video_analysis.png'

        />
      </div>
    </div>
  );
};

const ServiceCard = ({ title, description, link, imgSrc }) => {
  const navigate = useNavigate();

  const handleClick = () => {
    if (link) {
      navigate(link); // link가 있으면 해당 경로로 이동
    }
  };

  return (
    <div className="service-card" onClick={handleClick} style={{ cursor: 'pointer' }}>
      <h3>{title}</h3>
      <img src={imgSrc}></img>
      
      <p>{description.split("\n").map((line, index) => (
        <React.Fragment key={index}>
          {line}
          <br />
        </React.Fragment>
      ))}</p>
    </div>
  );
};

export default MainPage;