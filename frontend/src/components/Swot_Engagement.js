import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Bar, Doughnut } from 'react-chartjs-2';
import axios from 'axios';
import Loader from "./Loader";
import './Swot_Engagement.css';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  scales,
} from "chart.js";

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  ArcElement,
  Title,
  Tooltip,
  Legend
);
const createOverlapChartData = (uploadTimes, viewTimes) => {
  const totalSegments = 24; // 0~23시를 15도 단위로 나눔
  const segmentAngles = Array.from({ length: totalSegments }, (_, i) => [i, i + 1]); // [0,1], [1,2], ..., [23,24]
  const backgroundColors = Array(totalSegments).fill('#D3D3D3'); // 기본값: 아무것도 아닌 시간 (회색)
  const labels = Array(totalSegments).fill(''); // 라벨 초기화

  // 겹치는 시간 확인 및 색상 지정
  uploadTimes.forEach(([uStart, uEnd]) => {
    viewTimes.forEach(([vStart, vEnd]) => {
      const overlapStart = Math.max(uStart, vStart);
      const overlapEnd = Math.min(uEnd, vEnd);

      if (overlapStart < overlapEnd) {
        for (let i = overlapStart; i < overlapEnd; i++) {
          backgroundColors[i] = '#8b0be0'; // 겹치는 시간 (보라색)
          labels[i] = `${i}:00 - ${i + 1}:00`; // 겹치는 시간 라벨
        }
      }
    });
  });

  // 업로드 시간 확인 및 색상 지정
  uploadTimes.forEach(([start, end]) => {
    for (let i = start; i < end; i++) {
      if (backgroundColors[i] === '#D3D3D3') {
        // 겹치는 시간이 아니면 업로드 시간으로 설정
        backgroundColors[i] = '#4D5EF8'; // 업로드 시간 (파란색)
        labels[i] = `${i}:00 - ${i + 1}:00`; // 업로드 시간 라벨
      }
    }
  });

  // 시청 시간 확인 및 색상 지정
  viewTimes.forEach(([start, end]) => {
    for (let i = start; i < end; i++) {
      if (backgroundColors[i] === '#D3D3D3') {
        // 겹치는 시간, 업로드 시간이 아니면 시청 시간으로 설정
        backgroundColors[i] = '#FF5F7E'; // 시청 시간 (빨간색)
        labels[i] = `${i}:00 - ${i + 1}:00`; // 시청 시간 라벨
      }
    }
  });

  // 각 조각은 15도씩 차지하므로 데이터를 1로 설정
  const data = Array(totalSegments).fill(1);

  return {
    datasets: [
      {
        data,
        backgroundColor: backgroundColors,
        borderWidth: 0,
      },
    ],
    labels, // 각 조각에 해당하는 라벨
  };
};

const chartOptions = {
  plugins: {
    tooltip: {
      callbacks: {
        label: (context) => {
          const index = context.dataIndex;
          return context.chart.data.labels[index]; // 툴팁에서 라벨 표시
        },
      },
    },
    legend: {
      display: false
    },
  },
  circumference: 360, // 전체 원 사용
};


