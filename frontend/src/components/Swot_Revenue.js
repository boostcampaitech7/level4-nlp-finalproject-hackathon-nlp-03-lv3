import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Bar } from "react-chartjs-2"; // React Chart의 Bar 컴포넌트
import axios from "axios";
import Loader from "./Loader";
import "./Swot_Revenue.css";
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

const SwotRevenue = () => {
  const navigate = useNavigate();

  const currentUser = JSON.parse(localStorage.getItem("currentUser")) || {};
  const user_email = currentUser.email;
  const name_temp = JSON.parse(localStorage.getItem(user_email)) || {};
  const channelName = name_temp.surveyResponses?.channelName;


  const [bestAd, setBestAd] = useState(null); // 가장 성적이 좋은 광고 영상 데이터 상태
  const [worstAd, setWorstAd] = useState(null); // 가장 성적이 안 좋은 광고 영상 데이터 상태
  const [comparisonData, setComparisonData] = useState(null); // 광고 영상 vs 일반 영상 성과 비교 데이터 상태
  const [analysisResult, setAnalysisResult] = useState(""); // 수익성 분석 결과
  const [loading, setLoading] = useState(true); // 로딩 상태 추가
  const [viewsData, setViewsData] = useState(null); // 조회수 차트 데이터
  const [donationsData, setDonationsData] = useState(null); // 후원 수입 차트 데이터


  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);

        console.log(channelName)
        const uriViewsDonations = `http://10.28.224.177:30635/dashboard/profitability/views-and-donations/${channelName}`;
        const uriAdPerformance = `http://10.28.224.177:30635/dashboard/profitability/ad-performance/${channelName}`;
        const uriAdVsNormal = `http://10.28.224.177:30635/dashboard/profitability/ad-vs-normal/${channelName}`;
        const uriProfitabilityAnalysis = `http://10.28.224.177:30635/chatbot/profitability/revenue-analysis/${channelName}`;

        const [
          responseViewsDonations,
          responseAdPerformance,
          responseAdVsNormal,
          responseProfitabilityAnalysis,
        ] = await Promise.all([
          axios.get(uriViewsDonations),
          axios.get(uriAdPerformance),
          axios.get(uriAdVsNormal),
          axios.get(uriProfitabilityAnalysis),
        ]);

        const apiData = responseViewsDonations.data[0];
        setViewsData({
          labels: ["내 계정", "평균값"],
          datasets: [
            {
              label: "조회수 수입",
              data: [apiData.조회수_유저, apiData.조회수_평균],
              backgroundColor: ["#EDF9DE", "#FBD8A8"],
            },
          ],
        });

        setDonationsData({
          labels: ["내 계정", "평균값"],
          datasets: [
            {
              label: "후원 수입",
              data: [apiData.후원_유저, apiData.후원_평균],
              backgroundColor: ["#EDF9DE", "#FBD8A8"],
            },
          ],
        });

        setBestAd(responseAdPerformance.data["가장 성적이 좋은 광고 영상"]);
        setWorstAd(responseAdPerformance.data["가장 성적이 안좋은 광고 영상"]);
        setComparisonData(responseAdVsNormal.data[0]);
        setAnalysisResult(responseProfitabilityAnalysis.data);
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
    <div className="revenue-container">

      {/* Toggle 버튼 영역 */}
      < div className="toggle-buttons" >
        <button className="toggle-button" onClick={() => navigate("/main/Swot/Performance")}>채널 성과</button>
        <button className="toggle-button" onClick={() => navigate("/main/Swot/Engagement")}>시청자 참여도</button>
        <button className="toggle-button active" onClick={() => navigate("/main/Swot/Revenue")}>채널 수익성</button>
      </div >

      <div className="revenue-grid-container">

        {/* 조회수 및 후원 수입 섹션 */}
        <div className="revenue_charts-wrapper">
          <h3>조회수 수입 및 후원 수입</h3>
          {/* 조회수 차트 */}
          <div className="revenue_charts">
            <div className="revenue_chart">
              <div>조회수</div>
              {viewsData && (
                <Bar
                  data={viewsData}
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
                />
              )}
            </div>
            {/* 후원 수입 차트 */}
            <div className="revenue_chart">
              <div>후원</div>
              {donationsData && (
                <Bar
                  data={donationsData}
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
                />
              )}
            </div>
          </div>

        </div>

        <div className="ads-wrapper">
          {/* 가장 성적이 좋은 광고영상 */}
          <div className="ad-section">
            <h4>가장 성적이 좋은 광고영상</h4>
            {bestAd ? (
              <>
                <div className="ad-thumbnail-wrapper">
                  <img src={bestAd.썸네일} alt="Best Ad" className="ad-thumbnail" />
                </div>
                <div className="ad-content">
                  <div className="ad-info">
                    <p className="ad-title">{bestAd.제목}</p>
                    <div className="ad-detail">
                      <span>업로드 날짜</span>
                      <span>{bestAd["업로드 날짜"]}</span>
                    </div>
                    <div className="ad-detail">
                      <span>조회수</span>
                      <span>{bestAd.조회수}</span>
                    </div>
                    <div className="ad-detail">
                      <span>평균 조회율</span>
                      <span>{bestAd["평균 조회율"]}</span>
                    </div>
                    <div className="ad-detail">
                      <span>댓글 참여율</span>
                      <span>{bestAd["댓글 참여율"]}</span>
                    </div>
                    <div className="ad-detail">
                      <span>좋아요 참여율</span>
                      <span>{bestAd["좋아요 참여율"]}</span>
                    </div>
                    <div className="ad-detail">
                      <span>노출 클릭률</span>
                      <span>{bestAd["노출 클릭률"]}</span>
                    </div>
                  </div>
                </div>
              </>
            ) : (
              <p>Loading...</p>
            )}
          </div>

          {/* 가장 성적이 안 좋은 광고영상 */}
          <div className="ad-section">
            <h4>가장 성적이 안 좋은 광고영상</h4>
            {worstAd ? (
              <>
                <div className="ad-thumbnail-wrapper">
                  <img src={worstAd.썸네일} alt="Worst Ad" className="ad-thumbnail" />
                </div>
                <div className="ad-content">
                  <div className="ad-info">
                    <p className="ad-title">{worstAd.제목}</p>
                    <div className="ad-detail">
                      <span>업로드 날짜</span>
                      <span>{worstAd["업로드 날짜"]}</span>
                    </div>
                    <div className="ad-detail">
                      <span>조회수</span>
                      <span>{worstAd.조회수}</span>
                    </div>
                    <div className="ad-detail">
                      <span>평균 조회율</span>
                      <span>{worstAd["평균 조회율"]}</span>
                    </div>
                    <div className="ad-detail">
                      <span>댓글 참여율</span>
                      <span>{worstAd["댓글 참여율"]}</span>
                    </div>
                    <div className="ad-detail">
                      <span>좋아요 참여율</span>
                      <span>{worstAd["좋아요 참여율"]}</span>
                    </div>
                    <div className="ad-detail">
                      <span>노출 클릭률</span>
                      <span>{worstAd["노출 클릭률"]}</span>
                    </div>
                  </div>
                </div>
              </>
            ) : (
              <p>Loading...</p>
            )}
          </div>
        </div>


        {/* 광고영상과 일반영상의 성과 비교 */}
        <div className="table-wrapper">
          <h3>광고영상과 일반영상의 성과 비교</h3>
          {comparisonData ? (
            <table className="comparison-table">
              <thead>
                <tr>
                  <th>항목</th>
                  <th>일반영상</th>
                  <th>광고영상</th>
                  <th>비교</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(comparisonData).map(([key, value]) => (
                  <tr key={key}>
                    <td>{key}</td>
                    <td>{value["일반 영상"]}</td>
                    <td>{value["광고 영상"]}</td>
                    <td>{value["비교"]}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <p>Loading...</p>
          )}
        </div>

        {/* 채널의 수익성 분석 결과 */}
        <div className="analysis-wrapper">
          <h3>채널의 수익성에 대한 분석결과</h3>
          {analysisResult ? (
            <div className="analysis-box">{analysisResult}</div>
          ) : (
            <p>Loading...</p>
          )}
        </div>
      </div>
    </div>

  );
};

export default SwotRevenue;
