FROM ubuntu:24.04

WORKDIR /app

# Install libreoffice and libreoffice-h2orestart
RUN apt-get update

RUN apt-get install -y language-pack-ko && locale-gen ko_KR.UTF-8 ko_KR.EUC-KR && update-locale LANG=ko_KR.UTF-8

RUN apt-get install -y libreoffice libreoffice-h2orestart

RUN apt-get clean

# Install Python 3 and pip
RUN apt-get update && apt-get install -y python3 python3-pip python3-venv

# Upgrade pip
# RUN python3 -m pip install --upgrade pip --break-system-packages

# 3. requirements.txt 파일 복사
COPY requirements.txt .

# 4. requirements.txt에 있는 패키지 설치 (python3 -m pip을 사용하여 pip 명령어 호출)
RUN python3 -m pip install -r requirements.txt --break-system-packages

COPY . .

# 포트 설정: 명확하게 포트를 명시합니다.
EXPOSE 8000

# CMD 실행: uvicorn 실행 명령어를 명확하게 작성합니다.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--ws-max-size", "52428800"]
