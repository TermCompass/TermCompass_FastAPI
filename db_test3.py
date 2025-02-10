# 특정 테이블의 칼럼 정보 확인
# python test/db_test2.py

from sqlalchemy import create_engine, text
from module.global_var import conn


try:
    with conn.connect() as conn:
        print("✅ MySQL 연결 성공!")

        # 테이블 목록 조회
        result = conn.execute(text("SHOW TABLES"))
        tables = [row[0] for row in result.fetchall()]

        print("📌 termcompass 데이터베이스의 테이블 목록:")
        for table in tables:
            print(f" - {table}")

        table_name = "law"

        if table_name in tables:
            result = conn.execute(text(f"DESCRIBE {table_name}"))
            columns = result.fetchall()

            print(f"\n📌 '{table_name}' 테이블의 칼럼 정보:")
            print(f"{'칼럼명':<20} {'데이터 타입':<20} {'NULL 허용':<10} {'키 타입':<10} {'기본값':<10}")
            print("=" * 80)
            for column in columns:
                column_name, data_type, is_nullable, key, default, extra = column
                print(f"{column_name:<20} {data_type:<20} {is_nullable:<10} {key:<10} {default if default else 'NULL':<10}")

            # 테이블 데이터 조회 (튜플로 반환됨)
            data_result = conn.execute(text(f"SELECT * FROM {table_name}"))
            headers = data_result.keys()  # 컬럼 이름 리스트
            rows = data_result.fetchall()

            print(f"\n📌 '{table_name}' 테이블의 데이터:")
            if rows:
                header_str = " | ".join(f"{header:<15}" for header in headers)
                print(header_str)
                print("-" * len(header_str))
                # 각 행을 튜플 인덱스를 사용하여 출력
                for row in rows:
                    # 헤더 순서에 맞춰 인덱스 번호로 접근
                    row_str = " | ".join(f"{str(row[idx]):<15}" for idx in range(len(headers)))
                    print(row_str)
            else:
                print(f"⚠️ '{table_name}' 테이블에 데이터가 없습니다.")
        else:
            print(f"⚠️ '{table_name}' 테이블이 존재하지 않습니다.")

except Exception as err:
    print(f"🚨 오류 발생: {err}")