const SwotEngagement = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);

  const currentUser = JSON.parse(localStorage.getItem("currentUser")) || {};
  const user_email = currentUser.email;
  const name_temp= JSON.parse(localStorage.getItem(user_email))||{};
  const channelName=name_temp.surveyResponses?.channelName;

  const target_gender = name_temp?.surveyResponses?.targetGender;
  const target_age = name_temp?.surveyResponses?.targetAge;

  // 대시보드 변수
  const [channelEngagement, setChannelEngagement] = useState(null);
  const [liveComparisonData, setLiveComparisonData] = useState(null);
  const [commentComparisonData, setCommentComparisonData] = useState(null); // 대댓글 수 BarChart
  const [averageLiveView, setAverageLiveView] = useState(null);
  const [targetStrategy, setTargetStrategy] = useState(null);
  const [doughnutData, setDoughnutData] = useState(null);
  const [overlapChartData, setOverlapChartData] = useState(null);

  // 챗봇 변수
  const [analysisEngagement, setAnalysisEngagement] = useState(null);
  const [analysisCommunication, setAnalysisCommunication] = useState(null);
  const [analysisTarget, setAnalysisTarget] = useState(null);

  // API 요청
  useEffect(() => {
    const fetchData = async () => {
      try {
        // 대시보드 URI
        const uriChannelEngagement = `http://10.28.224.177:30635/dashboard/audience/engagement/${channelName}`;
        const uriLiveComparison = `http://10.28.224.177:30635/dashboard/audience/creator-communication/${channelName}`;
        const uriTargetStrategy = `http://10.28.224.177:30635/dashboard/audience/targeting-strategy/${channelName}`
        //챗봇 URI
        const uriChatbot_engagement = `http://10.28.224.177:30635/chatbot/audience/engagement-analysis/${channelName}`;
        const uriChatbot_communication = `http://10.28.224.177:30635/chatbot/audience/communication-analysis/${channelName}`;
        const uriChatbot_targeting = `http://10.28.224.177:30635/chatbot/audience/targeting-analysis/${channelName}`;

        // 데이터 병렬 호출
        const [
          channelEngagementRes,
          liveComparisonRes,
          targetStrategyRes,
          analysisEngagementRes,
          analysisCommunicationRes,
          analysisTargetRes,
        ] = await Promise.all([
          axios.get(uriChannelEngagement),
          axios.get(uriLiveComparison),
          axios.get(uriTargetStrategy),
          axios.get(uriChatbot_engagement),
          axios.get(uriChatbot_communication),
          axios.get(uriChatbot_targeting),
        ]);

        // 상태 업데이트
        setChannelEngagement(channelEngagementRes.data[0]);
        setAnalysisEngagement(analysisEngagementRes.data);
        const liveComparison = liveComparisonRes.data[0];
        setAverageLiveView(liveComparisonRes.data[0]);
        setAnalysisCommunication(analysisCommunicationRes.data);
        setTargetStrategy(targetStrategyRes.data[0]);
        setAnalysisTarget(analysisTargetRes.data);

        const chartData = createOverlapChartData(
          targetStrategyRes.data[0]["영상 업로드 시간"],
          targetStrategyRes.data[0]["영상 시청 시간"]
        );
        setOverlapChartData(chartData);

        const adRatio = parseFloat(targetStrategyRes.data[0]["일반/광고 영상 비율"].replace("%", "")) / 100;
        const doughnutData = {
          datasets: [
            {
              data: [1 - adRatio, adRatio],
              backgroundColor: ["#A2D2FF", "#FFAFCC"],
              hoverOffset: 4,
            },
          ],
        };
        setDoughnutData(doughnutData);

        setLiveComparisonData({
          labels: ["내 라이브 수", "경쟁 채널 라이브 수"],
          datasets: [
            {
              label: "라이브 수",
              data: [liveComparison["라이브 수"], liveComparison["경쟁 채널 라이브 수"]],
              backgroundColor: ["#EDF9DE", "#FBD8A8"],
            },
          ],
        });
        // 대댓글 수 BarChart 데이터 설정
        setCommentComparisonData({
          labels: ["내 대댓글 수", "경쟁 채널 대댓글 수"],
          datasets: [
            {
              label: "대댓글 수",
              data: [
                liveComparison["대댓글 수"], liveComparison["경쟁 채널 평균 대댓글 수"],
              ],
              backgroundColor: ["#EDF9DE", "#FBD8A8"],
            },
          ],
        });

      }
      catch (error) {
        console.error("Error fetching data:", error);
      }
      finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) {
    return <Loader  message="데이터를 불러오는 중..." />;
  }

  const calculateRotation = (score, min, max) => {
    // '%' 제거 및 숫자 변환 함수
    const parsePercentage = (value) => {
      if (typeof value === "string" && value.includes("%")) {
        return parseFloat(value.replace("%", ""));
      }
      return parseFloat(value); // 숫자로 변환
    };

    // 각 값 변환 및 기본값 설정
    const normalizedScore = parsePercentage(score) || 0;
    const numberizedMin = parsePercentage(min) || 0;
    const numberizedMax = parsePercentage(max) || 1; // max 기본값을 1로 설정

    // min과 max가 같은 경우 처리 (0으로 나누는 경우 방지)
    if (numberizedMax === numberizedMin) {
      return 0; // 기본 각도로 설정
    }

    // 점수를 각도로 변환
    return ((normalizedScore - numberizedMin) / (numberizedMax - numberizedMin)) * 180 - 90;
  };

  const formatScore = (score) => {
    // 소수점 2자리로 표시
    const normalizedScore = parseFloat(score.replace("%", ""));
    return normalizedScore.toFixed(2) + "%";
  };

  return (
    <div className="engagement-container">
      {/* Toggle 버튼 영역 */}
      <div className="toggle-buttons">
        <button className="toggle-button" onClick={() => navigate('/main/Swot/Performance')}>
          채널 성과
        </button>
        <button className="toggle-button active" onClick={() => navigate('/main/Swot/Engagement')}>
          시청자 참여도
        </button>
        <button className="toggle-button" onClick={() => navigate('/main/Swot/Revenue')}>
          채널 수익성
        </button>
      </div>

      <div className="engagement-grid-container">
        {/*게이지 차트 (시청자 참여도)*/}
        <div className='gauge_wrapper'>
          {/* 좋아요 비율 */}
          <div className="gauge">
            <div className="gauge-background"></div>
            <div
              className="gauge-arrow"
              style={{
                transform: `rotate(${calculateRotation(
                  channelEngagement["좋아요 비율"],
                  channelEngagement["최소 좋아요 비율"],
                  channelEngagement["최대 좋아요 비율"]
                )}deg)`,
              }}
            ></div>
            <div className="gauge-cover">
              <span className="score-text">
                {formatScore(channelEngagement["좋아요 비율"])}
              </span>
              <span className="label-text">좋아요 비율</span>
            </div>
          </div>


          {/* 댓글 비율 */}
          <div className="gauge">
            <div className="gauge-background"></div>
            <div
              className="gauge-arrow"
              style={{
                transform: `rotate(${calculateRotation(
                  channelEngagement["댓글 비율"],
                  channelEngagement["최소 댓글 비율"],
                  channelEngagement["최대 댓글 비율"]
                )}deg)`,
              }}
            ></div>
            <div className="gauge-cover">
              <span className="score-text">
                {formatScore(channelEngagement["댓글 비율"])}
              </span>
              <span className="label-text">댓글 비율</span>
            </div>
          </div>

          {/* 공유 비율 */}
          <div className="gauge">
            <div className="gauge-background"></div>
            <div
              className="gauge-arrow"
              style={{
                transform: `rotate(${calculateRotation(
                  channelEngagement["공유 비율"],
                  channelEngagement["최소 공유 비율"],
                  channelEngagement["최대 공유 비율"]
                )}deg)`,
              }}
            ></div>
            <div className="gauge-cover">
              <span className="score-text">
                {formatScore(channelEngagement["공유 비율"])}
              </span>
              <span className="label-text">공유 비율</span>
            </div>
          </div>
        </div>

        {/*시청자 참여도에 대한 하이퍼 클로바 응답*/}
        <div className='engagement_analysis'>
          <h3>시청자 참여도에 대한 분석결과</h3>
          {analysisEngagement ? (<div className='analysis-box'>{analysisEngagement}</div>) : (<p>Loading...</p>)}
        </div>

        {/* 크레이터 소통활동 그래프 */}
        <div className="communication_wrapper">
          {/* 내 라이브 수 vs 경쟁 채널 라이브 수 */}
          <div className="graph-section">
            <h3>내 라이브 수 vs 경쟁 채널 라이브 수</h3>
            <div className='view_chart'>
              {liveComparisonData && (
                <Bar
                  data={liveComparisonData}
                  options={{
                    responsive: true,
                    plugins: { legend: { display: false } },
                    scales: {
                      x: { ticks: { font: { size: 12 } } },
                      y: { ticks: { font: { size: 12 } } },
                    },
                  }}
                  height={250}
                  width={300}
                />
              )}
            </div>

          </div>
          {/* 내 대댓글 수 vs 경쟁 채널 평균 대댓글 수 */}
          <div className="graph-section">
            <h3>내 대댓글 수 vs 경쟁 채널 평균 대댓글 수</h3>
            <div className='view_chart'>
              {commentComparisonData && (
                <Bar
                  data={commentComparisonData}
                  options={{
                    responsive: true,
                    plugins: { legend: { display: false } },
                    scales: {
                      x: { ticks: { font: { size: 12 } } },
                      y: { ticks: { font: { size: 12 } } },
                    },
                  }}
                  height={250}
                  width={300}
                />
              )}
            </div>

          </div>
          {/* 라이브 평균 시청자 수 */}
          <div className="gauge">
            <div className="communication-gauge-background"></div>
            <div
              className="gauge-arrow"
              style={{
                transform: `rotate(${calculateRotation(
                  averageLiveView['라이브 평균 시청자 수'],
                  0,
                  averageLiveView["라이브 최대 시청자 수"]
                )}deg)`,
              }}
            ></div>
            <div className="gauge-cover">
              <span className="score-text">
                {averageLiveView['라이브 평균 시청자 수']}명
              </span>
              <span className="label-text">라이브 평균 시청자 수</span>
            </div>
          </div>


        </div>

        {/* 소통활동에 대한 분석 */}
        <div className='communication_analysis'>
          <h3>시청자와의 소통활동에 대한 분석결과</h3>
          {analysisCommunication ? (<div className='analysis-box'>{analysisCommunication}</div>) : (<p>Loading...</p>)}
        </div>

        {/* 키워드 섹션 */}
        <div className="keywords-section">
          {/* keyword 그림 */}
          <div className="keywords-container">
            {targetStrategy &&
              targetStrategy["키워드"]
                .split(",")
                .map((keyword, index) => (
                  <div key={index} className="keyword-bubble">
                    {keyword.trim()}
                  </div>
                ))}
          </div>
          {/* 일반/광고 영상 비율 */}
          <div className="doughnut-chart">
            <h3>일반/광고 영상 비율</h3>
            {doughnutData && (
              <Doughnut data={doughnutData} options={{ plugins: { legend: { display: false } } }}
              />
            )}
            <div className='doughnut-label'>
              <div className='label-item'>
                <span className='color-indicator' style={{ backgroundColor: "#A2D2FF" }}></span>
                일반 영상
              </div>
              <div className='label-item'>
                <span className='color-indicator' style={{ backgroundColor: "#FFAFCC" }}></span>
                광고 영상
              </div>
            </div>
          </div>
          {/* 영상 시청 시간, 업로드 시간 */}
          <div className='doughnut-chart'>
            <h3>업로드 시간 및 시청 시간 도넛 차트</h3>
            {overlapChartData ? (
              <Doughnut data={overlapChartData} options={chartOptions} />
            ) : (
              <p>데이터를 불러오는 중...</p>
            )}
            <div className='doughnut-label'>
              <div className='label-item'>
                <span className='color-indicator' style={{ backgroundColor: '#4D5EF8' }}></span>
                업로드 시간
              </div>
              <div className='label-item'>
                <span className='color-indicator' style={{ backgroundColor: '#FF5F7E' }}></span>
                시청 시간
              </div>
              <div className='label-item'>
                <span className='color-indicator' style={{ backgroundColor: '#8b0be0' }}></span>
                겹치는 시간
              </div>
            </div>
          </div>

          {/* 타겟 연령층과 성별 */}
          <div className='target_gender_section'>
            <div className='target-container'>
              <img
                src={target_gender === '남성' ? '/man.png' : '/woman.png'}
                alt={target_gender}
                className='target-image'
              />
              <span className='target-age'>{target_age}대</span>
            </div>
          </div>
        </div>

        {/*시청자 타겟팅에 대한 하이퍼 클로바 응답*/}
        <div className='target_analysis'>
          <h3>시청자 타겟팅에 대한 분석결과</h3>
          {analysisTarget ? (<div className='analysis-box'>{analysisTarget}</div>) : (<p>Loading...</p>)}
        </div>

      </div >


    </div>
  );
};

export default SwotEngagement;
