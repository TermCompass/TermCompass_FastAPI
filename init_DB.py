from module.global_var import conn
import pandas as pd

# 엑셀 파일을 읽어서 DataFrame으로 변환
file_path = "./TermList.xlsx"  # 업로드한 파일 경로
df = pd.read_excel(file_path)

df = df[['id', 'company_id', 'content', 'evaluation', 'title', 'summary']]

print("✅ 컬럼 순서를 termlist 테이블과 동일하게 변경 완료!")

# DataFrame을 MySQL 테이블에 삽입
df.to_sql("term_list", conn, if_exists="append", index=False, method="multi")

print("엑셀 데이터를 MySQL 테이블에 성공적으로 삽입했습니다!")

# 엑셀 파일을 읽어서 DataFrame으로 변환
file_path = "./site_rank.xlsx"  # 업로드한 파일 경로
df = pd.read_excel(file_path)

# df = df[['id', 'company_id', 'content', 'evaluation', 'title', 'summary']]

# print("✅ 컬럼 순서를 termlist 테이블과 동일하게 변경 완료!")

# DataFrame을 MySQL 테이블에 삽입
df.to_sql("company", conn, if_exists="append", index=False, method="multi")

print("엑셀 데이터를 MySQL 테이블에 성공적으로 삽입했습니다!")
