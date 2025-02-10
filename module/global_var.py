import os
from sqlalchemy import create_engine
from transformers import LlamaForCausalLM , PreTrainedTokenizerFast

# 모델을 1번 불러와 전역으로 선언하기 위한 파일
model : LlamaForCausalLM = None
tokenizer : PreTrainedTokenizerFast = None

# ===========
# 로컬 DB와 연결
# ===========

# # MySQL 커넥터 전역 선언
# MYSQL_USERNAME = os.environ.get('MYSQL_USERNAME')
# MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD')
# MYSQL_HOST = os.environ.get('MYSQL_HOST')
# MYSQL_PORT = os.environ.get('MYSQL_PORT')
# MYSQL_DBNAME = os.environ.get('MYSQL_DBNAME')

conn = create_engine(f'mysql+mysqlconnector://{MYSQL_USERNAME}:{MYSQL_PASSWORD}@localhost:3307/{MYSQL_DBNAME}')



# ===========
# 클라우드 DB와 연결
# ===========

# MYSQL_USERNAME = os.environ.get('MYSQL_USERNAME')
# MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD')
# MYSQL_HOST = os.environ.get('MYSQL_HOST')
# MYSQL_PORT = os.environ.get('MYSQL_PORT')
# MYSQL_DBNAME = os.environ.get('MYSQL_DBNAME')
# conn = create_engine(f'mysql+mysqlconnector://{MYSQL_USERNAME}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DBNAME}')