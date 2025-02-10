import asyncio
import time
from fastapi import WebSocket
import requests
import xml
import xml.etree.ElementTree as ET
import pandas as pd
import re
import json
import os

# 웹소켓 send 함수
from module.websocket_sender import ws_send

# SQLAlchemy 엔진 생성
from sqlalchemy import create_engine, inspect

MYSQL_USERNAME = os.environ.get('MYSQL_USERNAME')
MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD')

LAW_OPEN_DATA_APIKEY = os.environ.get('LAW_OPEN_DATA_APIKEY') # 국가법령정보 공동활용 API 키 값
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')

conn = create_engine(f'mysql+mysqlconnector://{MYSQL_USERNAME}:{MYSQL_PASSWORD}@localhost:3306/TermCompass')
# from module.global_var import conn


# OpenAPI 클라이언트 설정
import openai

# #파일의 apikey불러오기
# openai_api_key_path = "./admin/api_key/openai_api_key.txt"
# with open(openai_api_key_path, "r") as f:
#     openai_api_key = f.read()

# client = openai.OpenAI(
#         api_key=openai_api_key,
#     )

client = openai.OpenAI(
        api_key=OPENAI_API_KEY,
    )

# 요약 함수
def llm_model_for_summarize_case_law(sentences):
    """
    판례내용을 언어모델로 요약하는 함수입니다.
    판례요약은 Sambanova Cloud의 API 호출을 통해서, Llama-3.1-405B 모델을 불러옵니다.
    사전에 작성된 프롬프트와 판례내용을 입력값으로 넣어서 구조화된 요약문을 얻을 수 있습니다.
    """

    if len(sentences) > 16000:
            print(f"예외처리 : 판례의 길이가 Llama3.1-405B 모델의 입력 토큰 범위를 벗어났습니다.")
            return "판례의 길이가 너무 깁니다."
    if sentences == "판례내용이 없습니다.":
            print(f"[summarize_case_law_detail] 예외처리 : 판례 내용이 없습니다.")
            return "판례내용이 없습니다."        

    response = client.chat.completions.create(
        model='gpt-4o',
        messages=[{"role":"system",
                   "content":"""당신은 매우 철저하게 판례를 요약하는 조수입니다.
                   출력 형식
                   당신의 응답은 다음과 같은 정확한 구조를 따라야 합니다. 반드시 최종 답변을 포함하십시오.
                   "(사건 배경) 원고가 항소를 하게된 배경에 대하여 문장으로 서술하시오. 글자 수는 100자 이내로 작성하시오.
                   "(판결 요지) 법원은 해당 사건에 대하여 왜 판결했는지를 문장으로 서술하시오. 글자 수는 200자 이내로 작성하시오."
                   """},
                  {"role":"user","content":f"{sentences}"}],
        temperature =  0.1,
        top_p = 0.1
    )
    summary = response.choices[0].message.content
    return summary

# 개요 요약 함수
def llm_model_for_summarize_case_law1(sentences):
    """
    판례내용을 언어모델로 요약하는 함수입니다.
    판례요약은 Sambanova Cloud의 API 호출을 통해서, Llama-3.1-405B 모델을 불러옵니다.
    사전에 작성된 프롬프트와 판례내용을 입력값으로 넣어서 구조화된 요약문을 얻을 수 있습니다.
    """

    if len(sentences) > 16000:
            print(f"예외처리 : 판례의 길이가 Llama3.1-405B 모델의 입력 토큰 범위를 벗어났습니다.")
            return "판례의 길이가 너무 깁니다."
    if sentences == "판례내용이 없습니다.":
            print(f"[summarize_case_law_detail] 예외처리 : 판례 내용이 없습니다.")
            return "판례내용이 없습니다."        

    response = client.chat.completions.create(
        model='gpt-4o',
        messages=[{"role":"system",
                   "content":"""당신은 매우 철저하게 판례를 요약하는 조수입니다.
                   출력 형식
                   당신의 응답은 다음과 같은 정확한 구조를 따라야 합니다. 반드시 최종 답변을 포함하십시오.
                   "(사건 배경) 재판의 배경에 대하여 문장으로 서술하시오. 글자 수는 100자 이내로 작성하시오.
                   """},
                  {"role":"user","content":f"{sentences}"}],
        temperature =  0.1,
        top_p = 0.1
    )
    summary = response.choices[0].message.content
    return summary

