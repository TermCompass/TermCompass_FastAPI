import requests
import xml.dom.minidom
import xml.etree.ElementTree as ET
import pandas as pd
import re
import openai
import itertools
import ast
import time

# # SQLAlchemy 엔진 생성
# from sqlalchemy import create_engine,inspect
# conn = create_engine('mysql+mysqlconnector://termcompass:termcompass@localhost:9906/termcompass')

# OpenAPI 클라이언트 설정
import openai


#파일의 apikey불러오기
openai_api_key_path = "./admin/api_key/openai_api_key.txt"
with open(openai_api_key_path, "r") as f:
    openai_api_key = f.read()

client = openai.OpenAI(
        api_key=openai_api_key,
    )


def load_list_law_api(api_key = 'eogus2469', PageNumber = 1, display = 100):
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


def call_list_law(law):
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
        # time.sleep(10) # Sambanova cloud API를 사용하는 경우에만, 타임슬립.

    lst = list(itertools.chain.from_iterable(lst))
    law['key_word']= lst

    # "해당사항_없음"이 아닌 행만 남기기
    law = law[law['key_word'] != '해당사항_없음']
    
    # 필요하다면 인덱스 재정렬
    law.reset_index(drop=True, inplace=True)

    return law

# # DB의 특정 테이블 불러오기
# def load_list_db(table_name = "list_law"):

#     if table_name in inspect(conn).get_table_names():

#         df = pd.read_sql_table(table_name, conn)
#         return df
    
#     else:
#         print(f"[load_list_db] {table_name} 테이블이 존재하지 않습니다.")

#         # 테이플 열 이름 참고를 위한 데이터 1개 불러오기
#         df = load_list_law_api(api_key="eogus2469", PageNumbers=1, display=1)
#         columns = df.columns

#         # 빈 데이터프레임 생성
#         empty_df = pd.DataFrame(columns=columns)

#         # 빈 테이블 생성
#         empty_df.to_sql(table_name, conn, index=False, if_exists="fail")

#         # 테이블 형식이 지정된 빈 데이터프레임 반환
#         return empty_df
    

def process_row_law(law, api_key = "eogus2469"):
    """
    법령목록을 활용하여, 세부 법령 DataFrame을 생성하는 함수.
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
        
        df.to_excel(f"./Data/Dataframe/{id}_{law_na}.xlsx", index=False)
    print("[process_row_law] 법령 DataFrame 생성 완료!")
    # 함수 끝! return 없음!

def update_law():
    """
    기존 법령 DB와 새로운 법령 DB를 비교하여, DB를 최신화하는 함수입니다.
    """
    ##### DataBase -> DataFrame형태로 변환하는 코드 필요! #####
    ##### DataBase -> DataFrame형태로 변환하는 코드 필요! #####
    ##### DataBase -> DataFrame형태로 변환하는 코드 필요! #####

    old_df = pd.read_excel("./Data/Dataframe/법령목록.xlsx")
    old_df['law_id'] = old_df['law_id'].astype(int)
    old_df['publication_date'] = old_df['publication_date'].astype(int)
    new_df = load_list_law_api()
    new_df = call_list_law(law=new_df)
    new_df['law_id'] = new_df['law_id'].astype(int)
    new_df['publication_date'] = new_df['publication_date'].astype(int)
    new_df['effective_date'] = new_df['effective_date'].astype(int)
    updated_law_ids = []
    # 기존의 법령에서 변경사항이 발생한 경우
    merged_df = pd.merge(old_df, new_df, on='law_id', suffixes=('_old', '_new'))
    for _, row in merged_df.iterrows():
        if row['publication_date_old'] != row['publication_date_new']:  # publication_date가 변경된 경우
            updated_law_ids.append(row['law_id'])
            filtered_df = new_df[new_df['law_id'] == updated_law_ids[-1]]
            old_df = pd.concat([old_df, filtered_df], ignore_index=True)
    #새로운 법령이 추가된 경우
    new_law_ids = set(new_df['law_id']) - set(old_df['law_id'])  # 차집합: new_df에는 있고 old_df에는 없는 law_id
    updated_law_ids.extend(list(new_law_ids))
    for id in updated_law_ids:
        filtered_df = new_df[new_df['law_id'] == id]
        old_df = pd.concat([old_df, filtered_df], ignore_index=True)
 
    if len(updated_law_ids) == 0:
        print("[update_law] 헌행법령 DB가 최신 상태입니다!")
    else:
        old_df.to_excel("./Data/Dataframe/법령목록.xlsx", index=False)

        ##### DataFrame -> DataBase형태로 변환하는 코드 필요! #####
        ##### DataFrame -> DataBase형태로 변환하는 코드 필요! #####
        ##### DataFrame -> DataBase형태로 변환하는 코드 필요! #####    
        
        new_law = pd.DataFrame(updated_law_ids, columns=['law_id'])
        process_row_law(law=new_law, api_key = "eogus2469")
        print(f"[update_law] {len(updated_law_ids)}개의 현행법령 DB를 최신화했습니다!")
 
    # return 없음!


def keyword_law(law, api_key = "eogus2469"):
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
        
                    # (핵심) 호내용 앞에 '1.' '2.' 같은 번호가 있다면 제거
                    #       예: "2. 제1호 외의..." → "제1호 외의..."
                    ho_cont_clean = re.sub(r'^[\s]*\d+\.\s*', '', ho_cont)
        
                    # 최종 출력: "호번호 + (호내용에서 번호 제거한 텍스트)"
                    #           예: "2. 제1호 외의..."
                    combined = f"{ho_no} {ho_cont_clean}".strip()
        
                    rows.append({
                        '조항번호': clause_label,
                        '항': para_no,
                        '내용': combined
                    })
        
        df = pd.DataFrame(rows, columns=['조항번호','항','내용'])
        
        df_grouped = (
            df.groupby(["조항번호", "항"])["내용"]
              .apply(lambda rows: " ".join(rows))  # or "\n".join(rows)
              .reset_index(name="내용")
        )
        df_grouped = df_grouped.rename(columns={"조항번호": "article_number", "항": "paragraph", "내용": "text"})
        
        df2 = pd.concat([df2] * len(df_grouped), ignore_index=True)
        merged_df = pd.concat([df2, df_grouped], axis=1)
        
        law_na = law_name.replace(' ', '_')
        
        merged_df.to_excel(f"./Data/Dataframe/{law_id}_keyword_{law_na}.xlsx", index=False)

        ##### DataFrame -> DataBase형태로 변환하는 코드 필요! #####
        ##### DataFrame -> DataBase형태로 변환하는 코드 필요! #####
        ##### DataFrame -> DataBase형태로 변환하는 코드 필요! #####

    print("[keyword_law] keyword 추출용 Dataframe 생성 완료!")
    # return 없음! 

# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!파이프라인!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

# 초기 사전 세팅 / DB가 비어있는 상태에서 최초 1회만 실행 ( 2개 )
def init_setup():
    law = load_list_law_api()
    law = call_list_law(law=law)
    law.to_excel("./Data/Dataframe/법령목록.xlsx", index=False)

    ##### DataFrame -> DataBase형태로 변환하는 코드 필요! #####
    ##### DataFrame -> DataBase형태로 변환하는 코드 필요! #####
    ##### DataFrame -> DataBase형태로 변환하는 코드 필요! #####

    process_row_law(law=law)
    keyword_law(law = law)

init_setup()





#############################

# 기존 법령DB를 최신화하는 함수 작성 예정


