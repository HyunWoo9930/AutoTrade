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
        self.pyramid_tracker = {}  # 분할 매수 추적 {stock_code: {'first_buy': qty, 'avg_price': price, 'target_qty': total}}

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

    def detect_market_regime(self, stock_code):
        """시장 상태 감지: trending, sideways, crash"""
        df = self.get_ohlcv(stock_code, count=30)
        if df is None or len(df) < 20:
            return "unknown", {}

        # ADX (Average Directional Index) 계산 - 추세 강도 측정
        adx_indicator = ta.trend.ADXIndicator(df['high'], df['low'], df['close'], window=14)
        df['ADX'] = adx_indicator.adx()

        # ATR 계산
        df['ATR'] = ta.volatility.average_true_range(df['high'], df['low'], df['close'], window=14)

        # 이동평균 계산
        df['MA5'] = df['close'].rolling(5).mean()
        df['MA20'] = df['close'].rolling(20).mean()

        latest = df.iloc[-1]
        prev_5 = df.iloc[-5:] if len(df) >= 5 else df

        # 최근 5일 가격 변화율 (일봉 종가 기준)
        price_change_5d = (latest['close'] - prev_5['close'].iloc[0]) / prev_5['close'].iloc[0] * 100

        # 🆕 장중 현재가 기반 변화율 추가 (실시간 급락 감지)
        try:
            current_price = int(self.api.get_current_price(stock_code))
            # 전날 종가 대비 오늘 현재가 변화율
            intraday_change = (current_price - latest['close']) / latest['close'] * 100
        except:
            current_price = latest['close']
            intraday_change = 0

        # 변동성 계산 (최근 20일 표준편차)
        volatility = df['close'].tail(20).std() / df['close'].tail(20).mean() * 100

        regime_info = {
            'adx': latest['ADX'],
            'atr': latest['ATR'],
            'price_change_5d': price_change_5d,
            'intraday_change': intraday_change,  # 🆕 장중 변화율
            'current_price': current_price,  # 🆕 현재가
            'volatility': volatility,
            'ma5': latest['MA5'],
            'ma20': latest['MA20']
        }

        # 🚨 급락장 감지: 5일간 -10% 이상 하락 또는 (하락 + 고변동성)
        # 수정: 급등(+수익률)은 제외, 하락만 급락으로 판단
        if price_change_5d < -10:
            return "crash", regime_info

        # 하락 + 고변동성 동시 충족 시에만 급락장
        if price_change_5d < 0 and volatility > 10:
            return "crash", regime_info

        # 🆕 장중 급락 감지: 전날 종가 대비 -5% 이상 급락
        if intraday_change < -5:
            return "crash", regime_info

        # 📊 횡보장 감지: ADX < 25 (약한 추세) + MA5와 MA20 근접
        if pd.notna(latest['ADX']) and latest['ADX'] < 25:
            ma_diff = abs(latest['MA5'] - latest['MA20']) / latest['MA20'] * 100
            if ma_diff < 2:  # MA 간격이 2% 이내
                return "sideways", regime_info

        # 📈 추세장 감지: ADX >= 25 (강한 추세)
        if pd.notna(latest['ADX']) and latest['ADX'] >= 25:
            return "trending", regime_info

        return "unknown", regime_info

    def calculate_position_size(self, stock_code, account_balance, regime="unknown"):
        """포지션 사이징 (손절 퍼센트 기준)"""
        df = self.get_ohlcv(stock_code, count=30)
        if df is None or len(df) < 14:
            return 0, 0, 0

        # ATR 계산 (참고용)
        atr = ta.volatility.average_true_range(
            df['high'], df['low'], df['close'], window=14
        ).iloc[-1]

        current_price = int(self.api.get_current_price(stock_code))

        # 손절 퍼센트 결정 (급락장: -3%, 평상시: -5%)
        stop_loss_pct = 0.03 if regime == "crash" else 0.05

        # 2% 리스크 기준으로 수량 계산
        risk_amount = account_balance * 0.02
        stop_loss_amount = current_price * stop_loss_pct
        shares = int(risk_amount / stop_loss_amount)

        # 횡보장일 때는 포지션 크기 50% 축소
        if regime == "sideways":
            shares = int(shares * 0.5)

        # 한 종목 최대 10% 제한 (횡보장: 5%)
        max_position_pct = 0.05 if regime == "sideways" else 0.10
        max_position = account_balance * max_position_pct
        max_shares = int(max_position / current_price)

        shares = min(shares, max_shares)

        return shares, current_price, atr

    def execute_strategy(self, stock_code, stock_name):
        """전략 실행"""
        print(f"\n{'=' * 60}")
        print(f"🎯 3단 로켓 전략 실행: {stock_name} ({stock_code})")
        print(f"{'=' * 60}\n")

        try:
            # 0단계: 시장 상태 감지
            regime, regime_info = self.detect_market_regime(stock_code)
            print(f"🌐 시장 상태: {regime.upper()}")
            if regime_info:
                print(f"  ADX: {regime_info.get('adx', 0):.1f}")
                print(f"  5일 변화율: {regime_info.get('price_change_5d', 0):.2f}%")
                print(f"  장중 변화율: {regime_info.get('intraday_change', 0):.2f}%")  # 🆕
                print(f"  변동성: {regime_info.get('volatility', 0):.2f}%\n")

                # 급락장이나 횡보장 감지 시 디스코드 알림
                if regime in ["crash", "sideways"]:
                    self.notifier.notify_market_regime(stock_name, stock_code, regime, regime_info)

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

            # 3단계: 매매 결정 (시장 상태에 따라 분기)
            if holding_qty > 0:
                self._manage_position(stock_code, stock_name, holding_qty, profit_rate, regime)
            else:
                # 🚨 급락장: 신호가 강해도 매수 금지
                if regime == "crash":
                    print(f"\n🚨 급락장 감지! 매수 금지 (변동성 {regime_info.get('volatility', 0):.2f}%)")
                    return

                # 📊 횡보장: 신호 3개 이상 매수 (단, 포지션 크기 50% 축소)
                elif regime == "sideways":
                    if signals >= 3:
                        print(f"\n📊 횡보장 - 신호 확인! ({signals}/5)")
                        print(f"  ⚠️ 횡보장이므로 포지션 크기 50% 축소")
                        self._execute_buy(stock_code, stock_name, cash, signals, regime)
                    else:
                        print(f"\n❌ 횡보장 - 신호 부족 ({signals}/5, 필요: 3+) - 대기")

                # 📈 추세장: 기존 전략 (3개 이상 매수)
                elif regime == "trending":
                    if signals >= 3:
                        self._execute_buy(stock_code, stock_name, cash, signals, regime)
                    else:
                        print(f"\n❌ 매수 신호 부족 ({signals}/5) - 대기")

                # ❓ 알 수 없음: 보수적 (4개 이상만)
                else:
                    if signals >= 4:
                        self._execute_buy(stock_code, stock_name, cash, signals, regime)
                    else:
                        print(f"\n❌ 시장 상태 불명확 - 신호 부족 ({signals}/5, 필요: 4+) - 대기")

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

    def _execute_buy(self, stock_code, stock_name, cash, signals, regime="unknown"):
        """매수 실행 (분할 매수)"""
        print(f"\n🎯 강한 매수 신호! ({signals}/5)")

        total_balance = cash + 30000000
        shares, current_price, atr = self.calculate_position_size(stock_code, total_balance, regime)

        if shares == 0:
            print("❌ 매수 가능 수량 없음")
            return

        position_value = shares * current_price

        # 손절 퍼센트 결정
        stop_loss_pct = 0.03 if regime == "crash" else 0.05
        stop_loss_price = int(current_price * (1 - stop_loss_pct))

        print(f"\n📋 매수 계획:")
        print(f"  목표 수량: {shares}주")
        print(f"  현재가: {current_price:,}원")
        print(f"  투자금액: {position_value:,}원")
        print(f"  ATR: {atr:,.0f}원 (참고)")
        print(f"  손절가: {stop_loss_price:,}원 (-{stop_loss_pct*100:.0f}%)")

        first_buy = int(shares * 0.4)

        if first_buy > 0:
            print(f"\n💰 1차 매수 실행: {first_buy}주 (40%)")
            result = self.api.buy_stock(stock_code, first_buy)

            if result:
                print("✅ 매수 성공!")

                # 피라미드 매수 추적 정보 저장
                self.pyramid_tracker[stock_code] = {
                    'first_buy_qty': first_buy,
                    'first_buy_price': current_price,
                    'target_qty': shares,
                    'remaining_qty': shares - first_buy,
                    'stop_loss': stop_loss_price,
                    'stop_loss_pct': stop_loss_pct,
                    'atr': atr,
                    'regime': regime
                }

                # 📝 일지 기록
                strategy_note = f"신호 {signals}/5 | 시장: {regime} | 손절가: {stop_loss_price:,}원 (-{stop_loss_pct*100:.0f}%) | 분할: 1/2"
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
                regime_emoji = {"trending": "📈", "sideways": "📊", "crash": "🚨"}.get(regime, "❓")
                self.notifier.notify_strategy(
                    f"{stock_name} 매수 전략 (1차)",
                    f"신호: {signals}/5\n"
                    f"시장 상태: {regime_emoji} {regime}\n"
                    f"수량: {first_buy}주 (40% 분할)\n"
                    f"목표: {shares}주 (2차 추가매수 대기)\n"
                    f"손절가: {stop_loss_price:,}원 (-{stop_loss_pct*100:.0f}%)"
                )
            else:
                # 매수 실패 알림
                self.notifier.notify_buy_failed(stock_name, stock_code, "주문 실패 (장 마감 또는 예수금 부족)")

    def _manage_position(self, stock_code, stock_name, quantity, profit_rate, regime="unknown"):
        """포지션 관리 (익절/손절/추가매수)"""
        print(f"\n📊 포지션 관리 중...")

        current_price = int(self.api.get_current_price(stock_code))

        # 🚨 급락장 감지 시 강제 청산
        if regime == "crash":
            print(f"\n🚨 급락장 감지! 보유 포지션 긴급 청산")
            result = self.api.sell_stock(stock_code, quantity)
            if result:
                print("✅ 긴급 청산 완료")

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
                        sell_reason="🚨 급락장 긴급 청산"
                    )
                    del self.current_buy_id[stock_code]

                # 피라미드 추적 삭제
                if stock_code in self.pyramid_tracker:
                    del self.pyramid_tracker[stock_code]

                # 급락장 긴급 청산 전용 알림
                self.notifier.notify_crash_protection(stock_name, stock_code, quantity, current_price, profit_rate)
            else:
                self.notifier.notify_sell_failed(stock_name, stock_code, "긴급 청산 주문 실패")
            return

        # 📈 피라미드 매수 체크 (2차 추가 매수)
        if stock_code in self.pyramid_tracker:
            tracker = self.pyramid_tracker[stock_code]
            first_price = tracker['first_buy_price']
            remaining_qty = tracker['remaining_qty']

            # 조건: +3% 이상 수익이면 언제든 추가 매수 가능 (범위 제한 제거)
            if profit_rate >= 3.0 and remaining_qty > 0:
                print(f"\n📈 피라미드 매수 조건 충족! (수익률 {profit_rate:.2f}%)")

                # 추가 신호 확인 (간단 체크)
                signals, _ = self.check_buy_signals(stock_code)
                if signals >= 3:
                    second_buy = int(remaining_qty)
                    print(f"💰 2차 추가 매수 실행: {second_buy}주 (60%)")

                    result = self.api.buy_stock(stock_code, second_buy)
                    if result:
                        print("✅ 추가 매수 성공!")

                        # 일지 업데이트
                        buy_id = self.current_buy_id.get(stock_code)
                        if buy_id:
                            strategy_note = f"2차 추가매수 | 신호 {signals}/5 | 평균단가 조정"
                            self.journal.log_buy(
                                stock_code=stock_code,
                                stock_name=stock_name,
                                quantity=second_buy,
                                price=current_price,
                                signals=signals,
                                strategy_note=strategy_note
                            )

                        # 피라미드 추적 완료 처리
                        del self.pyramid_tracker[stock_code]

                        # 디스코드 알림 (피라미드 전용)
                        self.notifier.notify_pyramid_buy(stock_name, stock_code, second_buy, current_price, phase="2차")
                    else:
                        self.notifier.notify_buy_failed(stock_name, stock_code, "2차 추가매수 실패")

                else:
                    print(f"⚠️ 추가 매수 보류 - 신호 약화 ({signals}/5)")

        # 손절: -5% 이하 (또는 급락장 손절 강화)
        stop_loss_threshold = -5.0
        if regime == "crash":
            stop_loss_threshold = -3.0  # 급락장에서는 손절 라인 강화

        if profit_rate <= stop_loss_threshold:
            print(f"\n🚨 손절 라인! ({profit_rate}% <= {stop_loss_threshold}%)")
            result = self.api.sell_stock(stock_code, quantity)
            if result:
                print("✅ 손절 매도 완료")

                # 📝 일지 기록
                buy_id = self.current_buy_id.get(stock_code)
                if buy_id:
                    sell_reason = f"손절 ({stop_loss_threshold}% 도달)"
                    if regime == "crash":
                        sell_reason = "🚨 급락장 강화 손절 (-3% 도달)"

                    self.journal.log_sell(
                        buy_id=buy_id,
                        stock_code=stock_code,
                        stock_name=stock_name,
                        quantity=quantity,
                        price=current_price,
                        profit_rate=profit_rate,
                        sell_reason=sell_reason
                    )
                    del self.current_buy_id[stock_code]

                # 피라미드 추적 삭제
                if stock_code in self.pyramid_tracker:
                    del self.pyramid_tracker[stock_code]

                self.notifier.notify_sell(stock_name, stock_code, quantity, current_price, profit_rate)
            else:
                # 매도 실패 알림
                self.notifier.notify_sell_failed(stock_name, stock_code, "손절 주문 실패")

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
            else:
                # 매도 실패 알림
                self.notifier.notify_sell_failed(stock_name, stock_code, "1차 익절 주문 실패")

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

                # 피라미드 추적 삭제
                if stock_code in self.pyramid_tracker:
                    del self.pyramid_tracker[stock_code]

                self.notifier.notify_sell(stock_name, stock_code, quantity, current_price, profit_rate)
            else:
                # 매도 실패 알림
                self.notifier.notify_sell_failed(stock_name, stock_code, "2차 익절 주문 실패")

        else:
            print(f"\n⏳ 홀딩 중 (수익률: {profit_rate}%)")
            print(f"  목표: +10% (1차 익절), +20% (2차 익절)")
            print(f"  손절: {stop_loss_threshold}%")

            # 피라미드 매수 대기 중인 경우 상태 표시
            if stock_code in self.pyramid_tracker:
                tracker = self.pyramid_tracker[stock_code]
                print(f"  📈 2차 추가매수 대기: {tracker['remaining_qty']}주 (조건: +3~5% 구간)")


# advanced_strategy.py 마지막 부분
if __name__ == "__main__":
    from watchlist import get_all_stocks

    strategy = AdvancedTradingStrategy()

    watchlist = get_all_stocks()

    for code, name in watchlist:
        strategy.execute_strategy(code, name)
        print("\n" + "-" * 60 + "\n")