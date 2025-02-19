import re

# 입력 파일 경로
input_file = "data/origin/stt_result_2.txt" 
output_file = "data/processed/stt_result_2_processed.txt" 

# 파일 읽기 및 처리
with open(input_file, "r", encoding="utf-8") as file:
    lines = file.readlines()

# 숫자~숫자: 형식 제거 및 줄바꿈 제거
processed_text = " ".join([re.sub(r"^\d+ ~ \d+ :", "", line).strip() for line in lines])

# 결과 저장
with open(output_file, "w", encoding="utf-8") as file:
    file.write(processed_text)

print(f"처리가 완료되었습니다. 결과는 '{output_file}'에 저장되었습니다.")
