import React, { useState } from 'react';
import LoginPopup from './components/LoginPopup';
import './App.css';
function App() {
  const [isPopupOpen, setPopupOpen] = useState(false);

  const handleOpenPopup = () => {
    setPopupOpen(true);
  };

  const handleClosePopup = () => {
    setPopupOpen(false);
  };

  
  return (
    <div className="app-container">
      <img src="/clovista_logo.png" alt="CLOVISTA Logo" className="logo" />
      <h1>CLOVISTA</h1>
      <h3>Influencer Consultant Service with HyperCLOVA X</h3>
      <p>
        CLOVISTA는 "CLOVA"와 라틴어에서 유래된 "시야"를 뜻하는 "VISTA"의 합성어로,<br/>
        HyperCLOVA X를 통해 유튜브 채널에 대한 깊이 있는 시선을 사용자에게 제공합니다.
      </p>
      <button onClick={handleOpenPopup}>
        CLOVISTA와 대화하기
      </button>

      {isPopupOpen && <LoginPopup onClose={handleClosePopup} />}
    </div>
  );
}

export default App;
