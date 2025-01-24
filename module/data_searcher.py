from pprint import pprint
from unittest import result
from sqlalchemy import create_engine,text

# 키워드 목록을 넣으면, 각 분야 데이터들을 검색해서 리스트 딕셔너리로 반환하는 모듈

# SQLAlchemy 엔진 생성
conn = create_engine('mysql+mysqlconnector://termcompass:termcompass@localhost:9906/termcompass')

# 데이터 검색
def search_data(keywords : list):
    # keywords: 검색할 키워드 목록
    search_result = {"case" : [], "law" : [], "standard" : []}
    search_result["case"] = search_case(keywords)
    search_result["law"] = search_law(keywords)
    search_result["standard"] = search_standard(keywords)
    return search_result

# 판례 검색
def search_case(keywords: list):
    result = []
    query = text("""
        SELECT DISTINCT cls.case_id, cls.case_name, cls.summary
        FROM case_law cl
        JOIN case_law_summary cls ON cl.case_id = cls.case_id
        WHERE (
            cl.case_name LIKE :keyword OR
            cls.summary LIKE :keyword OR
            cls.판시사항 LIKE :keyword OR
            cls.판결요지 LIKE :keyword OR
            cls.판례내용 LIKE :keyword
        )
    """)

    with conn.connect() as connection:
        for keyword in keywords:
            params = {"keyword": f"%{keyword}%"}
            rows = connection.execute(query, params).fetchall()
            print(f"======================== keyword : {keyword} =======================================")
            
            # 각 row를 문자열 1개로 변환하여 리스트에 추가
            for row in rows:
                print(row)
                result.append(", ".join(row)) 
    return result

    
# 법률 검색
def search_law(keywords : list):
    result = []
    return result

# 표준 검색
def search_standard(keywords : list):
    result = []
    return result
