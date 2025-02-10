# 특정 테이블의 칼럼 정보 확인
# python test/db_test2.py

from sqlalchemy import create_engine, text
from module.global_var import conn


try:
    # 데이터베이스 연결 테스트
    with conn.connect() as conn:
        print("✅ MySQL 연결 성공!")

        # 테이블 목록 조회
        result = conn.execute(text("SHOW TABLES"))
        tables = [row[0] for row in result.fetchall()]

        print("📌 termcompass 데이터베이스의 테이블 목록:")
        for table in tables:
            print(f" - {table}")

        # 특정 테이블 칼럼 조회 (예: user 테이블)
        table_name = "list_law"

        if table_name in tables:
            result = conn.execute(text(f"DESCRIBE {table_name}"))
            columns = result.fetchall()

            print(f"\n📌 '{table_name}' 테이블의 칼럼 정보:")
            print(f"{'칼럼명':<20} {'데이터 타입':<20} {'NULL 허용':<10} {'키 타입':<10} {'기본값':<10}")
            print("=" * 80)

            for column in columns:
                column_name, data_type, is_nullable, key, default, extra = column
                print(f"{column_name:<20} {data_type:<20} {is_nullable:<10} {key:<10} {default if default else 'NULL':<10}")

        else:
            print(f"⚠️ '{table_name}' 테이블이 존재하지 않습니다.")

except Exception as err:
    print(f"🚨 오류 발생: {err}")