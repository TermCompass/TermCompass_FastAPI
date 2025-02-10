import requests
import xml.dom.minidom
import xml.etree.ElementTree as ET
import pandas as pd
import re
import openai
import itertools
import ast
import time
import glob
import os

from sqlalchemy import create_engine, text

from module.global_var import OPENAI_KEY

# # SQLAlchemy 엔진 생성
MYSQL_USERNAME = os.environ.get('MYSQL_USERNAME')
MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD')
conn = create_engine(f'mysql+mysqlconnector://{MYSQL_USERNAME}:{MYSQL_PASSWORD}@localhost:3306/TermCompass')

# OpenAPI 클라이언트 설정
import openai


#파일의 apikey불러오기
openai_api_key_path = "./admin/api_key/openai_api_key.txt"
with open(openai_api_key_path, "r") as f:
    openai_api_key = f.read()

client = openai.OpenAI(
        api_key=OPENAI_KEY,
    )


def load_list_law_api(api_key = 'kyj9447', PageNumber = 1, display = 100):
    """
    현행법령 목록 조회하는 함수입니다.
    현행법령은 판례와 새로 생성되는 법령의 수가 많질 않습니다. 그래서 PageNumber을 1로 설정해도 충분할 것 같습니다.
        
    """
    KeyWord = ['약관', '개인정보', '공정거래', '전자상거래', '정보통신망']
    data = []
    for keyword in KeyWord:
        url = f"http://www.law.go.kr/DRF/lawSearch.do?OC={api_key}&target=law&type=XML&display={display}&page={PageNumber}&query={keyword}"
        response = requests.get(url)
        xml_str = response.text
        root = ET.fromstring(xml_str)
        
        for law in root.findall(".//law"):
            law_id = law.findtext("법령일련번호")  # 법령일련번호
            law_name = law.findtext("법령명한글")
            law_date1 = law.findtext("공포일자")
            law_date2 = law.findtext("시행일자")
            if law_id and law_name and law_date1 and law_date2:
                data.append({"law_id": law_id, "law_name": law_name, "publication_date": law_date1, "effective_date": law_date2})

    df = pd.DataFrame(data)
    print(f"[load_list_law_api] 최신 현행법령 {len(df)}개를 불러왔습니다!")
    df.reset_index(drop=True, inplace=True)
    return df


def Filtering_list_law(sentences):
    """
    (ex) '약관' 키워드로 법령목록 검색 시, '농약관리법'이라는 법령도 같이 탐색되는 문제가 발생.
    위와 같은 문제를 Llama 모델을 통하여 분류하기 위한 함수.
    => 법령목록에서 ['약관', '개인정보', '공정거래', '전자상거래', '정보통신망]에 관련된 목록만 추출하기 위한 LLM 모델 호출
    """
    response = client.chat.completions.create(
        model='gpt-4o',
        messages=[{"role":"system",
                   "content":"""당신은 매우 철저하게 법령을 분류하는 조수입니다.
                   입력으로는 리스트 형태의 법령 제목들이 들어옵니다.
                   답변으로는 각 법령 제목들에 대한 리스트 형태의 분류 결과를 제공합니다.
                   답변은 무조건 리스트형태로만 제공해야 합니다!
                   법령 제목이 들어왔을 때, [약관', '개인정보', '공정거래', '전자상거래', '정보통신망'] 키워드에 관련된 법령인 경우에 해당 키워드를 답변으로 제공합니다.
                   해당 키워드와 관련이 없는 경우, '해당사항_없음'을 답변으로 제공합니다.

                   (예시1)
                   입력:
                   ['전자상거래 등에서의 소비자보호에 관한 법률', '농약관리법 시행령', '물가안정에 관한 법률']
                   답변:
                   ['전자상거래', '해당사항_없음', '해당사항_없음']

                   (예시2)
                   입력:
                   ['농약관리법 시행령', '가맹사업거래의 공정화에 관한 법률 시행령']	
                   답변:
                   ['해당사항_없음', '공정거래']
                   """},
                  {"role":"user","content":f"{sentences}"}],
        temperature =  0.1,
        top_p = 0.1
    )
    summary = response.choices[0].message.content
    # 해당 목록만 반환하기
    return summary


