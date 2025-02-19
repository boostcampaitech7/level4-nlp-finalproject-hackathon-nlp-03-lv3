import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Bar, Line, Doughnut } from "react-chartjs-2"; // 차트 컴포넌트 가져오기
import axios from "axios";
import Loader from "./Loader";
import "./Swot_Performance.css";
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

const Performance = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [channelInfo, setChannelInfo] = useState(null);
  const [videoInfo, setVideoInfo] = useState(null);
  const [thumbnailInfo, setThumbnailInfo] = useState(null);
  const [viewsChartData, setViewsChartData] = useState(null);
  const [growthChartData, setGrowthChartData] = useState(null);
  const [viewsChangeChartData, setViewsChangeChartData] = useState(null);
  const [uploadCycleData, setUploadCycleData] = useState(null);
  const [activationData, setActivationData] = useState(null);


  // chatbot data
  const [popular_video_analysis, setPopularVideo] = useState(null);
  const [popular_thumbnail_analysis, setPopularThumbnail] = useState(null);
  const [freq_upload_analysis, setFreqVideo] = useState(null);
  const [activation_analysis, setActivation] = useState(null);
  const currentUser = JSON.parse(localStorage.getItem("currentUser")) || {};
  const user_email = currentUser.email;
  const name_temp = JSON.parse(localStorage.getItem(user_email)) || {};
  const channelName = name_temp.surveyResponses?.channelName;
  useEffect(() => {
    const fetchData = async () => {
      try {
        const uriChannelInfo = `http://10.28.224.177:30635/dashboard/performance/channel-banner/${channelName}`;
        const uriVideoInfo = `http://10.28.224.177:30635/dashboard/performance/channel-performance/${channelName}`;
        const uriViewCount = `http://10.28.224.177:30635/dashboard/performance/channel-viewcount/${channelName}`;
        const uriChannelGrowth = `http://10.28.224.177:30635/dashboard/performance/channel-growth/${channelName}`;
        const uriChannelFeature = `http://10.28.224.177:30635/dashboard/performance/channel-feature/${channelName}`;
        const uriChatbot_popular_video = `http://10.28.224.177:30635/chatbot/performance/popular-videos-analysis/${channelName}`;
        const uriChatbot_popular_thumbnail = `http://10.28.224.177:30635/chatbot/performance/thumbnail-analysis/${channelName}`;
        const uriChatbot_upload_frequency = `http://10.28.224.177:30635/chatbot/performance/upload-pattern-analysis/${channelName}`;
        const uriChatbot_activation = `http://10.28.224.177:30635/chatbot/performance/activity-analysis/${channelName}`;

        // 데이터 병렬 호출
        const [
          channelInfoRes,
          videoInfoRes,
          viewCountRes,
          channelGrowthRes,
          channelFeatureRes,
          chatbot_popular_video,
          chatbot_popular_thumbnail,
          chatbot_upload_video,
          chatbot_activation,
        ] = await Promise.all([
          axios.get(uriChannelInfo),
          axios.get(uriVideoInfo),
          axios.get(uriViewCount),
          axios.get(uriChannelGrowth),
          axios.get(uriChannelFeature),
          axios.get(uriChatbot_popular_video),
          axios.get(uriChatbot_popular_thumbnail),
          axios.get(uriChatbot_upload_frequency),
          axios.get(uriChatbot_activation),
        ]);

        // 채널 정보
        setChannelInfo(channelInfoRes.data[0]);

        // 비디오 정보
        if (videoInfoRes.data) {
          setVideoInfo(videoInfoRes.data["많은 사랑을 받은 영상"]);
          setThumbnailInfo(videoInfoRes.data["많은 사랑을 받은 썸네일"]);
        }

        // 조회수 및 경쟁 채널 평균 조회수
        const viewData = viewCountRes.data[0];
        setViewsChartData({
          labels: ["내 채널", "경쟁 채널"],
          datasets: [
            {
              label: "조회수",
              data: [
                viewData["내 채널 평균 조회수"],
                viewData["경쟁 채널 평균 조회수"],
              ],
              backgroundColor: ["#EDF9DE", "#FBD8A8"],
            },
          ],
        });



        // 채널 성장 추세
        const growthData = channelGrowthRes.data[0];
        setGrowthChartData({
          labels: growthData["x"], // 날짜
          datasets: [
            {
              label: "구독자 수",
              data: growthData["구독자 그래프"],
              borderColor: "#4CAF50",
              backgroundColor: "rgba(76, 175, 80, 0.2)",
              tension: 0,
              pointRadius: 0, // 데이터 포인트의 원을 제거
            },
          ],
        });

        setViewsChangeChartData({
          labels: growthData["x"], // 날짜
          datasets: [
            {
              type: "bar", // 일일 조회수는 bar 차트로 설정
              label: "일일 조회수",
              data: growthData["조회수 그래프"]["daily"],
              backgroundColor: "rgba(76, 175, 80, 0.6)", // 초록색 반투명 바
              barThickness: 2, // 바의 두께를 얇게 설정
              yAxisID: "y", // Y축 ID
            },
            {
              type: "line", // 누적 조회수는 line 차트로 설정
              label: "누적 조회수",
              data: growthData["조회수 그래프"]["total"],
              borderColor: "rgba(255, 99, 132, 1)", // 빨간색 선
              backgroundColor: "rgba(255, 99, 132, 0.2)", // 선 아래 배경색 (투명도 추가)
              fill: false, // 누적 조회수는 채우지 않음
              tension: 0, // 선의 곡률 (직선)
              pointRadius: 0, // 포인트 제거
              yAxisID: "y1", // 두 번째 Y축 사용
            },
          ],
          options: {
            responsive: true, // 반응형
            scales: {
              y: {
                type: "linear", // 첫 번째 Y축 (일일 조회수)
                position: "left",
                beginAtZero: true, // 0부터 시작
                title: {
                  display: false, // Y축 제목 숨기기
                },
              },
              y1: {
                type: "linear", // 두 번째 Y축 (누적 조회수)
                position: "right",
                beginAtZero: true, // 0부터 시작
                grid: {
                  drawOnChartArea: false, // 두 축의 격자선을 겹치지 않게 설정
                },
                title: {
                  display: false, // Y1축 제목 숨기기
                },
              },
              x: {
                title: {
                  display: false, // X축 제목 숨기기
                },
              },
            },
          },
        });



        // 업로드 주기
        const uploadData = channelFeatureRes.data[0];
        setUploadCycleData({
          labels: uploadData["x"], // 월
          datasets: [
            {
              label: "업로드 영상 수",
              data: uploadData["영상 수"],
              backgroundColor: "rgba(54, 162, 235, 0.7)",
            },
          ],
        });

        // 구독자와 비구독자 비율
        const participationPercent = parseFloat(uploadData["참여도"].replace("%", "")) / 100;

        setActivationData({
          labels: ["구독자 비율", "비구독자 비율"],
          datasets: [
            {
              label: "구독자/비구구독자 비율",
              data: [1 - participationPercent, participationPercent],
              backgroundColor: ["#A2D2FF", "#FFAFCC"],
              hoverOffset: 4,
            },
          ],
        });

        setPopularVideo(chatbot_popular_video.data)
        setPopularThumbnail(chatbot_popular_thumbnail.data)
        setFreqVideo(chatbot_upload_video.data)
        setActivation(chatbot_activation.data)


      } catch (error) {
        console.error("Error fetching data:", error);
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
    <div className="performance-container">
      {/* Toggle 버튼 영역 */}
      < div className="toggle-buttons" >
        <button className="toggle-button active" onClick={() => navigate("/main/Swot/Performance")}>채널 성과</button>
        <button className="toggle-button" onClick={() => navigate("/main/Swot/Engagement")}>시청자 참여도</button>
        <button className="toggle-button" onClick={() => navigate("/main/Swot/Revenue")}>채널 수익성</button>
      </div >

      <div className="performance-grid-container">
        {/* 채널 정보 */}
        {channelInfo && (
          <div className="profile-section">
            <img src={channelInfo["썸네일"]} alt="Channel Profile" className="profile-image" />
            <div className="profile-detail">
              <h2>{channelInfo["채널 이름"]}</h2>
              <p>구독자 {channelInfo["구독자"]}</p>
              <p>동영상 {channelInfo["동영상"]}</p>
            </div>
          </div>
        )}

        {/* 조회수 차트 */}
        <div className="graph-section">
          <h3>채널 평균 조회수 및 경쟁 채널 평균 조회수</h3>
          <div className="view_chart">
            {viewsChartData && (<Bar
              data={viewsChartData}
              options={{
                responsive: true,
                plugins: { legend: { display: false } },
                scales: {
                  x: {
                    ticks: { font: { size: 12 } }, // X축 폰트 크기
                  },
                  y: {
                    ticks: { font: { size: 12 } }, // Y축 폰트 크기
                  },
                },
              }}
              height={250} // 그래프의 고정 높이
              width={300} // 그래프의 고정 너비
            />)}
          </div>

        </div>
        {/* 많은 사랑을 받은 영상 */}
        <div className="popular-videos">
          <h3>많은 사랑을 받은 영상</h3>
          <div className="video-list">
            {videoInfo ? (
              videoInfo.map((video, index) => (
                <div className="video-card" key={index}>
                  <img
                    src={video["썸네일"]}
                    alt={video["제목"]}
                    className="thumbnail"
                  />
                  <div className="video-info">
                    <div className="video-title">
                      {video["제목"]}
                    </div>
                    <div className="video-detail">
                      <span>조회수</span>
                      <span>{video["조회수"]}</span>
                    </div>
                    <div className="video-detail">
                      <span>평균 조회율</span>
                      <span>{video["평균 조회율"]}</span>
                    </div>
                    <div className="video-detail">
                      <span>댓글 참여율</span>
                      <span>{video["댓글 참여율"]}</span>
                    </div>
                    <div className="video-detail">
                      <span>좋아요 참여율</span>
                      <span>{video["좋아요 참여율"]}</span>
                    </div>
                    <div className="video-detail">
                      <span>노출 클릭률</span>
                      <span>{video["노출 클릭률"]}</span>
                    </div>
                  </div>
                </div>
              ))
            ) : (
              <p>로딩 중...</p>
            )}
          </div>
          <div className="analysis-wrapper">
            {popular_video_analysis ? (
              <div className="analysis-box">{popular_video_analysis}</div>
            ) : (
              <p>Loading...</p>
            )}
          </div>
        </div>
        {/* 많은 사랑을 받은 썸네일 */}
        <div className="popular-thumbnails">
          <h3>많은 사랑을 받은 썸네일</h3>
          <div className="video-list">
            {thumbnailInfo ? (
              thumbnailInfo.map((thumb, index) => (
                <div className="video-card" key={index}>
                  <img
                    src={thumb["썸네일"]}
                    alt={thumb["제목"]}
                    className="thumbnail"
                  />
                  <div className="video-info">
                    <div className="video-title">
                      {thumb["제목"]}
                    </div>
                    <div className="video-detail">
                      <span>조회수</span>
                      <span>{thumb["조회수"]}</span>
                    </div>
                    <div className="video-detail">
                      <span>평균 조회율</span>
                      <span>{thumb["평균 조회율"]}</span>
                    </div>
                    <div className="video-detail">
                      <span>댓글 참여율</span>
                      <span>{thumb["댓글 참여율"]}</span>
                    </div>
                    <div className="video-detail">
                      <span>좋아요 참여율</span>
                      <span>{thumb["좋아요 참여율"]}</span>
                    </div>
                    <div className="video-detail">
                      <span>노출 클릭률</span>
                      <span>{thumb["노출 클릭률"]}</span>
                    </div>
                  </div>
                </div>
              ))
            ) : (
              <p>로딩 중...</p>
            )}
          </div>
          <div className="analysis-wrapper">
            {popular_thumbnail_analysis ? (
              <div className="analysis-box">{popular_thumbnail_analysis}</div>
            ) : (
              <p>Loading...</p>
            )}
          </div>
        </div>


        {/* 채널 성장 추세 */}
        {growthChartData && (
          <div className="graph-section">
            <h3>채널 성장 추세</h3>
            <Line
              data={growthChartData}
              options={{
                responsive: true,
                plugins: {
                  legend: { display: true, position: "top" },
                },
              }}
            />
          </div>
        )}
        {/* 조회수 변화 그래프 */}
        {viewsChangeChartData && (
          <div className="graph-section">
            <h3>조회수 변화 그래프</h3>
            <Bar
              data={viewsChangeChartData}
            />
          </div>
        )}


        {/* 영상 업로드 주기 */}
        {uploadCycleData && (
          <div className="graph-section">
            <h3>영상 업로드 주기</h3>
            <Bar
              data={uploadCycleData}
              optiosns={{
                responsive: true,
                plugins: { legend: { display: false } },
              }}
            />
            <div className="analysis-wrapper">
              {freq_upload_analysis ? (
                <div className="analysis-box">{freq_upload_analysis}</div>
              ) : (
                <p>Loading...</p>
              )}
            </div>
          </div>
        )}

        {/* 활성도 비율 */}
        {activationData && (
          <div className="graph-section">
            <h3>유사 채널 대비 활성도</h3>
            <div className="activation_graph">
              <Doughnut
                data={activationData}
                options={{
                  plugins: {
                    legend: {
                      display: false
                    },
                    tooltip: {
                      callbacks: {
                        label: function (context) {
                          const label = context.label || '';
                          const value = context.raw || 0;
                          return `${label}: ${(value * 100).toFixed(2)}%`;
                        },
                      },
                    },
                  },
                }}
                style={{ position: 'relative', height: '300px', width: '300px' }}

              />
            </div>

            <div className="analysis-wrapper">
              {activation_analysis ? (
                <div className="analysis-box">{activation_analysis}</div>
              ) : (
                <p>Loading...</p>
              )}
            </div>
          </div>
        )}


      </div>
    </div>
  );

};

export default Performance;
