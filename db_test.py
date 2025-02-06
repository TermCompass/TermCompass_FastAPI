# TermCompass_DB 도커 배포 후, 실행
# 로컬 상태에서 DB 연결 확인용 코드

import mysql.connector

# MySQL 연결 설정
config = {
    "host": "localhost",  # Docker 컨테이너 내부 네트워크 IP (또는 localhost)
    "port": 3306,         # 기본 MySQL 포트
    "user": "termcompass",    # .env 또는 docker-compose.yml에 설정한 사용자
    "password": "termcompass",  # 비밀번호
    "database": "termcompass"  # 사용할 데이터베이스
}


# MySQL 서버에 연결
try:
    conn = mysql.connector.connect(**config)
    cursor = conn.cursor()
    
    # 데이터 조회 예제
    cursor.execute("SHOW TABLES;")
    tables = cursor.fetchall()
    print("데이터베이스의 테이블 목록:", tables)

    # 연결 종료
    cursor.close()
    conn.close()
except mysql.connector.Error as err:
    print(f"❌ MySQL 연결 오류: {err}")
