import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import './Sense_List.css';

const SenseList = () => {
  const navigate = useNavigate();
  const [data, setData] = useState([]); // API 데이터 저장
  const [currentPage, setCurrentPage] = useState(1); // 현재 페이지
  const itemsPerPage = 10; // 페이지당 항목 수

  useEffect(() => {
    const fetchData = async () => {
      try {
        const currentUser = JSON.parse(localStorage.getItem("currentUser")) || {};
        const user_email = currentUser.email;
        const name_temp= JSON.parse(localStorage.getItem(user_email))||{};
        const userID=name_temp.name;
        const response = await axios.get(
          `http://10.28.224.177:30635/sensitive/result/${userID}`,
          { headers: { accept: "application/json" } }
        );

        console.log(response.data[0])

        // 데이터 변환 (임의의 검사 날짜 및 파일 형식 추가)
        const processedData = response.data.map((item, index) => ({
          id: index + 1,
          title: item.title,
          date: `2025.01.${String(24 - (index % 3)).padStart(2, "0")}`, // 가상의 날짜
          format: index % 2 === 0 ? '.mp4' : '.avi', // 가상의 파일 형식
          status:
            item.status === 0 ? '분석 중' : item.status === 1 ? '결과 보기' : '오류',
        }));

        setData(processedData);
      } catch (error) {
        console.error("❌ 데이터를 불러오는 중 오류 발생:", error);
      }
    };

    fetchData();
  }, []);

  const totalPages = Math.ceil(data.length / itemsPerPage);

  // 현재 페이지에 표시할 데이터
  const currentItems = data.slice(
    (currentPage - 1) * itemsPerPage,
    currentPage * itemsPerPage
  );

  // 페이지 변경 핸들러
  const handlePageChange = (page) => {
    setCurrentPage(page);
  };

  // "결과 보기" 클릭 시 상세 페이지 이동
  const handleViewResult = (title) => {
    navigate(`/main/sense/${encodeURIComponent(title)}`);
  };

  return (
    <div className="sense-list-container">
      <h2>민감도 검사 결과 목록</h2>

      {/* 검색 및 정렬 */}
      <div className="search-container">
        <input type="text" placeholder="Search" className="search-input" />
        <select className="sort-select">
          <option value="newest">Sort by: Newest</option>
          <option value="oldest">Sort by: Oldest</option>
        </select>
      </div>

      {/* 검사 결과 테이블 */}
      <table className="sense-list-table">
        <thead>
          <tr>
            <th>업로드된 영상 제목</th>
            <th>검사 날짜</th>
            <th>파일 형식</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {currentItems.map((item) => (
            <tr key={item.id}>
              <td>{item.title}</td>
              <td>{item.date}</td>
              <td>{item.format}</td>
              <td>
                <span
                  className={`status-label ${
                    item.status === '분석 중'
                      ? 'status-pending'
                      : item.status === '결과 보기'
                      ? 'status-completed'
                      : 'status-error'
                  }`}
                  onClick={
                    item.status === '결과 보기'
                      ? () => handleViewResult(item.title) // "결과 보기" 상태에서만 클릭 가능
                      : undefined
                  }
                  style={{
                    cursor: item.status === '결과 보기' ? 'pointer' : 'default', // "결과 보기" 상태에서만 커서 변경
                  }}
                >
                  {item.status}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {/* 페이지네이션 */}
      <div className="pagination">
        {Array.from({ length: totalPages }, (_, i) => (
          <button
            key={i + 1}
            className={`page-button ${currentPage === i + 1 ? 'active' : ''}`}
            onClick={() => handlePageChange(i + 1)}
          >
            {i + 1}
          </button>
        ))}
      </div>
    </div>
  );
};

export default SenseList;
