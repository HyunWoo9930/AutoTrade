# config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    APP_KEY = os.getenv('APP_KEY')
    APP_SECRET = os.getenv('APP_SECRET')
    ACCOUNT_NO = os.getenv('ACCOUNT_NO')
    
    # 모의투자 URL (중요!)
    BASE_URL = "https://openapivts.koreainvestment.com:29443"
    
    # 실전투자라면 아래 URL 사용
    # BASE_URL = "https://openapi.koreainvestment.com:9443"
