from pprint import pprint
from fastapi import FastAPI, File, UploadFile
from pydantic import BaseModel
import torch
from transformers import LlamaForCausalLM , PreTrainedTokenizerFast

app = FastAPI()

# 0-1. 모델 로드 ------------------------------------------------------------------------------------

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
from module.data_searcher import search_data
from task.review import review
from task.generate import generate
from task.modify import modify
from task.chat import chat

# 1. 검토 (텍스트 or 파일 -> 검토 결과 List) ------------------------------------------------------

# 1-1. 검토 (텍스트)
@app.post("/review_text")
def review_text(data: str):
    return {"result": review(data) }

# 1-2. 검토 (파일)
@app.post("/review_file")
async def review_text(file: UploadFile = File(...)):
    try:
        text = await file2text(file)
        return { "result": review(text) }
    except TypeError as e:
        return {"result": f"파일을 읽을 수 없습니다. {e}"}

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


# 4. !!!!!!!!!![TEST]!!!!!!!!!! 데이터 검색 (키워드 List -> 검색 결과 List) ----------------------------------------------------
class search_form(BaseModel):
    keywords: list = ["항공","보험"]

@app.post("/search")
def search(data: search_form):
    print("검색 키워드 : ",data.keywords)
    # 검색 결과 반환
    return {"result": search_data(data.keywords)}