def call_list_law(law : pd.DataFrame):
    """
    불러온 법령목록에서 법령이름(law['law_name'])을 활용하여, 해당 법령을 라벨링 및 ['약관', '개인정보', '공정거래', '전자상거래', '정보통신망]에 관련된 법령데이터 목록만 남김
    """
    lst = []
    for i in range(0, int(len(law['law_name']) / 10 + 1)):   # 모든 법령목록에 대하여 한 번에 라벨링할 경우, 에러가 발생하기도 함. LLM API 호출 횟수와 에러율을 줄이기 위해 한 번에 10개의 법령목록에 대하여 연산을 수행함. 
        list_ = [law_ for law_ in law['law_name'][(10 * i):(10 * (i + 1))]]
        a = Filtering_list_law(sentences=list_)
        lst.append(ast.literal_eval(a))
        # print(f"{i}")
        print(f"[call_list_law] {10 * i} ~ {10 * (i + 1)} 범위의 법령목록 라벨링 완료!")
        # time.sleep(10) # Sambanova cloud API(개발용 API)를 사용하는 경우에만, 타임슬립.

    lst = list(itertools.chain.from_iterable(lst))
    law['key_word']= lst

    # "해당사항_없음"이 아닌 행만 남기기
    law = law[law['key_word'] != '해당사항_없음']
    
    # 필요하다면 인덱스 재정렬
    law.reset_index(drop=True, inplace=True)

    return law

# DB의 특정 테이블 불러오기
def load_list_db(table_name = "list_law"):

    query = "SHOW TABLES;"
    df = pd.read_sql(query, conn)

    if len(df) != 0:
        query = f"SELECT * FROM `{table_name}`;"  # 테이블명에 한글, 숫자, 특수문자가 있으므로 백틱(`)으로 감싸야 함
        df = pd.read_sql(query, conn)
        return df
    
    else:
        print(f"[load_list_db] {table_name} 테이블이 존재하지 않습니다.")

        # 테이플 열 이름 참고를 위한 데이터 1개 불러오기
        df = load_list_law_api(api_key="kyj9447", PageNumbers=1, display=1)
        columns = df.columns

        # 빈 데이터프레임 생성
        empty_df = pd.DataFrame(columns=columns)

        # 빈 테이블 생성
        empty_df.to_sql(table_name, conn, index=False, if_exists="fail")

        # 테이블 형식이 지정된 빈 데이터프레임 반환
        return empty_df
    

def process_row_law(law, api_key = "kyj9447"):
    """
    법령목록을 활용하여, 세부 법령 DataBase를 생성하는 함수.
    """
    ids = law['law_id']

    for id in ids:
        url = f"http://www.law.go.kr/DRF/lawService.do?OC={api_key}&target=law&MST={id}&type=XML"
        
        response = requests.get(url)
        xml_str = response.text
        root = ET.fromstring(xml_str)
        time.sleep(1)
        
        rows = []
        law_name = root.findtext(".//법령명_한글")
        law_sum_name = root.findtext(".//법령명약칭")
        rows.append({
            '조항번호': '',
            '항': '',
            '호': '',
            '목': '',
            '내용': f'{law_name} (약칭 : {law_sum_name})'
        })
        
        for art_elem in root.findall('.//조문단위'):
            art_no = art_elem.findtext('조문번호', default='')
            art_title = art_elem.findtext('조문제목', default='')
            art_label = f"제{art_no}조({art_title})" if art_no else art_title
        
            art_content = art_elem.findtext('조문내용', default='').strip()
            if art_content:
                rows.append({
                    '조항번호': art_label,
                    '항': '',
                    '호': '',
                    '목': '',
                    '내용': art_content
                })
        
        
            para_elems = art_elem.findall('.//항')
            for para_elem in para_elems:
                para_no = para_elem.findtext('항번호', default='').strip()
                para_content = para_elem.findtext('항내용', default='').strip()
        
        
                has_ho = para_elem.findall('.//호')
                if para_content and not has_ho:
                    rows.append({
                        '조항번호': art_label,
                        '항': para_no,
                        '호': '',
                        '목': '',
                        '내용': para_content
                    })
        
                ho_elems = para_elem.findall('.//호')
                for ho_elem in ho_elems:
                    ho_no = ho_elem.findtext('호번호', default='').strip()
                    ho_content = ho_elem.findtext('호내용', default='').strip()
        
                    if para_content:
                        rows.append({
                            '조항번호': art_label,
                            '항': para_no,
                            '호': '',
                            '목': '',
                            '내용': para_content
                        })
                        para_content = ''  
                    
                    rows.append({
                        '조항번호': art_label,
                        '항': para_no,
                        '호': int(ho_no.split('.')[0]),
                        '목': '',
                        '내용': ho_content
                    })
        
                    mok_elems = ho_elem.findall('.//목')
                    for mok_elem in mok_elems:
                        mok_no = mok_elem.findtext('목번호', default='').strip()
                        mok_content = mok_elem.findtext('목내용', default='').strip()
                        
                        rows.append({
                            '조항번호': art_label,
                            '항': para_no,
                            '호': int(ho_no.split('.')[0]),
                            '목': mok_no.split('.')[0],
                            '내용': mok_content
                        })
        
        df = pd.DataFrame(rows, columns=['조항번호','항','호','목','내용'])
        df.columns = ['article_number','paragraph','subparagraph','item','text']

        law_na = law_name.replace(' ', '_')
        
        df.to_sql(f"{id}_{law_na}", conn, if_exists="replace", index=False)
        
    print("[process_row_law] 법령 DataBase 생성 완료!")
    # 함수 끝! return 없음!


