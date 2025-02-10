import os
from sqlalchemy import create_engine
from transformers import LlamaForCausalLM , PreTrainedTokenizerFast

# 모델을 1번 불러와 전역으로 선언하기 위한 파일
model : LlamaForCausalLM = None
tokenizer : PreTrainedTokenizerFast = None

###
# 도커 배포 테스트
###
# MySQL 커넥터 전역 선언
DB1_HOST = os.getenv("DB1_HOST", "db1")
DB2_HOST = os.getenv("DB2_HOST", "db2")

MYSQL_HOST = os.environ.get('MYSQL_HOST', 'localhost')
MYSQL_USERNAME = os.environ.get('MYSQL_USERNAME', 'termcompass')
MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', 'termcompass')
conn = create_engine(f'mysql+mysqlconnector://{MYSQL_USERNAME}:{MYSQL_PASSWORD}@{MYSQL_HOST}:3306/TermCompass')

# conn = create_engine(f'mysql+mysqlconnector://{MYSQL_USERNAME}:{MYSQL_PASSWORD}@{DB1_HOST}:3306/TermCompass')
conn2 = create_engine(f'mysql+mysqlconnector://{MYSQL_USERNAME}:{MYSQL_PASSWORD}@{DB2_HOST}:3307/termcompass_law')

# OpenAI API Key
OPENAI_KEY = os.environ.get('OPENAI_KEY')

# open.law API ID
OPEN_LAW = os.environ.get('OPEN_LAW')