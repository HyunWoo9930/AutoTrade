# sector_rotation.py
"""
섹터 로테이션 전략
- 11개 섹터의 상대 강도 분석
- 강세 섹터 우선 매수
- 약세 섹터 비중 축소
"""

from watchlist import WATCHLIST
from kis_api import KISApi
import pandas as pd


class SectorRotation:
    def __init__(self):
        self.api = KISApi()
        self.sector_scores = {}

    def calculate_sector_strength(self):
        """섹터별 강도 계산

        Returns:
            dict: {섹터명: 점수} (0~100점)
        """
        sector_scores = {}

        for sector, stocks in WATCHLIST.items():
            total_score = 0
            count = 0

            for stock_code, stock_name in stocks[:3]:  # 섹터 대표 3종목만
                try:
                    # 현재가 조회
                    current_price = int(self.api.get_current_price(stock_code))

                    # 일봉 데이터 조회
                    df = self._get_ohlcv(stock_code, count=20)

                    if df is None or len(df) < 20:
                        continue

                    # 5일 수익률
                    price_5d = df['close'].iloc[-5]
                    return_5d = (current_price - price_5d) / price_5d * 100

                    # 20일 수익률
                    price_20d = df['close'].iloc[0]
                    return_20d = (current_price - price_20d) / price_20d * 100

                    # 거래량 증가율
                    avg_volume = df['volume'].iloc[:15].mean()
                    recent_volume = df['volume'].iloc[-5:].mean()
                    volume_change = (recent_volume - avg_volume) / avg_volume * 100

                    # 점수 계산 (5일 60%, 20일 30%, 거래량 10%)
                    score = (
                        return_5d * 0.6 +
                        return_20d * 0.3 +
                        volume_change * 0.1
                    )

                    total_score += score
                    count += 1

                except Exception as e:
                    print(f"  ⚠️ {stock_name} 분석 실패: {e}")
                    continue

            if count > 0:
                avg_score = total_score / count
                # 0~100점으로 정규화 (평균 -10% ~ +10% 가정)
                normalized_score = max(0, min(100, (avg_score + 10) * 5))
                sector_scores[sector] = round(normalized_score, 1)
            else:
                sector_scores[sector] = 50.0  # 기본값

        # 점수 순 정렬
        sorted_sectors = dict(sorted(sector_scores.items(), key=lambda x: x[1], reverse=True))
        self.sector_scores = sorted_sectors

        return sorted_sectors

    def _get_ohlcv(self, stock_code, count=20):
        """일봉 데이터 조회 (간소화 버전)"""
        import requests

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
            "fid_period_div_code": "D"
        }

        self.api._rate_limit()
        res = requests.get(url, headers=headers, params=params)

        if res.status_code == 200:
            result = res.json()
            data = result.get('output', [])

            if data:
                df = pd.DataFrame(data)
                df = df.iloc[:count][::-1].reset_index(drop=True)
                df['close'] = df['stck_clpr'].astype(int)
                df['volume'] = df['acml_vol'].astype(int)
                return df[['close', 'volume']]

        return None

    def get_priority_sectors(self, top_n=3):
        """우선 투자 섹터 선정

        Args:
            top_n: 상위 N개 섹터 선택

        Returns:
            list: 강세 섹터 리스트
        """
        if not self.sector_scores:
            self.calculate_sector_strength()

        return list(self.sector_scores.keys())[:top_n]

    def should_avoid_sector(self, sector_name):
        """약세 섹터 체크

        Args:
            sector_name: 섹터명

        Returns:
            bool: True면 매수 회피 권장
        """
        if not self.sector_scores:
            self.calculate_sector_strength()

        # 하위 30% 섹터는 회피
        total_sectors = len(self.sector_scores)
        avoid_count = max(1, int(total_sectors * 0.3))

        weak_sectors = list(self.sector_scores.keys())[-avoid_count:]

        return sector_name in weak_sectors

    def print_sector_ranking(self):
        """섹터 순위 출력"""
        if not self.sector_scores:
            self.calculate_sector_strength()

        print("\n" + "=" * 60)
        print("📊 섹터 로테이션 분석")
        print("=" * 60)

        for i, (sector, score) in enumerate(self.sector_scores.items(), 1):
            if score >= 70:
                emoji = "🔥"
            elif score >= 50:
                emoji = "✅"
            elif score >= 30:
                emoji = "⚪"
            else:
                emoji = "❌"

            print(f"{i}. {emoji} {sector:15s} {score:5.1f}점")

        # 투자 권장 섹터
        top_sectors = self.get_priority_sectors(3)
        print(f"\n💡 투자 우선 섹터: {', '.join(top_sectors)}")

        # 회피 권장 섹터
        weak_sectors = list(self.sector_scores.keys())[-3:]
        print(f"⚠️  매수 회피 섹터: {', '.join(weak_sectors)}")
        print("=" * 60 + "\n")


if __name__ == "__main__":
    from kis_api import KISApi

    # API 초기화
    api = KISApi()
    api.get_access_token()

    # 섹터 분석 실행
    rotation = SectorRotation()
    rotation.calculate_sector_strength()
    rotation.print_sector_ranking()