# 요지 요약 함수
def llm_model_for_summarize_case_law2(sentences):
    """
    판례내용을 언어모델로 요약하는 함수입니다.
    판례요약은 Sambanova Cloud의 API 호출을 통해서, Llama-3.1-405B 모델을 불러옵니다.
    사전에 작성된 프롬프트와 판례내용을 입력값으로 넣어서 구조화된 요약문을 얻을 수 있습니다.
    """

    if len(sentences) > 16000:
            print(f"예외처리 : 판례의 길이가 Llama3.1-405B 모델의 입력 토큰 범위를 벗어났습니다.")
            return "판례의 길이가 너무 깁니다."
    if sentences == "판례내용이 없습니다.":
            print(f"[summarize_case_law_detail] 예외처리 : 판례 내용이 없습니다.")
            return "판례내용이 없습니다."        

    response = client.chat.completions.create(
        model='gpt-4o',
        messages=[{"role":"system",
                   "content":"""당신은 매우 철저하게 판례를 요약하는 조수입니다.
                   출력 형식
                   당신의 응답은 다음과 같은 정확한 구조를 따라야 합니다. 반드시 최종 답변을 포함하십시오.
                   "(판결 요지) 법원은 해당 사건에 대하여 왜 판결했는지를 문장으로 서술하시오. 글자 수는 200자 이내로 작성하시오."
                   """},
                  {"role":"user","content":f"{sentences}"}],
        temperature =  0.1,
        top_p = 0.1
    )
    summary = response.choices[0].message.content
    return summary

# 판례 목록 불러오기 (API)
def load_list_api(api_key = LAW_OPEN_DATA_APIKEY, PageNumbers = 3, display = 100):
    """
    국가법령정보 공동활용 API(https://open.law.go.kr/LSO/openApi/guideResult.do)를 활용해서, 최신 판례들의 목록을 불러오는 함수입니다.
    판례목록을 불러올 때, 페이지(Page) 단위로 불러옵니다.
    한 페이지에는 100개의 판례목록을 제공합니다.
    기본설정은 최신 판례 300개의 목록을 가져오도록 설정되어있습니다. (PageNumber = 3)
    """
    for PageNumber in range(1, PageNumbers+1):
        url = f"http://www.law.go.kr/DRF/lawSearch.do?OC={api_key}&target=prec&display={display}&page={PageNumber}&search=2&query=약관"
        print(url)
        response = requests.get(url)
        xml_str = response.text
        root = ET.fromstring(xml_str)

        # 데이터 저장을 위한 리스트
        data = []

        # 필요한 요소 추출
        for case in root.findall(".//prec"):
            case_id = case.findtext("판례일련번호")  # 판례일련번호
            case_name = case.findtext("사건명")  # 사건명
            judgment_date = case.findtext("선고일자")  # 선고일자
            if case_id and case_name and judgment_date:
                data.append({"case_id": case_id, "case_name": case_name, "judgment_date": judgment_date})

        if PageNumber==1:
            df = pd.DataFrame(data)
        else:
            df_ = pd.DataFrame(data)

            df = pd.concat([df, df_], axis=0)

        time.sleep(1) # 서버 과부화 예방을 위해, 1초에 하나의 request를 실행하도록 설정하였습니다.
    print(f"[load_list_of_case_law_from_openlawAPI] 최신 판례목록 {PageNumbers * display}개를 불러왔습니다!")
    df.reset_index(drop=True, inplace=True)
    return df


