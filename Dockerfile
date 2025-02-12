FROM ubuntu:24.04

WORKDIR /app

# 1. locales와 한글 언어팩 설치
RUN apt-get update && apt-get install -y locales language-pack-ko

# 한글 폰트 설치 (예: Nanum, Noto CJK)
RUN apt-get install -y fonts-nanum fonts-noto-cjk

# 2. /etc/locale.gen 파일에서 원하는 로케일 언코멘트 및 생성
RUN sed -i 's/^# *\(ko_KR.UTF-8\)/\1/' /etc/locale.gen && \
    sed -i 's/^# *\(ko_KR.EUC-KR\)/\1/' /etc/locale.gen && \
    locale-gen && \
    update-locale LANG=ko_KR.UTF-8

# 3. 환경 변수 설정 (이렇게 하면 런타임에도 적용됨)
ENV LANG ko_KR.UTF-8
ENV LC_ALL ko_KR.UTF-8

# 4. libreoffice 및 libreoffice-h2orestart 설치
RUN apt-get install -y libreoffice libreoffice-h2orestart && \
    apt-get clean

# 5. Python3, pip, venv 설치
RUN apt-get update && apt-get install -y python3 python3-pip python3-venv

# 6. requirements.txt 복사 및 pip 패키지 설치
COPY requirements.txt .
RUN python3 -m pip install -r requirements.txt --break-system-packages

COPY . .

EXPOSE 8000

# 7. uvicorn으로 앱 실행
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--ws-max-size", "52428800"]
