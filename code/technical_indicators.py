# technical_indicators.py
from kis_api import KISApi
import pandas as pd
import ta
import requests


class TechnicalAnalysis:
    def __init__(self):
        self.api = KISApi()
        self.api.get_access_token()

    def get_ohlcv(self, stock_code, period="D", count=30):
        """
        일봉 데이터 조회 (OHLCV)

        Args:
            stock_code: 종목코드
            period: 기간 (D: 일봉, W: 주봉, M: 월봉)
            count: 조회할 데이터 개수
        """
        url = f"{self.api.config.BASE_URL}/uapi/domestic-stock/v1/quotations/inquire-daily-price"

        headers = {
            "content-type": "application/json",
            "authorization": f"Bearer {self.api.access_token}",
            "appkey": self.api.config.APP_KEY,
            "appsecret": self.api.config.APP_SECRET,
            "tr_id": "FHKST01010400"
        }

        params = {
            "fid_cond_mrkt_div_code": "J",
            "fid_input_iscd": stock_code,
            "fid_org_adj_prc": "0",
            "fid_period_div_code": period
        }

        self.api._rate_limit()
        res = requests.get(url, headers=headers, params=params)  # 수정된 부분

        if res.status_code == 200:
            data = res.json()['output']

            # 최신 데이터가 먼저 오므로 역순으로 정렬
            df = pd.DataFrame(data)
            df = df.iloc[:count][::-1].reset_index(drop=True)

            # 컬럼명 변경 및 타입 변환
            df['date'] = pd.to_datetime(df['stck_bsop_date'])
            df['open'] = df['stck_oprc'].astype(int)
            df['high'] = df['stck_hgpr'].astype(int)
            df['low'] = df['stck_lwpr'].astype(int)
            df['close'] = df['stck_clpr'].astype(int)
            df['volume'] = df['acml_vol'].astype(int)

            return df[['date', 'open', 'high', 'low', 'close', 'volume']]
        else:
            print("❌ 데이터 조회 실패:", res.text)
            return None

    def calculate_indicators(self, stock_code):
        """
        기술적 지표 계산
        - 이동평균선 (5일, 20일, 60일)
        - RSI (14일)
        - MACD
        """
        print(f"\n{'=' * 60}")
        print(f"📊 기술적 지표 분석: {stock_code}")
        print(f"{'=' * 60}\n")

        # OHLCV 데이터 가져오기
        df = self.get_ohlcv(stock_code, count=100)

        if df is None or len(df) == 0:
            print("❌ 데이터를 가져올 수 없습니다.")
            return

        # 이동평균선 계산
        df['MA5'] = ta.trend.sma_indicator(df['close'], window=5)
        df['MA20'] = ta.trend.sma_indicator(df['close'], window=20)
        df['MA60'] = ta.trend.sma_indicator(df['close'], window=60)

        # RSI 계산
        df['RSI'] = ta.momentum.rsi(df['close'], window=14)

        # MACD 계산
        macd = ta.trend.MACD(df['close'])
        df['MACD'] = macd.macd()
        df['MACD_signal'] = macd.macd_signal()
        df['MACD_diff'] = macd.macd_diff()

        # 최근 데이터 출력
        latest = df.iloc[-1]

        print(f"📅 날짜: {latest['date'].strftime('%Y-%m-%d')}")
        print(f"💰 종가: {latest['close']:,}원\n")

        print("📈 이동평균선:")
        print(f"  - MA5:  {latest['MA5']:,.0f}원")
        print(f"  - MA20: {latest['MA20']:,.0f}원")
        print(f"  - MA60: {latest['MA60']:,.0f}원\n")

        print(f"📊 RSI(14): {latest['RSI']:.2f}")
        if latest['RSI'] >= 70:
            print("  → 과매수 구간 (매도 신호)")
        elif latest['RSI'] <= 30:
            print("  → 과매도 구간 (매수 신호)")
        else:
            print("  → 중립 구간")

        print(f"\n📉 MACD:")
        print(f"  - MACD: {latest['MACD']:.2f}")
        print(f"  - Signal: {latest['MACD_signal']:.2f}")
        print(f"  - Diff: {latest['MACD_diff']:.2f}")
        if latest['MACD_diff'] > 0:
            print("  → 골든크로스 (매수 신호)")
        else:
            print("  → 데드크로스 (매도 신호)")

        # 최근 5일 데이터 출력
        print(f"\n{'=' * 60}")
        print("📋 최근 5일 데이터")
        print(f"{'=' * 60}")
        print(df[['date', 'close', 'MA5', 'MA20', 'RSI']].tail())

        return df


if __name__ == "__main__":
    ta_analyzer = TechnicalAnalysis()

    # 삼성전자 기술적 지표 분석
    ta_analyzer.calculate_indicators("005930")