def update_law():
    """
    법령 DB를 최신화하는 함수입니다.
    현행법령 목록과 보유하고 있는 법령 목록을 비교한 후, 법령DB를 최신화(생성, 삭제)합니다.
    같은 법령이더라도 법령이 최신화된 경우, 법령일련번호가 다르게 부여됩니다.
    (ex)
    [law_id | law_name | publication_date | effective_date]
    [267737 | 개인정보 보호위원회 직제 시행 규칙 | 20241219 | 20241231]
    [268957 | 개인정보 보호위원회 직제 시행 규칙 | 20250131 | 20250131]
    """
    ### 법령목록 최신화 함수
    # 법령목록 DB를 가져오기
    list_law1 = load_list_db(table_name='list_law_')
    
    list_law1['law_id'] = list_law1['law_id'].astype(str)

    # 최신 법령 목록 가져오기(API 호출)
    list_law2 = load_list_law_api()
    list_law2 = call_list_law(law=list_law2)

    ##### 두 DataFrame을 비교하기 (데이터 처리)
    # - 기존 법령목록 DB에도 있고, 최신 법령 목록에도 있는 법령 -> 유지
    # None

    # - 기존 법령목록 DB에 있지만, 최신 법령 목록에는 없는 법령 -> 삭제
    df_only_in_list_law1 = list_law1[~list_law1['law_id'].isin(list_law2['law_id'])]
    if len(df_only_in_list_law1) != 0:
        print(df_only_in_list_law1)
        
        name_list = []
        for name in df_only_in_list_law1['law_name']:
            name_list.append(name)

        ids_list = []
        for id in df_only_in_list_law1['law_id']:
            ids_list.append(id)

        # DB 연결 및 테이블 삭제
        with conn.connect() as conn:
            for law_id, law_name in zip(ids_list, name_list):
                # 테이블 이름 생성
                law_na = law_name.replace(' ', '_')
                key_table_name = f"{law_id}_{law_na}"
                table_name = f"{law_id}_keyword_{law_na}"

                # key_table_name 삭제 시도
                try:
                    drop_query = text(f"DROP TABLE IF EXISTS `{key_table_name}`;")
                    conn.execute(drop_query)
                    print(f"테이블 '{key_table_name}' 삭제 완료.")
                except Exception as e:
                    print(f"테이블 '{key_table_name}' 삭제 실패: {e}")

                # table_name 삭제 시도
                try:
                    drop_query = text(f"DROP TABLE IF EXISTS `{table_name}`;")
                    conn.execute(drop_query)
                    print(f"테이블 '{table_name}' 삭제 완료.")
                except Exception as e:
                    print(f"테이블 '{table_name}' 삭제 실패: {e}")

        list_law2.to_sql("list_law_", conn, if_exists="replace", index=False)
        print(f"[update_law] {len(df_only_in_list_law1)}개의 법령 최신화 (삭제)")

    df_only_in_list_law2 = list_law2[~list_law2['law_id'].isin(list_law1['law_id'])]
    if len(df_only_in_list_law2) != 0:
        # keyword 추출용 DB 생성, AI 모델 학습용 DB 생성
        # 해당 DB 생성하는 코드 작성 필요!
        process_row_law(law=df_only_in_list_law2)
        keyword_law(law=df_only_in_list_law2)


        list_law2.to_sql("list_law_", conn, if_exists="replace", index=False)
        print(f"[update_law] {len(df_only_in_list_law2)}개의 법령 최신화 (생성)")

    if (len(df_only_in_list_law1) == 0) and (len(df_only_in_list_law2) == 0):
        print("[update_law] 현재 법령목록이 최신 상태입니다!")
    # return 없음!


