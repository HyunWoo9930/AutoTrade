# advanced_strategy.py
from kis_api import KISApi
from discord.discord_notifier import DiscordNotifier
import pandas as pd
import ta
import requests
from trading_journal import TradingJournal
import traceback  # 🔥 추가
import time

class AdvancedTradingStrategy:
    def __init__(self):
        self.api = KISApi()
        self.api.get_access_token()
        self.notifier = DiscordNotifier()
        self.journal = TradingJournal()
        self.current_buy_id = {}

    def get_ohlcv(self, stock_code, count=100):
        """일봉 데이터 조회"""
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

            # 디버깅: 응답 확인
            if 'output' not in result:
                print(f"❌ output 키가 없습니다: {result}")
                return None

            data = result['output']

            if not data or len(data) == 0:
                print(f"❌ 데이터가 비어있습니다")
                return None

            print(f"✅ {len(data)}개의 일봉 데이터 수신")

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

    def check_buy_signals(self, stock_code):
        """매수 신호 체크 (5개 지표)"""
        signals = 0
        signal_details = []

        # 기술적 지표 가져오기 (30개로 제한)
        df = self.get_ohlcv(stock_code, count=30)

        if df is None:
            return 0, ["❌ 데이터 조회 실패"]

        # 최소 20개 데이터 필요 (MA20 계산용)
        if len(df) < 20:
            return 0, [f"❌ 데이터 부족 (필요: 20개, 실제: {len(df)}개)"]

        print(f"✅ 데이터 수: {len(df)}개")

        # 이동평균 계산
        df['MA5'] = df['close'].rolling(5).mean()
        df['MA20'] = df['close'].rolling(20).mean()

        # RSI 계산
        df['RSI'] = ta.momentum.rsi(df['close'], window=14)

        # MACD 계산
        macd = ta.trend.MACD(df['close'])
        df['MACD'] = macd.macd()
        df['MACD_signal'] = macd.macd_signal()
        df['MACD_hist'] = macd.macd_diff()

        # 볼린저 밴드
        bb = ta.volatility.BollingerBands(df['close'])
        df['BB_upper'] = bb.bollinger_hband()
        df['BB_middle'] = bb.bollinger_mavg()
        df['BB_lower'] = bb.bollinger_lband()

        latest = df.iloc[-1]
        prev = df.iloc[-2]

        # 1. 추세 확인 (MA5 > MA20만 체크, MA60 제외)
        if pd.notna(latest['MA5']) and pd.notna(latest['MA20']):
            if latest['MA5'] > latest['MA20']:
                signals += 1
                signal_details.append(f"✅ 정배열 (MA5:{latest['MA5']:.0f} > MA20:{latest['MA20']:.0f})")
            else:
                signal_details.append(f"❌ 역배열 (MA5:{latest['MA5']:.0f} < MA20:{latest['MA20']:.0f})")
        else:
            signal_details.append("❌ 이동평균 계산 불가")

        # 2. RSI 확인
        if pd.notna(latest['RSI']) and pd.notna(prev['RSI']):
            if 30 < latest['RSI'] < 70 and latest['RSI'] > prev['RSI']:
                signals += 1
                signal_details.append(f"✅ RSI 적정+상승 ({latest['RSI']:.1f})")
            else:
                signal_details.append(f"❌ RSI 부적합 ({latest['RSI']:.1f}, 이전:{prev['RSI']:.1f})")
        else:
            signal_details.append("❌ RSI 계산 불가")

        # 3. MACD 골든크로스
        if pd.notna(latest['MACD']) and pd.notna(latest['MACD_signal']) and pd.notna(latest['MACD_hist']):
            if latest['MACD'] > latest['MACD_signal'] and latest['MACD_hist'] > 0:
                signals += 1
                signal_details.append("✅ MACD 골든크로스")
            else:
                signal_details.append(f"❌ MACD 약세 (MACD:{latest['MACD']:.1f}, Signal:{latest['MACD_signal']:.1f})")
        else:
            signal_details.append("❌ MACD 계산 불가")

        # 4. 거래량 확인
        avg_volume = df['volume'].tail(20).mean()
        if latest['volume'] > avg_volume * 1.2:
            signals += 1
            signal_details.append(f"✅ 거래량 급증 ({latest['volume'] / avg_volume:.1f}배)")
        else:
            signal_details.append(f"❌ 거래량 부족 ({latest['volume'] / avg_volume:.1f}배)")

        # 5. 볼린저 밴드 위치
        if pd.notna(latest['BB_lower']) and pd.notna(latest['BB_middle']) and pd.notna(latest['BB_upper']):
            bb_position = (latest['close'] - latest['BB_lower']) / (latest['BB_upper'] - latest['BB_lower']) * 100

            if latest['BB_lower'] < latest['close'] < latest['BB_middle']:
                signals += 1
                signal_details.append(f"✅ 볼린저 중하단 (위치:{bb_position:.0f}%)")
            elif latest['close'] < latest['BB_lower']:
                signals += 1
                signal_details.append(f"✅ 볼린저 하단 돌파 (과매도, 위치:{bb_position:.0f}%)")
            else:
                signal_details.append(f"❌ 볼린저 상단 (과매수, 위치:{bb_position:.0f}%)")
        else:
            signal_details.append("❌ 볼린저밴드 계산 불가")

        return signals, signal_details

    def calculate_position_size(self, stock_code, account_balance):
        """포지션 사이징 (ATR 기반)"""
        df = self.get_ohlcv(stock_code, count=30)
        if df is None or len(df) < 14:
            return 0, 0, 0

        # ATR 계산
        atr = ta.volatility.average_true_range(
            df['high'], df['low'], df['close'], window=14
        ).iloc[-1]

        current_price = int(self.api.get_current_price(stock_code))

        # 2% 리스크
        risk_amount = account_balance * 0.02
        stop_distance = atr * 2

        shares = int(risk_amount / stop_distance)

        # 한 종목 최대 10% 제한
        max_position = account_balance * 0.10
        max_shares = int(max_position / current_price)

        shares = min(shares, max_shares)

        return shares, current_price, atr

    def execute_strategy(self, stock_code, stock_name):
        """전략 실행"""
        print(f"\n{'=' * 60}")
        print(f"🎯 3단 로켓 전략 실행: {stock_name} ({stock_code})")
        print(f"{'=' * 60}\n")

        try:
            # 1단계: 매수 신호 확인
            signals, details = self.check_buy_signals(stock_code)

            print("📊 매수 신호 체크:")
            for detail in details:
                print(f"  {detail}")
            print(f"\n신호 점수: {signals}/5")

            # 현재가 조회
            current_price = int(self.api.get_current_price(stock_code))

            # 🔔 강한 신호면 디스코드 알림
            if signals >= 4:
                self.notifier.notify_signal_strong(
                    stock_name, stock_code, signals, details, current_price
                )
            elif signals == 3:
                self.notifier.notify_signal_weak(stock_name, stock_code, signals)

            # 2단계: 잔고 확인
            balance = self.api.get_balance()
            cash = 0
            holding_qty = 0
            profit_rate = 0

            if balance and 'output2' in balance:
                cash = int(balance['output2'][0]['dnca_tot_amt'])

            if balance and 'output1' in balance:
                for stock in balance['output1']:
                    if stock.get('pdno') == stock_code and int(stock.get('hldg_qty', 0)) > 0:
                        holding_qty = int(stock.get('hldg_qty', 0))
                        profit_rate = float(stock.get('evlu_pfls_rt', 0))
                        break

            print(f"\n💰 계좌 상태:")
            print(f"  예수금: {cash:,}원")
            print(f"  보유수량: {holding_qty}주")
            if holding_qty > 0:
                print(f"  수익률: {profit_rate}%")

                # 🔔 보유 현황 알림 (±5% 이상일 때만)
                if abs(profit_rate) >= 5:
                    self.notifier.notify_holding(
                        stock_name, stock_code, holding_qty, profit_rate
                    )

            # 3단계: 매매 결정
            if holding_qty > 0:
                self._manage_position(stock_code, stock_name, holding_qty, profit_rate)
            else:
                if signals >= 4:
                    self._execute_buy(stock_code, stock_name, cash, signals)
                elif signals >= 3:
                    print(f"\n⚠️ 보통 신호 (3/5) - 신중한 매수 고려")
                else:
                    print(f"\n❌ 매수 신호 부족 ({signals}/5) - 대기")

        except Exception as e:
            # 🔔 에러 알림
            error_msg = str(e)
            error_trace = traceback.format_exc()

            print(f"\n❌ 에러 발생: {error_msg}")
            print(error_trace)

            self.notifier.notify_error(
                location=f"{stock_name} ({stock_code})",
                error=error_msg
            )

            # 에러는 기록하되 프로그램은 계속 진행
            pass

    def _execute_buy(self, stock_code, stock_name, cash, signals):
        """매수 실행"""
        print(f"\n🎯 강한 매수 신호! ({signals}/5)")

        total_balance = cash + 30000000
        shares, current_price, atr = self.calculate_position_size(stock_code, total_balance)

        if shares == 0:
            print("❌ 매수 가능 수량 없음")
            return

        position_value = shares * current_price

        print(f"\n📋 매수 계획:")
        print(f"  목표 수량: {shares}주")
        print(f"  현재가: {current_price:,}원")
        print(f"  투자금액: {position_value:,}원")
        print(f"  ATR: {atr:,.0f}원")
        print(f"  손절가: {current_price - int(atr * 2):,}원 (-{atr * 2 / current_price * 100:.1f}%)")

        first_buy = int(shares * 0.4)

        if first_buy > 0:
            print(f"\n💰 1차 매수 실행: {first_buy}주")
            result = self.api.buy_stock(stock_code, first_buy)

            if result:
                print("✅ 매수 성공!")

                # 📝 일지 기록
                strategy_note = f"신호 {signals}/5 | 손절가: {current_price - int(atr * 2):,}원"
                buy_id = self.journal.log_buy(
                    stock_code=stock_code,
                    stock_name=stock_name,
                    quantity=first_buy,
                    price=current_price,
                    signals=signals,
                    strategy_note=strategy_note
                )
                self.current_buy_id[stock_code] = buy_id

                # 디스코드 알림
                self.notifier.notify_buy(stock_name, stock_code, first_buy, current_price)
                self.notifier.notify_strategy(
                    f"{stock_name} 매수 전략",
                    f"신호: {signals}/5\n"
                    f"수량: {first_buy}주 (40% 분할)\n"
                    f"손절가: {current_price - int(atr * 2):,}원"
                )

    def _manage_position(self, stock_code, stock_name, quantity, profit_rate):
        """포지션 관리 (익절/손절)"""
        print(f"\n📊 포지션 관리 중...")

        current_price = int(self.api.get_current_price(stock_code))

        # 손절: -5% 이하
        if profit_rate <= -5.0:
            print(f"\n🚨 손절 라인! ({profit_rate}% <= -5%)")
            result = self.api.sell_stock(stock_code, quantity)
            if result:
                print("✅ 손절 매도 완료")

                # 📝 일지 기록
                buy_id = self.current_buy_id.get(stock_code)
                if buy_id:
                    self.journal.log_sell(
                        buy_id=buy_id,
                        stock_code=stock_code,
                        stock_name=stock_name,
                        quantity=quantity,
                        price=current_price,
                        profit_rate=profit_rate,
                        sell_reason="손절 (-5% 도달)"
                    )
                    del self.current_buy_id[stock_code]

                self.notifier.notify_sell(stock_name, stock_code, quantity, current_price, profit_rate)

        # 1차 익절: +10% (50% 매도)
        elif profit_rate >= 10.0 and quantity > 1:
            sell_qty = int(quantity * 0.5)
            print(f"\n🎯 1차 익절! (+10%) - {sell_qty}주 매도")
            result = self.api.sell_stock(stock_code, sell_qty)
            if result:
                print("✅ 부분 익절 완료")

                # 📝 일지 기록
                buy_id = self.current_buy_id.get(stock_code)
                if buy_id:
                    self.journal.log_sell(
                        buy_id=buy_id,
                        stock_code=stock_code,
                        stock_name=stock_name,
                        quantity=sell_qty,
                        price=current_price,
                        profit_rate=profit_rate,
                        sell_reason="1차 익절 (+10% 달성)"
                    )

                self.notifier.notify_sell(stock_name, stock_code, sell_qty, current_price, profit_rate)

        # 2차 익절: +20% (전량 매도)
        elif profit_rate >= 20.0:
            print(f"\n🚀 2차 익절! (+20%) - 전량 매도")
            result = self.api.sell_stock(stock_code, quantity)
            if result:
                print("✅ 익절 매도 완료")

                # 📝 일지 기록
                buy_id = self.current_buy_id.get(stock_code)
                if buy_id:
                    self.journal.log_sell(
                        buy_id=buy_id,
                        stock_code=stock_code,
                        stock_name=stock_name,
                        quantity=quantity,
                        price=current_price,
                        profit_rate=profit_rate,
                        sell_reason="2차 익절 (+20% 달성)"
                    )
                    del self.current_buy_id[stock_code]

                self.notifier.notify_sell(stock_name, stock_code, quantity, current_price, profit_rate)

        else:
            print(f"\n⏳ 홀딩 중 (수익률: {profit_rate}%)")
            print(f"  목표: +10% (1차 익절), +20% (2차 익절)")
            print(f"  손절: -5%")


# advanced_strategy.py 마지막 부분
if __name__ == "__main__":
    from watchlist import get_all_stocks

    strategy = AdvancedTradingStrategy()

    watchlist = get_all_stocks()

    for code, name in watchlist:
        strategy.execute_strategy(code, name)
        print("\n" + "-" * 60 + "\n")