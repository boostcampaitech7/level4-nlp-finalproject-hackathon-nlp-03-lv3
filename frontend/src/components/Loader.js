import React from "react";
import "./Loader.css"; // 스타일을 추가할 경우
import loadingGif from "./spinner.gif"; // GIF 파일 경로를 지정

const Loader = ({ message }) => {
  return (
    <div className="loader-container">
      <div className="loader-content">
        <h2>{message}</h2>
        <img src={loadingGif} alt="Loading..." className="loader-gif" />
      </div>
    </div>
  );
};

export default Loader;
