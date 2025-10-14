# kis_api.py
import requests
import json
import time
from config import Config

class KISApi:
    def __init__(self):
        self.config = Config()
        self.access_token = None
        self.last_request_time = 0
        self.min_interval = 0.5  # 최소 0.2초 간격 (초당 5회)
        
    def _rate_limit(self):
        """API 호출 속도 제한"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self.last_request_time = time.time()
        
    def get_access_token(self):
        """접근 토큰 발급"""
        url = f"{self.config.BASE_URL}/oauth2/tokenP"
        
        headers = {"content-type": "application/json"}
        body = {
            "grant_type": "client_credentials",
            "appkey": self.config.APP_KEY,
            "appsecret": self.config.APP_SECRET
        }
        
        self._rate_limit()  # 속도 제한
        res = requests.post(url, headers=headers, data=json.dumps(body))
        
        if res.status_code == 200:
            self.access_token = res.json()["access_token"]
            print("✅ 토큰 발급 성공!")
            return self.access_token
        else:
            print("❌ 토큰 발급 실패:", res.text)
            return None
    
    def get_current_price(self, stock_code):
        """현재가 조회"""
        url = f"{self.config.BASE_URL}/uapi/domestic-stock/v1/quotations/inquire-price"
        
        headers = {
            "content-type": "application/json",
            "authorization": f"Bearer {self.access_token}",
            "appkey": self.config.APP_KEY,
            "appsecret": self.config.APP_SECRET,
            "tr_id": "FHKST01010100"
        }
        
        params = {
            "fid_cond_mrkt_div_code": "J",
            "fid_input_iscd": stock_code
        }
        
        self._rate_limit()  # 속도 제한
        res = requests.get(url, headers=headers, params=params)
        
        if res.status_code == 200:
            return res.json()["output"]["stck_prpr"]
        else:
            print("❌ 조회 실패:", res.text)
            return None
    
    def get_balance(self):
        """잔고 조회"""
        url = f"{self.config.BASE_URL}/uapi/domestic-stock/v1/trading/inquire-balance"
        
        headers = {
            "content-type": "application/json",
            "authorization": f"Bearer {self.access_token}",
            "appkey": self.config.APP_KEY,
            "appsecret": self.config.APP_SECRET,
            "tr_id": "VTTC8434R"
        }
        
        params = {
            "CANO": self.config.ACCOUNT_NO,
            "ACNT_PRDT_CD": "01",
            "AFHR_FLPR_YN": "N",
            "OFL_YN": "",
            "INQR_DVSN": "02",
            "UNPR_DVSN": "01",
            "FUND_STTL_ICLD_YN": "N",
            "FNCG_AMT_AUTO_RDPT_YN": "N",
            "PRCS_DVSN": "01",
            "CTX_AREA_FK100": "",
            "CTX_AREA_NK100": ""
        }
        
        self._rate_limit()  # 속도 제한
        res = requests.get(url, headers=headers, params=params)
        
        if res.status_code == 200:
            return res.json()
        else:
            print("❌ 잔고 조회 실패:", res.text)
            return None
    
    def buy_stock(self, stock_code, quantity, price=0):
        """주식 매수 (price=0이면 시장가)"""
        url = f"{self.config.BASE_URL}/uapi/domestic-stock/v1/trading/order-cash"
        
        headers = {
            "content-type": "application/json",
            "authorization": f"Bearer {self.access_token}",
            "appkey": self.config.APP_KEY,
            "appsecret": self.config.APP_SECRET,
            "tr_id": "VTTC0802U"
        }
        
        body = {
            "CANO": self.config.ACCOUNT_NO,
            "ACNT_PRDT_CD": "01",
            "PDNO": stock_code,
            "ORD_DVSN": "01" if price == 0 else "00",
            "ORD_QTY": str(quantity),
            "ORD_UNPR": "0" if price == 0 else str(price)
        }
        
        self._rate_limit()  # 속도 제한
        res = requests.post(url, headers=headers, data=json.dumps(body))
        
        if res.status_code == 200:
            print(f"✅ 매수 주문 성공: {stock_code} {quantity}주")
            return res.json()
        else:
            print(f"❌ 매수 주문 실패:", res.text)
            return None
    
    def sell_stock(self, stock_code, quantity, price=0):
        """주식 매도 (price=0이면 시장가)"""
        url = f"{self.config.BASE_URL}/uapi/domestic-stock/v1/trading/order-cash"
        
        headers = {
            "content-type": "application/json",
            "authorization": f"Bearer {self.access_token}",
            "appkey": self.config.APP_KEY,
            "appsecret": self.config.APP_SECRET,
            "tr_id": "VTTC0801U"
        }
        
        body = {
            "CANO": self.config.ACCOUNT_NO,
            "ACNT_PRDT_CD": "01",
            "PDNO": stock_code,
            "ORD_DVSN": "01" if price == 0 else "00",
            "ORD_QTY": str(quantity),
            "ORD_UNPR": "0" if price == 0 else str(price)
        }
        
        self._rate_limit()  # 속도 제한
        res = requests.post(url, headers=headers, data=json.dumps(body))
        
        if res.status_code == 200:
            print(f"✅ 매도 주문 성공: {stock_code} {quantity}주")
            return res.json()
        else:
            print(f"❌ 매도 주문 실패:", res.text)
            return None
