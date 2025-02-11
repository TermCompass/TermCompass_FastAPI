from io import BytesIO
import re
import traceback
import numpy as np
import uvicorn
import asyncio
from pprint import pprint
from fastapi import FastAPI, File, UploadFile, WebSocket, WebSocketDisconnect, WebSocketException
from pydantic import BaseModel
import torch
from transformers import LlamaForCausalLM , PreTrainedTokenizerFast
import json

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
from admin import case_updater
import module.global_var as global_var
global_var.model = model
global_var.tokenizer = tokenizer

# 0-2. 모듈 로드 ------------------------------------------------------------------------------------
# 모델, 토크나이저 초기화 후에 모듈을 로드해야 전역으로 선언된 모델, 토크나이저를 사용할 수 있음
from module.file2text import file2text
from module.task_planner import keyword_collector, tasker
from module.data_searcher import search_data
from task.review import review
from task.generate import generate
from task.modify import modify
from task.chat import chat
from module.decompress import decompress_data
from module.term_spliter import Text_Pipline
from module.text2formatted import process_and_refine_text
from module.websocket_sender import ping_client
from admin.standard_updater import extract_and_process_pdfs

# 1. 검토 (텍스트 or 파일 -> 검토 결과 List) ------------------------------------------------------

# 1-1. 검토 (텍스트)
@app.post("/review_text")
def review_text(data: str):
    return {"result": review(data) }

# 1-2. 검토 (파일)
@app.post("/review_file")
async def review_file(file: UploadFile = File(...)):
    try:
        text = await file2text(file)
        return { "result": text }
    except TypeError as e:
        return {"result": e}
    except Exception as e:
        return {"result": f"파일을 읽을 수 없습니다. {e}"}

# 1-3. 웹소켓

# # 중지 신호를 위한 Event 객체 생성
# stop_event = asyncio.Event()

@app.websocket("/ws")
async def update_case(websocket: WebSocket): 

    # 웹소켓 입력 후 명령 입력받음
    await websocket.accept()

    # 자동 ping 설정
    ping_task = asyncio.create_task(ping_client(websocket))

    # 종료 명령까지 지속 실행
    try:
        while True:
            data = await websocket.receive_text()
            jsondata = json.loads(data)
            type = jsondata['type']
            print('메세지 수신 : ',type)
            if type == 'test':

                # 내용물 확인
                content = jsondata['content']

                for _ in range(3):
                    await websocket.send_json({"type": "test","content": f"{content}!{content}!{content}!"})
                    print(f"응답 : {{type: test,content:{content}!{content}!{content}!}}")
                    await asyncio.sleep(3)  # 3초 대기
                await websocket.close()
            elif type == 'review':
                # # 중지 신호 초기화
                # stop_event.clear()

                # 내용물 확인
                content = jsondata['content']
                # print('check1')
                # 메타데이터 준비
                file_name = jsondata["fileName"]
                print('file_name : ',file_name)
                file_type = jsondata["fileType"]
                print('file_type : ',file_type)

                # 내용 압축 해제
                compressed_content = jsondata["content"]
                file_content = decompress_data(compressed_content)
                # print('check2')

                # UploadFile 객체 생성
                upload_file = UploadFile(filename=file_name, file=BytesIO(file_content))
                # print('check3')

                # file2text 파이프라인
                text = await file2text(upload_file, file_type)
                # print('check4')

                # 조항 split 파이프라인
                df = Text_Pipline(text, file_name)

                # List로 만들 행 생성
                df['result'] = np.where(df['서브번호'].notna(), df['서브번호'], df['조항번호']) + df['조항명']

                # List 보냄
                textList = df['result'].to_list()
                # print('textList',textList)

                length = len(textList)
                # print('check5')

                # 원문 List 송신
                await websocket.send_json({"type": "total","content": textList, "length":length })
                await asyncio.sleep(0)
                # print('check6')

                #=====================================================================================================
                # # 전체 통합 키워드목록
                # keyword_list = keyword_collector(textList)

                # # 키워드로 참고자료 검색해 목록 작성
                # data_list = search_data(keyword_list)

                # 한 조항씩 검토 후 검토결과 송신
                for index in range(1, len(textList) + 1):

                    # # 중지이벤트
                    # if stop_event.is_set():
                    #     # 중지됨 메세지 보내고 반복문 break
                    #     await websocket.send_json({"type": "stopped"})
                    #     break

                    # 입력 조항의 전후 조항 합치기
                    previous_text = textList[index - 2] if index - 2 >= 0 else ""
                    current_text = textList[index - 1] if index - 1 < len(textList) else ""
                    next_text = textList[index] if index < len(textList) else ""

                    # 텍스트 조합
                    combined_text = f"{previous_text} {current_text} {next_text}".strip()

                    # DB 조회는 현재 조항으로만
                    keyword_list = keyword_collector(current_text)
                    data_list = search_data(keyword_list)

                    # 조합된 조항으로 review
                    current_review = review(combined_text,data_list)
                    # review_dict = json.loads(current_review)
                    # pprint(current_review)

                    await websocket.send_json({"type": "review","number": index, "content": current_review['review'], "grade": current_review['grade']})
                    await asyncio.sleep(0)  # Ensure the message is sent immediately

                # 검토 완료시 Spring에게 end 신호 보내고 세션 종료
                await websocket.send_json({"type": "end"})
                await asyncio.sleep(0)
                await websocket.close()
                break

            # # 중지 이벤트 수신시
            # elif type == 'stop':
            #     # 중지 신호 설정
            #     stop_event.set()

    except WebSocketDisconnect as e:
        print(f"웹소켓 종료 사유 : {str(e)}")
    except WebSocketException as e:
        print(f"웹소켓 예외 발생 : {e}")
    except Exception as e:
        print(f"기타 예외 발생 : {e}")
        traceback.print_exc()

    finally:
        # Ping task 종료
        ping_task.cancel()
        await ping_task  # ping_task가 정상적으로 종료될 때까지 기다림

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

