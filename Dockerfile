FROM python:3.12.8-slim

WORKDIR /app

# 캐시 활용: requirements.txt 파일이 변경되지 않으면 이 단계는 다시 실행되지 않습니다.
COPY requirements.txt .

RUN pip install --upgrade pip && pip install -r requirements.txt

# Hugging Face 모델 다운로드 및 복사
RUN pip install transformers
RUN python -c "from transformers import AutoModelForCausalLM; AutoModelForCausalLM.from_pretrained('Bllossom/llama-3.2-Korean-Bllossom-3B').save_pretrained('/app/models/llama-3.2-Korean-Bllossom-3B')"

COPY . .

# 포트 설정: 명확하게 포트를 명시합니다.
EXPOSE 8000

# CMD 실행: uvicorn 실행 명령어를 명확하게 작성합니다.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--ws-max-size", "52428800"]