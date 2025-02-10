from module.global_var import conn
import pandas as pd
from sqlalchemy import text

# ✅ term_list 테이블을 미리 생성 (id를 PK로 지정)
with conn.connect() as connection:
    connection.execute(text("""
        CREATE TABLE IF NOT EXISTS term_list (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            company_id INT,
            content TEXT,
            evaluation VARCHAR(50),
            title VARCHAR(255),
            summary TEXT
        )
    """))
    connection.execute(text("""
        CREATE TABLE IF NOT EXISTS company (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255),
            `rank` VARCHAR(10),
            logo VARCHAR(255),
            link VARCHAR(255)
        )
    """))
    connection.commit()

print("✅ 테이블 생성 완료!")

# ✅ 엑셀 파일을 읽어서 DataFrame으로 변환
file_path = "./TermList.xlsx"
df = pd.read_excel(file_path)

df = df[['id', 'company_id', 'content', 'evaluation', 'title', 'summary']]

print("✅ 컬럼 순서를 term_list 테이블과 동일하게 변경 완료!")

# ✅ DataFrame을 MySQL 테이블에 삽입
df.to_sql("term_list", conn, if_exists="append", index=False, method="multi")

print("✅ 엑셀 데이터를 term_list 테이블에 성공적으로 삽입했습니다!")

# ✅ site_rank.xlsx 파일을 읽어서 DataFrame으로 변환
file_path = "./site_rank.xlsx"
df = pd.read_excel(file_path)

# ✅ DataFrame을 MySQL 테이블에 삽입
df.to_sql("company", conn, if_exists="append", index=False, method="multi")

print("✅ 엑셀 데이터를 company 테이블에 성공적으로 삽입했습니다!")