# ADMIN 1. 판례 업데이트 실행
@app.websocket("/case")
async def update_case(websocket: WebSocket): 

    # 웹소켓 입력 후 명령 입력받음
    await websocket.accept()

    # 자동 ping 설정
    # ping_task = asyncio.create_task(ping_client(websocket))

    # try:
    # while True:
    data = await websocket.receive_text()

    # 업데이트 요청
    if data == "update":
        await case_updater.init_setup(websocket)
        await case_updater.update_case_law(websocket)

    # 초기 세팅 요청
    elif data == "init":
        await case_updater.init_setup(websocket)

    # 다른 입력 -> 종료
    else:
        await websocket.send_text("종료\n")
        await websocket.close()
            # break

    # except WebSocketDisconnect as e:
    #     print(f"웹소켓 종료 사유 : {e.code}")
    # except WebSocketException as e:
    #     print(f"웹소켓 예외 발생 : {e}")
    # except Exception as e:
    #     print(f"기타 예외 발생 : {e}")

    # finally:
    #     # Ping task 종료
    #     ping_task.cancel()
    #     try:
    #         await ping_task  # ping_task가 정상적으로 종료될 때까지 기다림
    #     except asyncio.exceptions.CancelledError:
    #         pass  # 취소된 작업이므로 예외를 무시하고 처리

# ================
# 법령 데이터 최신화
# ================
@app.get("/law_setting")
def law_setting():
    law_updater.init_setup()

@app.get("/law_update")
def law_update():
    law_updater.update_law()
        
# ================
# 판례 데이터 최신화
# ================
# @app.get("/case_setting")
# def case_setting():
#     case_updater.init_setup()

@app.get("/case_update")
def case_update():
    case_updater.update_case_law()
    

# ================
# 실행
# ================

# PDF -> HTML 1회 테스트
@app.post("/refine")
async def refine(file: UploadFile = File(...)):

    text = await file2text(file)
    refined = process_and_refine_text(text)

    # 문자 마무리 처리
    refined = refined.replace("\n","") # 줄바꿈문자 삭제
    refined = re.sub(r'<h4>', '<h1>', refined, count=1)  # 첫 번째 <h4> -> <h1> ( 제목 )
    refined = re.sub(r'</h4>', '</h1>', refined, count=1)  # 첫 번째 닫는 </h4> -> </h1>

    return refined

# 모든 PDF -> HTML 처리
@app.post("/standard")
async def refine():
    folder_path = 'standard'
    await extract_and_process_pdfs(folder_path)

    # 결과를 저장
    # result_df.to_sql("standard", conn, if_exists="append", index=True, index_label="id", dtype={'refined_text': types.TEXT()}) # SQL 저장


# if __name__ == "__main__":
#     uvicorn.run(app, host="0.0.0.0", port=8000, ws_max_size=1024 * 1024 * 50)  # Increase to 50MB

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000, ws_max_size=1024 * 1024 * 50)  # Increase to 50MB