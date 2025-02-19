// PopupGuide.js
import React from "react";
import "./PopupGuide.css"; // 스타일 추가

const PopupGuide = ({ onClose }) => {
  return (
    <div className="popup-guide-container">
      <div className="popup-guide-content">
        <button className="close-button" onClick={onClose}>
          <img src={'/close.png'} alt="Close" />
        </button>
        <h2>연도별 논란 키워드랑 반복되는 논란되는 키워드 들어가는 팝업 내용 될 부분 블라블라</h2>
      </div>
    </div>
  );
};

export default PopupGuide;
