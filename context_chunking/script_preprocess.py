import re

def clean_script(file_path):
    # 파일을 읽기 모드로 열기
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()

    # 유튜브 링크와 "Transcript:" 문자열과 그 이전의 모든 내용을 제거
    content = re.sub(r'^.*?Transcript:', '', content, flags=re.DOTALL)

    # 시간 스탬프 제거
    cleaned_content = re.sub(r'\(\d{2}:\d{2}\)\s*', '', content)

    # 결과 반환
    return cleaned_content.strip()  # 양쪽 공백 제거

def save_to_txt(cleaned_content, output_file):
    # TXT 파일로 저장
    with open(output_file, 'w', encoding='utf-8') as file:
        file.write(cleaned_content)

# 사용 예시
file_path = 'data/lie.txt'
output_file = 'data/lie_clean.txt'
cleaned_text = clean_script(file_path)
save_to_txt(cleaned_text, output_file)
