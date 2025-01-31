import os
import pandas as pd
import numpy as np

def calculate_sentiment_ratio(directory_path, output_file_path):
    # 결과를 저장할 데이터프레임 초기화
    all_results = pd.DataFrame()
    
    # 디렉토리 내의 모든 CSV 파일을 찾기
    for filename in os.listdir(directory_path):
        if filename.endswith('.csv'):
            file_path = os.path.join(directory_path, filename)
            
            # 데이터 로드
            df = pd.read_csv(file_path)

            # 좋아요수 로그변환
            df['likeCount_log'] = np.log1p(df['likeCount'])

            # 감정 점수 매핑
            sentiment_map = {'긍정': 1, '부정': -1, '중립': 0}
            df['sentiment_score'] = df['label'].map(sentiment_map)

            # 가중 감정 점수 계산
            df['weighted_sentiment'] = df['sentiment_score'] * df['likeCount_log']

            # 감정 비율 계산
            sentiment_ratio = df.groupby('vId')['weighted_sentiment'].sum() / df.groupby('vId')['likeCount_log'].sum()
            sentiment_ratio = sentiment_ratio.reset_index()
            sentiment_ratio.columns = ['vId', 'SentimentRatio']

            all_results = pd.concat([all_results, sentiment_ratio], ignore_index=True)

        all_results.to_csv(output_file_path, index=False)

if __name__ == '__main__':
    directory_path = 'test'
    output_file_path = 'test_Pisick.csv'
    calculate_sentiment_ratio(directory_path, output_file_path)
