from io import BytesIO
import os
import shutil
import subprocess
import asyncio

from fastapi import UploadFile
from pdfminer.high_level import extract_text
from pathlib import Path
async def file2text(file: UploadFile):

    # print(file.content_type)

    # pdf인 경우
    if file.content_type == "application/pdf":

        # file 읽기
        content = await file.read()

        # pdf -> 문자열 추출
        result = extract_text(BytesIO(content))

        return result    
    
    # pdf가 아닌 경우 ( hwp, hwpx 예상 )
    else:
        try:

            # 경로 설정
            dir = "./temp/"
            path = Path(f"{dir}{file.filename}")

            # 디렉터리가 없으면 생성
            path.parent.mkdir(parents=True, exist_ok=True)

            # .hwp 파일 쓰기
            with path.open("wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            # hwp -> pdf 변환, 저장
            convert_to_pdf(dir,file.filename)
        
            # pdf -> 문자열 추출
            result = extract_text(path.with_suffix(".pdf"))

            # temp hwp, pdf 보안삭제
            secure_delete(path)
            secure_delete(path.with_suffix(".pdf"))

            # temp hwp, pdf 비동기 보안삭제
            # asyncio.create_task(secure_delete(path))
            # asyncio.create_task(secure_delete(path.with_suffix(".pdf")))

            return result
        
        except: # PDF외 파일 처리중 에러 발생시
            raise TypeError('PDF,HWP파일인지 확인해주세요.')
    
# hwp, hwpx -> pdf (LibreOffice, H2O restart 확장 필요)
def convert_to_pdf(dir,file):
    """
    LibreOffice로 파일을 PDF로 변환
    H2O restart 확장 : https://github.com/ebandal/H2Orestart
    """
    try:
        subprocess.run([
            "libreoffice",
            "--headless",
            "--convert-to", "pdf:writer_pdf_Export",
            "--outdir", dir,
            dir+file
        ], check=True)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"LibreOffice 변환 오류: {e}")
    

# 특정 파일 보안삭제하는 메서드
def secure_delete(file_path, passes=3):
    
    # 파일이 존재하는지 확인
    if not os.path.isfile(file_path):
        raise ValueError(f"{file_path}는 존재하지 않는 파일입니다.")

    # 파일 크기 얻기
    file_size = os.path.getsize(file_path)

    # 파일을 여러 번 덮어쓰며 삭제
    with open(file_path, "r+b") as f:
        for _ in range(passes):
            # 랜덤한 데이터를 덮어쓰기
            f.seek(0)  # 파일의 처음으로 이동
            f.write(os.urandom(file_size))  # 랜덤 데이터로 덮어쓰기
            f.flush()

    # 파일 삭제
    os.remove(file_path)
    print(f"{file_path}가 보안 삭제되었습니다.")