import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import './Sense.css';

const Sense = () => {
  const [selectedCategory, setSelectedCategory] = useState('');
  const [file, setFile] = useState(null);
  const [dragging, setDragging] = useState(false);
  const [showPopup, setShowPopup] = useState(true); // popup trend
  const [isUploaded, setIsUploaded] = useState(false);

  const navigate = useNavigate();

  // localStorage에서 user 정보 가져오기
  const currentUser = JSON.parse(localStorage.getItem("currentUser")) || {};
  const user_email = currentUser.email;
  const name_temp = JSON.parse(localStorage.getItem(user_email)) || {};
  const userID = name_temp.name;

  // 파일 선택 이벤트 핸들러
  const handleFileUpload = (e) => {
    const uploadedFile = e.target.files[0];
    if (uploadedFile) {
      setFile(uploadedFile); // file 상태 업데이트
      setIsUploaded(true);
    }
  };

  useEffect(() => {
    if (file && selectedCategory) {
      handleFileUploadComplete();
    }
  }, [file, selectedCategory]); // file과 selectedCategory가 설정된 경우에만 실행


  const handleFileUploadComplete = async () => {
    if (!file) {
      console.error("🚨 파일이 없습니다.");
      return;
    }
    if (!selectedCategory) {  // 카테고리가 선택되지 않았을 경우
      console.error("🚨 카테고리를 선택해주세요.");
      alert("⚠️ 카테고리를 선택해주세요!");
      return;
    }
    const formData = new FormData();
    formData.append('user_id', userID);  // ✅ user_id를 FormData에 추가
    formData.append('category', selectedCategory);  // ✅ category 추가
    formData.append('file', file, file.name);  // ✅ file 추가
    

    //FormData 내용
    console.log("🔍 FormData 내용:");
    formData.forEach((value, key) => {
      console.log(`${key}:`, value);
    });
    
    try {
      const response = await axios.post(
        `http://10.28.224.177:30635/sensitive/analysis/`,
        formData,
        {
          headers: {
            'accept': 'application/json'
            // 'Content-Type': 'multipart/form-data'
          }
        }
      );

      console.log("✅ 업로드 성공:", response.data);
      // alert("🎉 영상 업로드 성공!");
    } catch (error) {
      console.error("❌ 업로드 실패:", error);
      // alert("⚠️ 영상 업로드 실패. 다시 시도해주세요.");
    } finally {
    }
  };

  // Drag & Drop 이벤트 핸들링
  const handleDragOver = (e) => {
    e.preventDefault();
    setDragging(true);
  };

  const handleDragLeave = () => {
    setDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragging(false);
    const uploadedFile = e.dataTransfer.files[0];
    if (uploadedFile) {
      setFile(uploadedFile);
    }
  };
  const closePopup = () => {
    setShowPopup(false);
  }
  const handleCategoryChange = (e) => {
    setSelectedCategory(e.target.value);
  };

  const handleSensitivityCheck = () => {
    navigate('/main/senselist');
  };

  return (
    <div className='sense-total-wrapper'>
      <div className="sense-container">
        <h2>영상 카테고리를 선택하고 영상을 업로드하세요!</h2>

        {/* Drag-and-Drop File Upload Section */}
        <div
          className={`file-upload-section ${dragging ? 'dragging' : ''}`}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
        >
          {isUploaded ? (
            <p className="upload-success">✅ {file.name} <br /> 업로드 완료!</p>
          ) : (
            <>
              <p>눈금 아래로 영상을 드래그 앤 드롭하거나 버튼을 클릭하세요.<br/><br/>
              ex) 탁재훈_니콜.mp4
              </p>
              <input
                type="file"
                accept="video/mp4, video/mov, video/wmv, video/avi, audio/mp3"
                onChange={handleFileUpload}
                id="file-input"
              />
              <label htmlFor="file-input" className="file-input-label">
                파일 선택
              </label>
            </>
          )}
        </div>

        {/* Dropdown for Video Category */}
        <div className="dropdown-section">
          <label htmlFor="category">영상 카테고리를 골라주세요</label>
          <select
            id="category"
            value={selectedCategory}
            onChange={handleCategoryChange}
            className="dropdown"
          >
            <option value="">카테고리를 선택해주세요</option>
            <option value="entertainment">엔터테인먼트</option>
            <option value="education">교육</option>
            <option value="cooking">요리</option>
            <option value="sports">스포츠, 게임</option>
            <option value="music">음악</option>
          </select>
          {selectedCategory && <p className="category-selected">선택된 카테고리: {selectedCategory}</p>}
        </div>

        {/* 민감도 검사 버튼 */}
        <button className="sensitivity-check-button" onClick={handleSensitivityCheck}>
          민감도 검사 결과보기
        </button>
      </div>
      <div className='scroll-image'>
        <img src='/arrow.gif' />
        <p>최근 논란 트렌드와 반복되는 케이스를 확인해보세요!</p>
      </div>
      <div className='recent-trend-explain'>
        <h1>연도별 논란 키워드</h1>
        유튜브 콘텐츠의 논란 키워드는 시대별로 변화를 보여왔습니다. 과거에는 방송 중 욕설 사용이 논란의 소재가 되기도 하였으나, 현재는 오히려 유머의 요소로 욕설이 자주 사용되며 이에 대한 대중의 민감도도 상당히 낮아진 것을 확인할 수 있습니다.<br /> <br />
        2020년에는 '몰카'와 '주작' 콘텐츠가 트렌드로 자리 잡으며 새로운 형태의 문제들이 발생했습니다. 허위정보로 인한 사회적 혼란을 야기하거나, 특정 업체 및 배달원의 명예를 훼손하는 사례가 발생하고, 심지어 장애인을 가장한 주작 콘텐츠까지 제작되는 등 윤리적 경계를 넘어서는 일들이 빈번했습니다. 이는 콘텐츠의 과도기적 현상으로 볼 수 있으며, 그 심각성으로 인해 많은 사례가 기사화되고 법적 처벌로 이어지기도 했습니다.<br /> <br />
        2023년부터 최근까지는 특정 대상을 '비하'하는 콘텐츠로 인한 논란이 주를 이루고 있습니다. 이는 콘텐츠 제작자들이 자신의 콘텐츠가 특정 개인이나 집단에게 상처가 될 수 있다는 점을 더욱 신중하게 고려해야 할 필요성을 시사합니다.
      </div>

      <div className='sense-recent-trend-grid'>
        <div className='recent-trend-left'>
          <div className='sense-trend-year-keyword-first'>
            <span>2024년</span>
            <span>#비하 #조롱</span>
          </div>
        </div>
        <div className='recent-trend-right'>
          <h2>피식대학 영양군 지역비하 논란</h2>
          <div className='recent-trend-right-detail'>
            <img src='/sense-trend-pic/2024_psick_thumbnail.jpg'></img>
            <p>피식대학의 '메이드 인 경상도' 시리즈 중, 경북 영양편에서는 출연진이 현지 음식을 "할머니 맛", "할머니 살을 뜯는 것 같다"와 같이 부적절하게 비유했으며, 사장이 있는 식당 내에서 음식을 혹평하고 상표를 노출하는 등의 문제적 행동을 보였습니다. 또한 지역 인구와 환경에 대한 부정적인 발언으로 인해 지역 비하, 노인 비하, 기본적 예의 부족 등의 비판을 받았습니다.</p>
          </div>
        </div>
        <div className='recent-trend-left-l'>
        </div>
        <div className='recent-trend-right-l'>
          <h2>싱글벙글 군인 비하 영상 논란</h2>
          <div className='recent-trend-right-detail'>
            <img src='/sense-trend-pic/2024_sgbg.jpg'></img>
            <p>싱글벙글의 "나 오늘 전역했다니까!!!" 편에서는 최근 군 관련 비극적 사건이 발생한 상황에서, 징병과 군 생활의 불편함을 희화화하였습니다. 이러한 내용이 군인들의 희생을 가볍게 다루는 것으로 비칠 수 있어 시청자들의 반발을 샀습니다.</p>
          </div>
        </div>
        <div className='recent-trend-left'>
          <div className='sense-trend-year-keyword'>
            <span>2023년</span>
            <span>#비하 #조롱 #일반화</span>
          </div>
        </div>
        <div className='recent-trend-right'>
          <h2>가요이 키우기 후쿠시마 물 맛 논란</h2>
          <div className='recent-trend-right-detail'>
            <img src='/sense-trend-pic/2023_gayoi.jpg'></img>
            <p>가요이 키우기의 기타큐슈 여행 브이로그에서, 출연자가 기타큐슈 공항 근처에서 구매한 생수를 마시며 "후쿠시마 맛"이라고 발언하였습니다. 이 발언이 후쿠시마의 역사적 사건을 경시하는 것으로 받아들여져 일본 및 한국 네티즌들의 항의가 이어졌습니다.</p>
          </div>
        </div>
        <div className='recent-trend-left'></div>
        <div className='recent-trend-right'>
          <h2>고누리 던전앤파이터 유저 비하 논란</h2>
          <div className='recent-trend-right-detail'>
            <img src='/sense-trend-pic/gonoori.webp'></img>
            <p>고누리의 '던파하는 선임' 영상에서는 던전앤파이터 유저들을 일반화하여 비하하는 내용이 포함되어 있었습니다. 영상은 특정 선임의 행동을 모든 유저에게 적용하여 “-던-은 과학이다.”라며 차별적 표현을 사용하여 던전앤파이터 유저를 일반화하여 비하했습니다.</p>
          </div>
        </div>
        <div className='recent-trend-left-l'></div>
        <div className='recent-trend-right-l'>
          <h2>승우아빠 당근마켓 비하 논란</h2>
          <div className='recent-trend-right-detail'>
            <img src='/sense-trend-pic/2023_dangn_news.jpg'></img>
            <p>승우아빠는 식당 창업에 관한 조언을 제공하는 영상에서 "당근에서 구인하면 중고들만 들어온다", "사람도 중고 같다"는 발언을 하였습니다. 이는 막연한 고정관념을 가지고 당근마켓 플랫폼뿐만 아니라, 구인 구직자 전반을 비하한 것으로 대중의 반감을 불러일으켰습니다.</p>
          </div>
        </div>
        <div className='recent-trend-left'>
          <div className='sense-trend-year-keyword'>
            <span>2020년</span>
            <span>#몰카 #주작 #허위정보</span>
          </div>
        </div>
        <div className='recent-trend-right'>
          <h2>비슷해보이즈 코로나바이러스감염증-19 유튜브 몰카 사건</h2>
          <div className='recent-trend-right-detail'>
            <img src='/sense-trend-pic/2020_covid.jpg'></img>
            <p>비슷해보이즈는 동대구역에서 코로나바이러스감염증-19 환자를 연기하여 확진자가 도주한 것처럼 연출한 몰래카메라 영상을 촬영하고 업로드했습니다. 이 행위로 시민들 사이에 공포와 오해를 일으켜, 사회적으로 민감한 시기에 공중의 안전과 질서를 심각하게 해친 것으로 평가받았습니다.</p>
          </div>
        </div>
        <div className='recent-trend-left'></div>
        <div className='recent-trend-right'>
          <h2>송대익 피자나라 치킨공주 조작 사건</h2>
          <div className='recent-trend-right-detail'>
            <img src='/sense-trend-pic/2020_song.jpg'></img>
            <p>송대익은 피자나라 치킨공주에서 주문한 음식이 배달 과정에서 일부 먹혀져 왔다고 주장하며 이를 문제 삼아 매장에 항의하는 내용의 조작된 영상을 업로드했습니다. 이는 해당 업체의 명예를 훼손하고 배달 업계 종사자들을 비하하는 내용으로 사회적 비난을 유발하였습니다.</p>
          </div>
        </div>
        <div className='recent-trend-left-l'></div>
        <div className='recent-trend-right-l'>
          <h2>하말넘많 스마트폰 크기 논란</h2>
          <div className='recent-trend-right-detail'>
            <img src='/sense-trend-pic/2020_smartphone.jpg'></img>
            <p>하말넘많은 페미니즘 관련 도서를 바탕으로 제작한 영상에서, 기술과 제품 디자인이 남성 중심으로 이루어져 여성에게 불편을 초래한다고 주장했습니다. 이 영상은 관련 기술 및 제품의 개발 의도를 남녀 차별 문제로 확대해석하고, 검증되지 않은 정보를 바탕으로 한 주장으로 논란을 일으켰습니다.</p>
          </div>
        </div>
        <div className='recent-trend-left'>
          <div className='sense-trend-year-keyword'>
            <span>2017년</span>
            <span>#욕설</span>
          </div>
        </div>
        <div className='recent-trend-right'>
          <h2>침착맨 거준깝 사건</h2>
          <div className='recent-trend-right-detail'>
            <img src='/sense-trend-pic/2017_chim.jpg'></img>
            <p>유튜브 방송 중 침착맨은 한 어그로 시청자의 도발적 댓글에"거참 준내게 깐족대네 시벌새끼가"라며 강한 어조의 욕설을 사용하였습니다. 이 사건은 지식인 상담 변호사가 모욕죄 가능성에 대해 원론적인 답변을 제시하면서 논란이 되었으나, 이후 해당 발언은 밈이 되어 널리 사용되고 있습니다.</p>
          </div>
        </div>
      </div>
      <div className='repeated-trend-explain'>
        <h1>반복되는 논란 키워드</h1>
        연도별 논란 추세 외에도 유튜브 플랫폼에서는 지속적으로 문제가 제기되는 민감한 주제들이 존재합니다.
      </div>

      <div className='repeated-trend-container'>
        <h1># 장애인 연기</h1>
        <div className='reapeted_pictures-grid'>
          <h1># 2020년  # 홍정오 아임뚜렛 사건</h1>
          <h1># 2022년  # 우와소 자폐인 희화화 논란</h1>
          <img src='/new_pic/아임뚜렛1.jpg'></img>
          <img src='/new_pic/우와소1.jpg'></img>
          <img src='/new_pic/아임뚜렛3.jpg'></img>
          <img src='/new_pic/우와소3.jpg'></img>
        </div>
        <p>장애인 관련 논란은 콘텐츠 제작자들이 장애를 희화화하거나 부적절하게 재현하는 과정에서 발생했습니다. 2020년 홍정오의 '아임뚜렛' 사건에서는 투렛 증후군이 없는 제작자가 장애를 연기하며 실제 환자들의 고통을 오락거리로 만들었다는 비판을 받았습니다. 2022년에는 유튜버 우와소가 자폐 스펙트럼 장애를 가진 드라마 캐릭터의 특징적인 말투와 행동을 모방하며 자폐인을 희화화했다는 논란이 일었습니다. 이러한 사례들은 우리 사회가 사회적 약자나 소수자를 다룰 때 특히 높은 수준의 윤리의식을 요구한다는 점을 보여줍니다.</p>
        <h1># 군 복무/군인</h1>
        <div className='reapeted_pictures-grid'>
          <h1># 2022년  # 주르르 군인 비하 논란</h1>
          <h1># 2024년  # 싱글벙글 군인 비하 논란</h1>
          <img src></img>
          <img src='/new_pic/싱글벙글1.jpg'></img>
          <img src='/new_pic/주르르.jpg'></img>
          <img src='/new_pic/싱글벙글2.jpg'></img>
        </div>
        <p>군 복무 관련 콘텐츠 역시 지속적인 논란의 대상이 되어왔습니다. 2022년 주르르는 국방의 의무를 "국방부 퀘스트"로, 군복을 "레어 의상 득템"으로 표현하며 군인들의 희생과 노력을 경시했다는 비판을 받았습니다. 최근 2024년에는 싱글벙글이 군 관련 사고들을 고려하지 않은 채 군인들의 고통과 불편함을 가볍게 다루는 콘텐츠를 제작해 논란이 되었습니다. 이러한 사례들은 군인들의 노고를 당연하게 여기거나 그들의 수고로움을 충분히 고려하지 못한 발언들이 종종 등장하면서 문제가 되고 있어, 관련 콘텐츠 제작 시 각별한 주의가 필요함을 시사합니다.</p>
      </div>
    </div>

  );
};

export default Sense;
