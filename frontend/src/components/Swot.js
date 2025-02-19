import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './Swot.css';
import Loader from "./Loader";
import axios from 'axios';


const SwotPage = () => {
    const [loading, setLoading] = useState(true);
    const [total_info, setTotalInfo] = useState(null);


    const currentUser = JSON.parse(localStorage.getItem("currentUser")) || {};
    const user_email = currentUser.email;
    const name_temp = JSON.parse(localStorage.getItem(user_email)) || {};
    const channelName = name_temp.surveyResponses?.channelName;

    useEffect(() => {
        const fetchData = async () => {
            try {
                console.log(channelName);
                const uriTotalInfo = `http://10.28.224.177:30635/chatbot/summary/${channelName}`;
                const channelTotalRes = await axios.get(uriTotalInfo);
                setTotalInfo(channelTotalRes.data);
            } catch (error) {
                console.error("Error fetching data: ", error);
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, [channelName]);

    if (loading) {
        return <Loader message="데이터를 불러오는 중..." />;
    }

    return (
        <div className="main-container">
            {/* 종합 분석 결과 */}
            <div className="summary-box">
                <h1>종합 분석 결과</h1>
                {total_info ? (
                    <div className="analysis-box">{total_info}</div>
                ) : (
                    <p>Loading...</p>
                )}
            </div>

            {/* 서비스 카드 */}
            <div className="services">
                <ServiceCard
                    title="채널 성과 분석결과"
                    description="조회수, 구독자 증가율, 노출 클릭률 등 채널의 전반적인 성과를 분석 받아보세요."
                    link="/main/Swot/Performance"
                    imgSrc='/performance.png'
                />

                <ServiceCard
                    title="시청자 참여도 분석결과"
                    description="좋아요, 댓글, 공유 등 시청자들의 참여도를 분석받아보세요."
                    link="/main/Swot/Engagement"
                    imgSrc='/engagement.png'
                />

                <ServiceCard
                    title="채널 수익성 분석결과"
                    description="광고 수익, 광고 영상의 마케팅 영향력 등 채널의 수익성에 대한 분석받아보세요."
                    link="/main/Swot/Revenue"
                    imgSrc='/revenue.png'
                />
            </div>
        </div>
    );
};

const ServiceCard = ({ title, description, link , imgSrc}) => {
    const navigate = useNavigate();

    const handleClick = () => {
        if (link) {
            navigate(link);
        }
    };

    return (
        <div className="service-card" onClick={handleClick} style={{ cursor: 'pointer' }}>
            <h3>{title}</h3>
            <img src={imgSrc}></img>
            <p>{description}</p>
        </div>
    );
};

export default SwotPage;