def keyword_law(law, api_key = "kyj9447"):
    """
    법령일련번호를 활용하여 세부 법령내용을 키워드 추출용 DB형태로 만드는 함수.
    """
    ids = law['law_id']

    for law_id in [id for id in ids]: # DataFrame 형태의 ids를 리스트 형태로 변환 후, for문에 진행
        url = f"http://www.law.go.kr/DRF/lawService.do?OC={api_key}&target=law&MST={law_id}&type=XML"
        
        response = requests.get(url)
        xml_str = response.text
        root = ET.fromstring(xml_str)
        time.sleep(1)
        
        law_name = root.findtext(".//법령명_한글")
        name = root.findtext(".//소관부처명")
        publication_date = root.findtext(".//공포일자")
        effective_date = root.findtext(".//시행일자")
    
        df2_data = {"law_id": [f"{law_id}"], "law_name": [f"{law_name}"], "name": [f"{name}"], "publication_date": [f"{publication_date}"], "effective_date": [f"{effective_date}"]}
        df2 = pd.DataFrame(df2_data).iloc[0].to_frame().T
    
        root = ET.fromstring(xml_str)
        
        rows = []
        
        for article_elem in root.findall('.//조문단위'):
            article_no = article_elem.findtext('조문번호', default='')
            article_title = article_elem.findtext('조문제목', default='')
            clause_label = f"제{article_no}조({article_title})" if article_no else article_title
            
            para_elems = article_elem.findall('.//항')
            if not para_elems:
                # 항이 없으면 조문내용만 '내용'으로 처리하거나 생략
                continue
            
            for para_elem in para_elems:
                para_no = para_elem.findtext('항번호', default='').strip()
                para_content = para_elem.findtext('항내용', default='').strip()
                
                # 항 내용을 먼저 한 행에 담는다
                rows.append({
                    '조항번호': clause_label,
                    '항': para_no,
                    '내용': para_content
                })
                
                # <호> 순회
                for ho_elem in para_elem.findall('.//호'):
                    ho_no = ho_elem.findtext('호번호', default='').strip()
                    ho_cont = ho_elem.findtext('호내용', default='').strip()
                    ho_cont_clean = re.sub(r'^[\s]*\d+\.\s*', '', ho_cont)
                    combined = f"{ho_no} {ho_cont_clean}".strip()
        
                    rows.append({
                        '조항번호': clause_label,
                        '항': para_no,
                        '내용': combined
                    })
        
        df = pd.DataFrame(rows, columns=['조항번호','항','내용'])
        
        df_grouped = (
            df.groupby(["조항번호", "항"])["내용"]
              .apply(lambda rows: " ".join(rows)) 
              .reset_index(name="내용")
        )
        df_grouped = df_grouped.rename(columns={"조항번호": "article_number", "항": "paragraph", "내용": "text"})
        
        df2 = pd.concat([df2] * len(df_grouped), ignore_index=True)
        merged_df = pd.concat([df2, df_grouped], axis=1)
        
        law_na = law_name.replace(' ', '_')
        
        # merged_df.to_excel(f"./Data/Dataframe/{law_id}_keyword_{law_na}.xlsx", index=False)
        merged_df.to_sql("law", conn, if_exists="append", index=False) # 저장

    print("[keyword_law] keyword 추출용 DataBase 생성 완료!")
    # return 없음! 


# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!파이프라인!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

# 초기 사전 세팅 / DB가 비어있는 상태에서 최초 1회만 실행 ( 2개 )
def init_setup():
    law = load_list_law_api()
    law = call_list_law(law=law)

    # path = './Data/Dataframe/'
    # os.makedirs(path, exist_ok=True)
    # law.to_excel(f"{path}법령목록.xlsx", index=False)

    ##### DataFrame -> DataBase형태로 변환하는 코드 필요! #####
    ##### DataFrame -> DataBase형태로 변환하는 코드 필요! #####
    ##### DataFrame -> DataBase형태로 변환하는 코드 필요! #####

    # process_row_law(law=law)
    keyword_law(law = law)
    
    # return 없음!



init_setup()
# update_law()