# DB의 특정 테이블 불러오기
def load_list_db(table_name = "case_law"):

    if table_name in inspect(conn).get_table_names():

        df = pd.read_sql_table(table_name, conn)
        return df
    
    else:
        print(f"[load_list_db] {table_name} 테이블이 존재하지 않습니다.")

        # 테이플 열 이름 참고를 위한 데이터 1개 불러오기
        df = load_list_api(api_key=LAW_OPEN_DATA_APIKEY, PageNumbers=1, display=1)
        columns = df.columns

        # 빈 데이터프레임 생성
        empty_df = pd.DataFrame(columns=columns)

        # 빈 테이블 생성
        empty_df.to_sql(table_name, conn, index=False, if_exists="fail")

        # 테이블 형식이 지정된 빈 데이터프레임 반환
        return empty_df

# df1 = load_list_api(api_key = LAW_OPEN_DATA_APIKEY, PageNumbers = 1)
# df1.to_sql("case_law", conn, if_exists="replace", index=False)
# df1 = load_list_api(api_key = LAW_OPEN_DATA_APIKEY, PageNumbers = 3)
# df1

# # 중복된 행 확인
# duplicates = df1[df1.duplicated(subset=["case_id"], keep=False)]
# print(duplicates)


# df2 = load_list_db(table_name = "case_law")
# df2

# 특정 판례번호의 판례내용 불러오기 (API)

# def load_case_law_detail(api_key = LAW_OPEN_DATA_APIKEY, number=241977):
#     """
#     판례 요약을 위해, 세부 판례본문에 대한 데이터 전처리를 수행하는 함수입니다.
#     판례본문에서 <판례내용>의 내용과 길이를 추출 및 반환합니다.
#     판례내용의 길이는 모델 요약하는 과정에서 사용됩니다.(라마 모델의 16000토큰 이내)

#     """
#     url = f"http://www.law.go.kr/DRF/lawService.do?OC={api_key}&target=prec&ID={number}"
#     response = requests.get(url)
#     xml_str = response.text
#     dom = xml.dom.minidom.parseString(xml_str)
#     pretty_xml = dom.toprettyxml(indent="  ")
#     # <판례내용>과 </판례내용> 사이의 내용 추출
#     case_contents = re.findall(r'<판례내용><!\[CDATA\[(.*?)\]\]></판례내용>', pretty_xml, re.DOTALL)
#     # <br> 및 <br/> 기준으로 문장 나누기
#     if case_contents:
#         for idx, content in enumerate(case_contents):
#             sentences = re.split(r'<br\s*/?>', content)  # <br> 또는 <br/> 기준으로 분할
#     else:
#         sentences = "판례내용이 없습니다."
#     return sentences

# sentences= load_case_law_detail(api_key = LAW_OPEN_DATA_APIKEY, number=241977)
# print(sentences)

# 특정 판례번호의 상세 내용을 받아 요약, JSON 저장(및 경로 기록)
# "case_id,case_name,case_number,judgment_date,verdict,court_name,case_type,judgment_type,summary,path"

def process_row(id):

    # print("판례번호:", id, "처리중...")
    url = f"http://www.law.go.kr/DRF/lawService.do?OC={LAW_OPEN_DATA_APIKEY}&target=prec&ID={id}"

    # response = requests.get(url)

    # xml_str = response.text
    # print(xml_str)
    # dom = xml.dom.minidom.parseString(xml_str)
    # pretty_xml = dom.toprettyxml(indent="  ")
    # root = ET.fromstring(pretty_xml)

    response = requests.get(url)
    xml_str = response.text
    root = ET.fromstring(xml_str)

    # JSON 변환을 위한 딕셔너리 생성
    case_data = {
        "case_id": root.findtext("판례정보일련번호"),
        "case_name": root.findtext("사건명"),
        "case_number": root.findtext("사건번호"),
        "judgment_date": root.findtext("선고일자"),
        "verdict": root.findtext("선고"),
        "court_name": root.findtext("법원명"),
        "case_type": root.findtext("사건종류명"),
        "judgment_type": root.findtext("판결유형"),
        "summary": llm_model_for_summarize_case_law1(root.findtext("판례내용")),
        "holding": llm_model_for_summarize_case_law2(root.findtext("판결요지")),
        # "path":  json_file_path,
    }

    # JSON 파일 경로 (년도별)
    year = case_data["judgment_date"][:4]
    if year.isdigit() and len(year) == 4 :
        json_file_path = f'./Data/File/{year}/판례_{id}.json'
    else:
        json_file_path = f'./Data/File/ERROR/판례_{id}.json'

    # JSON에 경로 기록
    case_data["path"] = json_file_path

    # 디렉터리가 존재하지 않으면 생성
    os.makedirs(os.path.dirname(json_file_path), exist_ok=True)

    # # 판시사항, 판결요지, 판례내용 처리
    # for tag in ["판시사항", "판결요지", "판례내용"]:
    #     text = root.findtext(tag)
    #     if text:
    #         # <br> 또는 <br/> 기준으로 분할 후 공백 제거
    #         sentences = [s.strip() for s in re.split(r'<br\s*/?>', text) if s.strip()]
    #         try:
    #             case_data[tag] = sentences[0]
    #         except:
    #             case_data[tag] = ""
    #     else:
    #         case_data[tag] = ""

    # JSON 파일 저장
    with open(json_file_path, 'w', encoding='utf-8') as f:
        json.dump(case_data, f, ensure_ascii=False, indent=4)
        
    time.sleep(1)

    return case_data


# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!파이프라인!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

# 초기 사전 세팅 / DB가 비어있는 상태에서 최초 1회만 실행 ( 1개 )
def init_setup():
    
    text = "초기 세팅 실행...\n"
    # await ws_send(ws,text)
    print(text)

    df1 = load_list_api(api_key=LAW_OPEN_DATA_APIKEY, PageNumbers=1, display=1)
    df1.to_sql("case_law", conn, if_exists="replace", index=False) # 저장

    # case_ids = df1["case_id"].tolist()
    # summary_list = []
    # for case_id in case_ids:
    #     print("판례번호:", case_id, "처리중...")
    #     summary_list.append(process_row(case_id))

    # 차집합 df에 for문 사용, summary_df 데이터프레임 생성
    summary_list = []
    for index, target_row in enumerate(df1.itertuples()):

        text = f"{index} 판례번호:, {target_row.case_id}, 사건명:, {target_row.case_name},  처리중... "
        # await ws_send(ws,text)
        print(text)

        summary_list.append(process_row(target_row.case_id))

    summary_df = pd.DataFrame(summary_list)
    summary_df.to_sql("case_law_summary", conn, if_exists="replace", index=False) # 저장
                
    text = "초기 세팅 완료\n"
    # await ws_send(ws,text)
    print(text)

# 최신 판례 업데이트
def update_case_law():

    text = "업데이트 실행...\n"
    # await ws_send(ws,text)
    print(text)

    df1 = load_list_api(api_key=LAW_OPEN_DATA_APIKEY, PageNumbers=3, display=100) # 최신 판례 로드 10개 (API)
    df2 = load_list_db() # DB의 기존 판례 로드

    # 'case_id'을 기준으로 차집합 생성
    target_df = df1.merge(df2, how='left', indicator=True)
    target_df = target_df[target_df['_merge'] == 'left_only'].drop(columns=['_merge'])
    count = target_df.shape[0]

    text = f"{count}개의 신규 판례가 확인되었습니다."
    # await ws_send(ws,text)
    print(text)

    target_df.to_sql("case_law", conn, if_exists="append", index=False) # 저장

    # # 차집합의 'case_id' 리스트를 사용해 summary_df 데이터프레임 생성
    # case_ids = target_df["case_id"].tolist()
    # summary_list = []
    # for case_id in case_ids:
    #     print("판례번호:", case_id, "처리중...")
    #     summary_list.append(process_row(case_id))

    # 차집합 df에 for문 사용, summary_df 데이터프레임 생성
    summary_list = []
    for index, target_row in enumerate(target_df.itertuples()):

        text = f"{index} 판례번호:, {target_row.case_id}, 사건명:, {target_row.case_name}, 처리중... "
        # await ws_send(ws,text)
        print(text)

        summary_list.append(process_row(target_row.case_id))

    summary_df = pd.DataFrame(summary_list)
    summary_df.to_sql("case_law_summary", conn, if_exists="append", index=False) # 저장

    text = "업데이트 완료\n"
    # await ws_send(ws,text)
    print(text)

# init_setup()
# update_case_law()
