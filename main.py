import base64
from pprint import pprint
from fastapi import FastAPI
from pydantic import BaseModel
import torch
from transformers import LlamaForCausalLM , PreTrainedTokenizerFast

app = FastAPI()

# 0-1. 모델 로드 ------------------------------------------------------------------------------------
from module.global_var import model, tokenizer

# 모델과 토크나이저 로드
# model_name = "beomi/Llama-3-Open-Ko-8B"
model_name = "Bllossom/llama-3.2-Korean-Bllossom-3B"
model = LlamaForCausalLM.from_pretrained(model_name, torch_dtype=torch.float16, device_map="auto")
tokenizer = PreTrainedTokenizerFast.from_pretrained(model_name)

# 패딩 토큰 설정
tokenizer.pad_token = tokenizer.eos_token
model.config.pad_token_id = tokenizer.pad_token_id

print("모델 객체 타입 " + str(type(model)))
print("토크나이저 객체 타입 " + str(type(tokenizer)))

# 로드 후 전역 변수 업데이트
import module.global_var as global_var
global_var.model = model
global_var.tokenizer = tokenizer

# 0-2. 모듈 로드 ------------------------------------------------------------------------------------
# 모델, 토크나이저 초기화 후에 모듈을 로드해야 전역으로 선언된 모델, 토크나이저를 사용할 수 있음
from module.file2text import file2text
from module.task_planner import tasker
from task.review import review
from task.generate import generate
from task.modify import modify
from task.chat import chat



# 1. 검토 (텍스트 or 파일 -> 검토 결과 List) ------------------------------------------------------
class review_form(BaseModel):
    # task: str = "review"
    content: str


# 1-1. 검토 (텍스트)
@app.post("/review_text")
def review_text(data: review_form):
    pprint(data)
    review_result = review(data.content)
    return {"result": "검토 결과 List"}


# 1-2. 검토 (파일)
@app.post("/review_file")
def review_text(data: review_form):  # content: Base64로 인코딩된 파일 문자열
    # Base64.getUrlEncoder().encodeToString(fileBytes); -> base64.urlsafe_b64decode() 특수문자 문제시 인코딩 변경 고려 ???
    file = base64.b64decode(data.content)
    try:
        text = file2text(file)
        pprint(text)
        review_result = review(text)
        return {"result": "[검토 결과 List]"}
    except:
        return {"result": "파일을 읽을 수 없습니다."}


# 2. 생성요청 ------------------------------------------------------------------------------------
class generate_form(BaseModel):
    # task: str = "generate"
    content: str


class modify_form(BaseModel):
    # task: str = "modify"
    request: str  # 사용자 요청사항
    current: str  # 현재 약관
    context: str  # 현재 컨텍스트


# 2-1. 생성요청 (텍스트 -> 표준문서 ID)
@app.post("/generate")
def generate_term(data: generate_form):
    pprint(data)
    generate_result = generate(data.content)
    return {"result": "표준문서 ID"}


# 2-2. 항목추가/수정 (텍스트 -> 변경목록 List, 업데이트된 context)
@app.post("/modify")
def modify_term(data: modify_form):
    pprint(data)
    modify_result = modify(data.request, data.current, data.context)
    return {"result": {"answer": "[변경 List]", "context": "업데이트된 context"}}


# 3. 챗봇 ( 질문, context List -> 답변, 업데이트된 context List ) ----------------------------------------------------
class chat_form(BaseModel):
    # task: str = "chat"
    request: str
    context: list

@app.post("/chat")
def chatbot(data: chat_form):
    task_result = tasker(data.request)
    chat_result = chat(data.request, data.context)
    # print(chat_result)
    return {"result" : chat_result , "task" : task_result}
