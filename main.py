import base64
from pprint import pprint
from fastapi import FastAPI
from pydantic import BaseModel

# modules
from module.file2text import file2text
from model.review import review
from model.generate import generate
from model.modify import modify
from model.chat import chat

app = FastAPI()


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
def generate(data: generate_form):
    pprint(data)
    return {"result": "표준문서 ID"}


# 2-2. 항목추가/수정 (텍스트 -> 변경목록 List, 업데이트된 context)
@app.post("/modify")
def modify(data: modify_form):
    pprint(data)
    return {"result": {"answer": "[변경 List]", "context": "업데이트된 context"}}


# 3. 챗봇 (텍스트 -> 답변, 업데이트된 context) ----------------------------------------------------
class chat_form(BaseModel):
    # task: str = "chat"
    request: str
    context: str


@app.post("/chat")
def chat(data: chat_form):
    pprint(data)
    return {"result": {"answer": "답변", "context": "업데이트된 context"}}
