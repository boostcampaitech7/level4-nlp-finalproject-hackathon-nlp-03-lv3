import os
import pandas as pd
import http.client
import json
import time
from tqdm import tqdm


class CompletionExecutor:
    def __init__(self, host, api_key, request_id):
        self._host = host
        self._api_key = api_key
        self._request_id = request_id

    def _send_request(self, completion_request):
        headers = {
            'Content-Type': 'application/json; charset=utf-8',
            'Authorization': self._api_key,
            'X-NCP-CLOVASTUDIO-REQUEST-ID': self._request_id
        }

        conn = http.client.HTTPSConnection(self._host)
        retries = 0
        while retries < 3:  # 최대 3번 재시도
            conn.request('POST', '/testapp/v1/tasks/yl1do68p/search', json.dumps(completion_request), headers)
            response = conn.getresponse()
            if response.status == 429:  # Too Many Requests
                time.sleep(60)  # 60초 대기
                retries += 1
            else:
                break
        if response.status != 200:
            return {'status': {'code': str(response.status), 'message': 'HTTP error'}}
        result = json.loads(response.read().decode(encoding='utf-8'))
        conn.close()
        return result

    def execute(self, completion_request):
        res = self._send_request(completion_request)
        if res['status']['code'] == '20000':
            return res['result']['outputText']
        else:
            return f"Error: {res['status']['message']}"

def analyze_comments(input_file_path, output_file_path):
    df = pd.read_csv(input_file_path)
    completion_executor = CompletionExecutor(
        host='clovastudio.stream.ntruss.com',
        api_key='Bearer nv-f5786fde571f424786ed0823986ca992h3P1',
        request_id='7f97fccdf117491c8f159c33c3cb9fa8'
    )
    
    def process_row(row):
        try:
            time.sleep(1)  # API 호출 사이 1초 대기
            return completion_executor.execute({'text': row['textDisplay'], 'includeAiFilters': True})
        except Exception as e:
            print(f"Error processing row: {row['textDisplay']} -> {str(e)}")
            return "Error"

    df['label'] = df.apply(process_row, axis=1)
    df.to_csv(output_file_path, index=False)

def process_all_files(directory):
    files = [f for f in os.listdir(directory) if f.endswith('.csv')]
    for filename in tqdm(files, desc="Processing files"):
        if filename.endswith('.csv'):
            input_file_path = os.path.join(directory, filename)
            output_file_path = os.path.join(directory, filename)  # 같은 파일명으로 저장
            analyze_comments(input_file_path, output_file_path)
            print(f'Processed {filename}')

if __name__ == '__main__':
    directory = 'Psick_comments'  # Psick_comments, SGBG_comments
    process_all_files(directory)
