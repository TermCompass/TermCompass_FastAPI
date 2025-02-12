FROM python:3.12.8-slim

# 작업 디렉토리 설정
WORKDIR /app

# 캐시 디렉토리 설정 (모델이 저장될 위치)
ENV TRANSFORMERS_CACHE=/app/models_cache

# requirements.txt 복사 후 의존성 설치
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# 모델 다운로드: 이미지를 빌드할 때 모델을 다운로드
RUN python -c "from transformers import LlamaForCausalLM, PreTrainedTokenizerFast; \
                model_name = 'Bllossom/llama-3.2-Korean-Bllossom-3B'; \
                LlamaForCausalLM.from_pretrained(model_name, torch_dtype='torch.float16', device_map='auto'); \
                PreTrainedTokenizerFast.from_pretrained(model_name)"

# 프로젝트 파일 복사
COPY . .

# 포트 노출
EXPOSE 8000

# FastAPI 애플리케이션 실행
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--ws-max-size", "52428800"]
