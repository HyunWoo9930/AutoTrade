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
        self.min_interval = 0.6  # 최소 0.6초 간격 (초당 1.6회) - 안전하게 조정
        
    def _rate_limit(self):
        """API 호출 속도 제한"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self.last_request_time = time.time()
        
    def get_access_token(self):
        """접근 토큰 발급 (파일 공유 방식)"""
        import os

        token_file = '/tmp/kis_token.json'

        # 1. 기존 토큰 파일 확인 (다른 프로세스가 발급한 토큰)
        if os.path.exists(token_file):
            try:
                with open(token_file, 'r') as f:
                    token_data = json.load(f)

                # 토큰 유효 시간 체크 (발급 후 24시간)
                issued_at = token_data.get('issued_at', 0)
                if time.time() - issued_at < 86400:  # 24시간 = 86400초
                    self.access_token = token_data['token']
                    print("✅ 기존 토큰 재사용!")
                    return self.access_token
            except Exception as e:
                print(f"⚠️ 토큰 파일 읽기 실패: {e}")

        # 2. 새 토큰 발급
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

            # 3. 토큰 파일로 저장 (다른 프로세스와 공유)
            try:
                with open(token_file, 'w') as f:
                    json.dump({
                        'token': self.access_token,
                        'issued_at': time.time()
                    }, f)
                print("✅ 토큰 발급 성공!")
            except Exception as e:
                print(f"⚠️ 토큰 파일 저장 실패: {e}")

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
            result = res.json()
            rt_cd = result.get('rt_cd', '')
            msg1 = result.get('msg1', '')

            if rt_cd == '0':
                print(f"✅ 매수 주문 성공: {stock_code} {quantity}주")
                return result
            else:
                print(f"❌ 매수 주문 실패: {msg1}")
                return None
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
            result = res.json()
            rt_cd = result.get('rt_cd', '')
            msg1 = result.get('msg1', '')

            if rt_cd == '0':
                print(f"✅ 매도 주문 성공: {stock_code} {quantity}주")
                return result
            else:
                print(f"❌ 매도 주문 실패: {msg1}")
                return None
        else:
            print(f"❌ 매도 주문 실패:", res.text)
            return None

    # ==================== 해외주식 API ====================

    def get_overseas_current_price(self, ticker, exchange="NAS"):
        """해외주식 현재가 조회

        Args:
            ticker: 종목 심볼 (예: AAPL, TSLA)
            exchange: 거래소 코드 (NAS=나스닥, NYSE=뉴욕, AMS=아멕스)
        """
        url = f"{self.config.BASE_URL}/uapi/overseas-price/v1/quotations/price"

        headers = {
            "content-type": "application/json",
            "authorization": f"Bearer {self.access_token}",
            "appkey": self.config.APP_KEY,
            "appsecret": self.config.APP_SECRET,
            "tr_id": "HHDFS00000300"
        }

        params = {
            "AUTH": "",
            "EXCD": exchange,
            "SYMB": ticker
        }

        self._rate_limit()
        res = requests.get(url, headers=headers, params=params)

        if res.status_code == 200:
            output = res.json().get("output")
            if output:
                return output.get("last")  # 현재가
        else:
            print(f"❌ 해외주식 조회 실패: {res.text}")
        return None

    def get_overseas_balance(self, exchange="NASD", currency="USD"):
        """해외주식 잔고 조회

        Args:
            exchange: 거래소 코드 (NASD, NYSE, AMEX 등)
            currency: 통화 코드 (USD, HKD, JPY 등)
        """
        url = f"{self.config.BASE_URL}/uapi/overseas-stock/v1/trading/inquire-balance"

        headers = {
            "content-type": "application/json",
            "authorization": f"Bearer {self.access_token}",
            "appkey": self.config.APP_KEY,
            "appsecret": self.config.APP_SECRET,
            "tr_id": "VTTS3012R"  # 모의투자용
        }

        params = {
            "CANO": self.config.ACCOUNT_NO,
            "ACNT_PRDT_CD": "01",
            "OVRS_EXCG_CD": exchange,
            "TR_CRCY_CD": currency,
            "CTX_AREA_FK200": "",
            "CTX_AREA_NK200": ""
        }

        self._rate_limit()
        res = requests.get(url, headers=headers, params=params)

        if res.status_code == 200:
            return res.json()
        else:
            print("❌ 해외주식 잔고 조회 실패:", res.text)
            return None

    def buy_overseas_stock(self, ticker, quantity, exchange="NASD", price=0):
        """해외주식 매수

        Args:
            ticker: 종목 심볼 (예: AAPL)
            quantity: 수량
            exchange: 거래소 코드 (NASD=나스닥, NYSE=뉴욕, AMEX=아멕스)
            price: 가격 (0이면 현재가로 지정가 주문)
        """
        # 모의투자는 지정가만 가능 - price가 0이면 현재가 조회
        if price == 0:
            exchange_code = "NAS" if exchange == "NASD" else exchange.replace("AMEX", "AMS")
            current_price_str = self.get_overseas_current_price(ticker, exchange_code)
            if current_price_str:
                price = float(current_price_str)
                print(f"  📌 지정가 주문 (현재가): ${price:.2f}")
            else:
                print(f"  ❌ 현재가 조회 실패")
                return None

        url = f"{self.config.BASE_URL}/uapi/overseas-stock/v1/trading/order"

        headers = {
            "content-type": "application/json",
            "authorization": f"Bearer {self.access_token}",
            "appkey": self.config.APP_KEY,
            "appsecret": self.config.APP_SECRET,
            "tr_id": "VTTT1002U"  # 모의투자 매수
        }

        body = {
            "CANO": self.config.ACCOUNT_NO,
            "ACNT_PRDT_CD": "01",
            "OVRS_EXCG_CD": exchange,
            "PDNO": ticker,
            "ORD_QTY": str(quantity),
            "OVRS_ORD_UNPR": str(price),  # 지정가 필수
            "ORD_SVR_DVSN_CD": "0",
            "ORD_DVSN": "00"  # 00=지정가 (모의투자 필수)
        }

        self._rate_limit()
        res = requests.post(url, headers=headers, data=json.dumps(body))

        if res.status_code == 200:
            result = res.json()
            rt_cd = result.get('rt_cd', '')
            msg1 = result.get('msg1', '')

            if rt_cd == '0':
                print(f"✅ 해외주식 매수 주문 성공: {ticker} {quantity}주")
                return result
            else:
                print(f"❌ 해외주식 매수 주문 실패: {msg1}")
                return None
        else:
            print(f"❌ 해외주식 매수 주문 실패: {res.text}")
            return None

    def sell_overseas_stock(self, ticker, quantity, exchange="NASD", price=0):
        """해외주식 매도

        Args:
            ticker: 종목 심볼 (예: AAPL)
            quantity: 수량
            exchange: 거래소 코드 (NASD=나스닥, NYSE=뉴욕, AMEX=아멕스)
            price: 가격 (0이면 현재가로 지정가 주문)
        """
        # 모의투자는 지정가만 가능 - price가 0이면 현재가 조회
        if price == 0:
            exchange_code = "NAS" if exchange == "NASD" else exchange.replace("AMEX", "AMS")
            current_price_str = self.get_overseas_current_price(ticker, exchange_code)
            if current_price_str:
                price = float(current_price_str)
                print(f"  📌 지정가 주문 (현재가): ${price:.2f}")
            else:
                print(f"  ❌ 현재가 조회 실패")
                return None

        url = f"{self.config.BASE_URL}/uapi/overseas-stock/v1/trading/order"

        headers = {
            "content-type": "application/json",
            "authorization": f"Bearer {self.access_token}",
            "appkey": self.config.APP_KEY,
            "appsecret": self.config.APP_SECRET,
            "tr_id": "VTTT1001U"  # 모의투자 매도
        }

        body = {
            "CANO": self.config.ACCOUNT_NO,
            "ACNT_PRDT_CD": "01",
            "OVRS_EXCG_CD": exchange,
            "PDNO": ticker,
            "ORD_QTY": str(quantity),
            "OVRS_ORD_UNPR": str(price),  # 지정가 필수
            "ORD_SVR_DVSN_CD": "0",
            "ORD_DVSN": "00"  # 00=지정가 (모의투자 필수)
        }

        self._rate_limit()
        res = requests.post(url, headers=headers, data=json.dumps(body))

        if res.status_code == 200:
            result = res.json()
            rt_cd = result.get('rt_cd', '')
            msg1 = result.get('msg1', '')

            if rt_cd == '0':
                print(f"✅ 해외주식 매도 주문 성공: {ticker} {quantity}주")
                return result
            else:
                print(f"❌ 해외주식 매도 주문 실패: {msg1}")
                return None
        else:
            print(f"❌ 해외주식 매도 주문 실패: {res.text}")
            return None

    def get_overseas_ohlcv(self, ticker, exchange="NAS", period="D", count=100):
        """해외주식 OHLCV 데이터 조회

        Args:
            ticker: 종목 심볼
            exchange: 거래소 (NAS, NYSE, AMS)
            period: 기간 (D=일봉, W=주봉, M=월봉)
            count: 데이터 개수
        """
        url = f"{self.config.BASE_URL}/uapi/overseas-price/v1/quotations/dailyprice"

        headers = {
            "content-type": "application/json",
            "authorization": f"Bearer {self.access_token}",
            "appkey": self.config.APP_KEY,
            "appsecret": self.config.APP_SECRET,
            "tr_id": "HHDFS76240000"
        }

        params = {
            "AUTH": "",
            "EXCD": exchange,
            "SYMB": ticker,
            "GUBN": period,
            "BYMD": "",  # 조회 시작일 (공백이면 최근부터)
            "MODP": "1"   # 0=수정주가 미반영, 1=반영
        }

        self._rate_limit()
        res = requests.get(url, headers=headers, params=params)

        if res.status_code == 200:
            result = res.json()
            if 'output2' in result:
                import pandas as pd
                data = result['output2'][:count]

                # 데이터 파싱
                df = pd.DataFrame(data)
                df['date'] = pd.to_datetime(df['xymd'])
                df['open'] = df['open'].astype(float)
                df['high'] = df['high'].astype(float)
                df['low'] = df['low'].astype(float)
                df['close'] = df['clos'].astype(float)
                df['volume'] = df['tvol'].astype(float)

                # 최신 데이터가 위에 있으므로 역순 정렬
                df = df.iloc[::-1].reset_index(drop=True)

                return df[['date', 'open', 'high', 'low', 'close', 'volume']]
        else:
            print(f"❌ 해외주식 OHLCV 조회 실패: {res.text}")

        return None

    def get_investor_trading(self, stock_code):
        """기관/외인 매매 동향 조회

        Args:
            stock_code: 종목 코드

        Returns:
            dict: {
                'institution_net': 기관 순매수량,
                'foreign_net': 외인 순매수량,
                'individual_net': 개인 순매수량
            }
        """
        url = f"{self.config.BASE_URL}/uapi/domestic-stock/v1/quotations/inquire-investor"

        headers = {
            "content-type": "application/json",
            "authorization": f"Bearer {self.access_token}",
            "appkey": self.config.APP_KEY,
            "appsecret": self.config.APP_SECRET,
            "tr_id": "FHKST01010900"
        }

        params = {
            "fid_cond_mrkt_div_code": "J",
            "fid_input_iscd": stock_code
        }

        self._rate_limit()
        res = requests.get(url, headers=headers, params=params)

        if res.status_code == 200:
            result = res.json()

            if 'output' in result and len(result['output']) > 0:
                data = result['output'][0]  # 당일 데이터

                return {
                    'institution_net': int(data.get('stck_prpr', 0)),  # 기관 순매수
                    'foreign_net': int(data.get('frgn_ntby_qty', 0)),  # 외인 순매수
                    'individual_net': int(data.get('prsn_ntby_qty', 0))  # 개인 순매수
                }
        else:
            print(f"❌ 기관 매매 조회 실패: {res.text}")

        return None

    def get_minute_ohlcv(self, stock_code, time_end="153000"):
        """국내주식 분봉 데이터 조회 (당일만, 최대 30건)

        Args:
            stock_code: 종목 코드
            time_end: 조회 종료 시간 (HHMMss 형식, 예: "153000" = 15:30:00)
                     이 시간부터 거꾸로 30개 데이터 조회

        Returns:
            DataFrame: 분봉 데이터 (date, open, high, low, close, volume)
        """
        url = f"{self.config.BASE_URL}/uapi/domestic-stock/v1/quotations/inquire-time-itemchartprice"

        headers = {
            "content-type": "application/json",
            "authorization": f"Bearer {self.access_token}",
            "appkey": self.config.APP_KEY,
            "appsecret": self.config.APP_SECRET,
            "tr_id": "FHKST03010200"
        }

        params = {
            "fid_etc_cls_code": "",
            "fid_cond_mrkt_div_code": "J",
            "fid_input_iscd": stock_code,
            "fid_input_hour_1": time_end,  # 조회 종료 시간
            "fid_pw_data_incu_yn": "Y"     # 과거 데이터 포함 여부
        }

        self._rate_limit()
        res = requests.get(url, headers=headers, params=params)

        if res.status_code == 200:
            result = res.json()

            if 'output2' not in result:
                print(f"❌ 분봉 데이터 없음")
                return None

            data = result['output2']

            if not data or len(data) == 0:
                print(f"❌ 분봉 데이터가 비어있습니다")
                return None

            import pandas as pd
            df = pd.DataFrame(data)

            # 컬럼명 변환 및 타입 변환
            df['datetime'] = pd.to_datetime(df['stck_bsop_date'] + ' ' + df['stck_cntg_hour'], format='%Y%m%d %H%M%S')
            df['open'] = df['stck_oprc'].astype(int)
            df['high'] = df['stck_hgpr'].astype(int)
            df['low'] = df['stck_lwpr'].astype(int)
            df['close'] = df['stck_prpr'].astype(int)
            df['volume'] = df['cntg_vol'].astype(int)

            # 시간순 정렬 (과거 → 현재)
            df = df.sort_values('datetime').reset_index(drop=True)

            return df[['datetime', 'open', 'high', 'low', 'close', 'volume']]
        else:
            print("❌ 분봉 데이터 조회 실패:", res.text)
            return None
