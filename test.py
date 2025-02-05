# =====
# 법령 최신화 테스트 세팅 코드
# 
#
# 법령 목록을 오래된 법령 목록으로 교체하여, 최신화 함수가 제대로 수행되는지 확인하기 위함.
#

import pandas as pd

##### SQLAlchemy 엔진 생성
from sqlalchemy import create_engine, inspect, text

DB_USER = "termcompass"
DB_PASSWORD = "termcompass"
port = 9907
DB_HOST = f"127.0.0.1:{port}"
DB_NAME = "termcompass_law"

# DB가 없을 경우 자동 생성
engine = create_engine(f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}")
with engine.connect() as conn:
    conn.execute(text(f"CREATE DATABASE IF NOT EXISTS {DB_NAME};"))

try:
    conn = create_engine(f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}")
    print("MySQL 연결 성공!")
except Exception as e:
    print(f"MySQL 연결 실패: {e}")


# 이전 버전 법령목록 로드 및 DataBase에 추가
excel_file = "./test/법령목록.xlsx"
df = pd.read_excel(excel_file)
df.to_sql("list_law_", conn, if_exists="replace", index=False)

excel_file = "./test/267337_keyword_개인정보_보호위원회_직제_시행규칙.xlsx"
df = pd.read_excel(excel_file)
df.to_sql("267337_keyword_개인정보_보호위원회_직제_시행규칙", conn, if_exists="append", index=False)

excel_file = "./test/267337_개인정보_보호위원회_직제_시행규칙.xlsx"
df = pd.read_excel(excel_file)
df.to_sql("267337_개인정보_보호위원회_직제_시행규칙", conn, if_exists="append", index=False)

print("법령 최신화 테스트 준비 완료!")
print("이제 law_updater.py 로 테스트 진행하면 됩니다!")