from io import BytesIO
import traceback
import numpy as np
import uvicorn
import asyncio
from fastapi import FastAPI, File, UploadFile, WebSocket, WebSocketDisconnect, WebSocketException
import torch
from transformers import LlamaForCausalLM , PreTrainedTokenizerFast
import json

app = FastAPI()

# 0-1. 모델 로드 ------------------------------------------------------------------------------------

# 모델과 토크나이저 로드
model_name = "/app/models/llama-3.2-Korean-Bllossom-3B"
model = LlamaForCausalLM.from_pretrained(model_name, torch_dtype=torch.float16, device_map="auto", local_files_only=True)
tokenizer = PreTrainedTokenizerFast.from_pretrained(model_name)

# 패딩 토큰 설정
tokenizer.pad_token = tokenizer.eos_token
model.config.pad_token_id = tokenizer.pad_token_id

print("모델 객체 타입 " + str(type(model)))
print("토크나이저 객체 타입 " + str(type(tokenizer)))

# 로드 후 전역 변수 업데이트
from admin import case_updater, law_updater
import module.global_var as global_var
global_var.model = model
global_var.tokenizer = tokenizer

# 0-2. 모듈 로드 ------------------------------------------------------------------------------------
# 모델, 토크나이저 초기화 후에 모듈을 로드해야 전역으로 선언된 모델, 토크나이저를 사용할 수 있음
from module.file2text import file2text
from module.task_planner import keyword_collector
from module.data_searcher import search_data
from task.review import review
from module.decompress import decompress_data
from module.term_spliter import Text_Pipline
from module.websocket_sender import ping_client

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

# 1-3. 검토 (웹소켓)
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

                # 내용물 확인
                content = jsondata['content']

                # 메타데이터 준비
                file_name = jsondata["fileName"]
                print('file_name : ',file_name)
                file_type = jsondata["fileType"]
                print('file_type : ',file_type)

                # 내용 압축 해제
                compressed_content = jsondata["content"]
                file_content = decompress_data(compressed_content)

                # UploadFile 객체 생성
                upload_file = UploadFile(filename=file_name, file=BytesIO(file_content))

                # file2text 파이프라인
                text = await file2text(upload_file, file_type)

                # 조항 split 파이프라인
                df = Text_Pipline(text, file_name)

                # List로 만들 행 생성
                df['result'] = np.where(df['서브번호'].notna(), df['서브번호'], df['조항번호']) + df['조항명']

                # List 보냄
                textList = df['result'].to_list()

                length = len(textList)

                # 원문 List 송신
                await websocket.send_json({"type": "total","content": textList, "length":length })
                await asyncio.sleep(0)

                # 한 조항씩 검토 후 검토결과 송신
                for index in range(1, len(textList) + 1):

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

                    await websocket.send_json({"type": "review","number": index, "content": current_review['review'], "grade": current_review['grade']})
                    await asyncio.sleep(0)  # Ensure the message is sent immediately

                # 검토 완료시 Spring에게 end 신호 보내고 세션 종료
                await websocket.send_json({"type": "end"})
                await asyncio.sleep(0)
                await websocket.close()
                break

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
@app.get("/case_setting")
def case_setting():
    case_updater.init_setup()

@app.get("/case_update")
def case_update():
    case_updater.update_case_law()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, ws_max_size=1024 * 1024 * 50)  # Increase to 50MB