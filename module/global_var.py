import os
from sqlalchemy import create_engine
from transformers import LlamaForCausalLM , PreTrainedTokenizerFast

# 모델을 1번 불러와 전역으로 선언하기 위한 파일
model : LlamaForCausalLM = None
tokenizer : PreTrainedTokenizerFast = None

# # MySQL 커넥터 전역 선언
# MYSQL_USERNAME = os.environ.get('MYSQL_USERNAME')
# MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD')
# conn = create_engine(f'mysql+mysqlconnector://{MYSQL_USERNAME}:{MYSQL_PASSWORD}@localhost:3306/TermCompass')


# MYSQL_USERNAME = os.environ.get('MYSQL_USERNAME')
# MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD')
# MYSQL_HOST = os.environ.get('MYSQL_HOST')
# MYSQL_PORT = os.environ.get('MYSQL_PORT')
# MYSQL_DBNAME = os.environ.get('MYSQL_DBNAME')

# LAW_OPEN_DATA_APIKEY = os.environ.get('LAW_OPEN_DATA_APIKEY') # 국가법령정보 공동활용 API 키 값

# OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY') # openai API 키 값

conn = create_engine(f'mysql+mysqlconnector://{MYSQL_USERNAME}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DBNAME}')