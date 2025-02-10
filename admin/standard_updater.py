from io import BytesIO
import os
import re
from fastapi import UploadFile
import pandas as pd
from sqlalchemy import create_engine, types
from module.file2text import file2text
from module.text2formatted import process_and_refine_text
from fastapi.datastructures import UploadFile
from starlette.datastructures import Headers as Headers  # noqa: F401

MYSQL_USERNAME = os.environ.get('MYSQL_USERNAME')
MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD')
conn = create_engine(f'mysql+mysqlconnector://{MYSQL_USERNAME}:{MYSQL_PASSWORD}@localhost:3306/TermCompass')

async def extract_and_process_pdfs(folder_path: str):
    """
    특정 폴더의 모든 PDF 파일에서 텍스트를 추출하고 정제한 결과를 데이터프레임으로 반환합니다.

    Args:
        folder_path (str): PDF 파일이 포함된 폴더 경로
    """
    pdf_files = [file for file in os.listdir(folder_path) if file.lower().endswith('.pdf')]

    for pdf_file in pdf_files:
        print("처리중 : ", pdf_file)

        # 텍스트 파일 경로 설정
        txt_file_path = os.path.join(folder_path, f"{pdf_file.rsplit('.pdf', 1)[0]}.txt")

        # 이미 처리된 파일은 건너뛰기
        if os.path.exists(txt_file_path):
            print(f"{pdf_file}는 이미 처리되었습니다. 건너뜁니다.")
            continue

        # 파일 읽기
        pdf_path = os.path.join(folder_path, pdf_file)
        file_bytes = open(pdf_path, "rb").read()

        # UploadFile객체 생성
        file = UploadFile(filename=pdf_file, file=BytesIO(file_bytes))

        # 텍스트 추출
        try:
            raw_text = await file2text(file, "application/pdf")
            refined_text = process_and_refine_text(raw_text)

            # 문자 마무리 처리
            refined_text = refined_text.replace("\n", "")  # 모든 줄바꿈 문자 \n 삭제
            refined_text = re.sub(r'<h([1-6])>', '<h4>', refined_text)  # 시작 태그 <h1>~<h6> -> <h4>
            refined_text = re.sub(r'</h([1-6])>', '</h4>', refined_text)  # 종료 태그 </h1>~</h6> -> </h4>
            refined_text = re.sub(r'<h4>', '<h1>', refined_text, count=1)# 첫 번째 <h4>를 <h1>로 교체
            refined_text = re.sub(r'</h4>', '</h1>', refined_text, count=1)# 첫 번째 </h4>를 </h1>로 교체

            data = {"filename": pdf_file.rsplit('.pdf', 1)[0], "refined_text": refined_text}

            # 데이터프레임 생성
            df = pd.DataFrame([data])

            # SQL에 저장
            # df.to_sql("standard", conn, if_exists="append", index=False, dtype={'refined_text': types.TEXT()})
            df.to_sql("standard", conn, if_exists="append", index=False, dtype={'refined_text': types.TEXT()})

            # 텍스트 파일로 저장
            with open(txt_file_path, "w", encoding="utf-8") as txt_file:
                txt_file.write(refined_text)
            
        except Exception as e:
            print(f"Error processing file {pdf_file}: {e}")
            continue