# overseas_strategy.py
"""
해외주식(미국 주식) 트레이딩 전략
- 국내주식 advanced_strategy.py와 동일한 로직 적용
- 9가지 고급 전략 모두 포함
"""
from kis_api import KISApi
from discord.discord_notifier import DiscordNotifier
import pandas as pd
import ta
import traceback
import time

class OverseasTradingStrategy:
    def __init__(self):
        self.api = KISApi()
        self.api.get_access_token()
        self.notifier = DiscordNotifier()
        self.current_buy_id = {}
        self.pyramid_tracker = {}
        self.max_holdings = 15  # 공격적 설정 (해외주식)
        self.sold_today = self._load_sold_today()  # ✅ 영구 저장
        self.peak_profit = {}

    def _load_sold_today(self):
        """당일 익절 종목 로드 (영구 저장)"""
        import os, json
        from datetime import datetime
        sold_file = '/app/data/sold_today_overseas.json'
        try:
            if os.path.exists(sold_file):
                with open(sold_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    today = datetime.now().strftime('%Y-%m-%d')
                    if data.get('date') == today:
                        return data.get('stocks', {})
        except Exception as e:
            print(f"⚠️ sold_today 로드 실패: {e}")
        return {}

    def _save_sold_today(self):
        """당일 익절 종목 저장 (영구 저장)"""
        import os, json
        from datetime import datetime
        sold_file = '/app/data/sold_today_overseas.json'
        try:
            os.makedirs(os.path.dirname(sold_file), exist_ok=True)
            today = datetime.now().strftime('%Y-%m-%d')
            data = {'date': today, 'stocks': self.sold_today}
            with open(sold_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️ sold_today 저장 실패: {e}")

    def _convert_exchange_code(self, exchange):
        """거래소 코드 변환 (NAS→NASD, NYSE→NYSE, AMS→AMEX)"""
        mapping = {
            "NAS": "NASD",
            "NYSE": "NYSE",
            "AMS": "AMEX"
        }
        return mapping.get(exchange, exchange)

    def get_current_holdings_count(self):
        """현재 보유 해외주식 수 조회"""
        try:
            balance = self.api.get_overseas_balance()
            if balance and 'output1' in balance:
                if isinstance(balance['output1'], list):
                    holdings = [s for s in balance['output1'] if float(s.get('ovrs_cblc_qty', 0)) > 0]
                    return len(holdings)
        except Exception as e:
            print(f"⚠️ 보유 종목 수 조회 실패: {e}")
        return 0

    def get_sector_exposure(self, sector_name, account_balance):
        """특정 섹터의 현재 노출도 계산"""
        try:
            from watchlist_us import WATCHLIST_US
            sector_stocks = WATCHLIST_US.get(sector_name, [])
            sector_tickers = [ticker for ticker, name, exchange in sector_stocks]

            balance = self.api.get_overseas_balance()
            if not balance or 'output1' not in balance:
                return 0.0

            if not isinstance(balance['output1'], list):
                return 0.0

            total_sector_value = 0
            for stock in balance['output1']:
                ticker = stock.get('ovrs_pdno')
                if ticker in sector_tickers:
                    qty = float(stock.get('ovrs_cblc_qty', 0))
                    price = float(stock.get('now_pric2', 0))
                    total_sector_value += qty * price

            return total_sector_value / account_balance if account_balance > 0 else 0.0
        except Exception as e:
            print(f"⚠️ 섹터 노출도 조회 실패: {e}")
            return 0.0

    def get_stock_sector(self, ticker):
        """종목 티커로 섹터 찾기"""
        try:
            from watchlist_us import WATCHLIST_US
            for sector, stocks in WATCHLIST_US.items():
                for t, name, exchange in stocks:
                    if t == ticker:
                        return sector
        except:
            pass
        return None

    def get_ohlcv(self, ticker, exchange="NAS", count=100):
        """일봉 데이터 조회 (해외주식)"""
        df = self.api.get_overseas_ohlcv(ticker, exchange, "D", count)
        if df is not None and len(df) > 0:
            print(f"✅ {len(df)}개의 일봉 데이터 수신 ({ticker})")
        return df

    def check_buy_signals(self, ticker, exchange="NAS"):
        """매수 신호 체크 (가중치 적용)"""
        WEIGHTS = {
            'MA': 2.0,
            'RSI': 1.0,
            'MACD': 1.5,
            'Volume': 1.5,
            'BB': 1.0
        }
        MAX_WEIGHTED_SCORE = sum(WEIGHTS.values())

        weighted_score = 0.0
        signal_details = []

        df = self.get_ohlcv(ticker, exchange, count=30)

        if df is None or len(df) < 20:
            return 0, ["❌ 데이터 부족"]

        # 이동평균
        df['MA5'] = df['close'].rolling(5).mean()
        df['MA20'] = df['close'].rolling(20).mean()

        # RSI
        df['RSI'] = ta.momentum.rsi(df['close'], window=14)

        # MACD
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

        # 1. MA 체크
        if pd.notna(latest['MA5']) and pd.notna(latest['MA20']):
            if latest['MA5'] > latest['MA20']:
                weighted_score += WEIGHTS['MA']
                signal_details.append(f"✅ 정배열 [+{WEIGHTS['MA']}]")
            else:
                signal_details.append(f"❌ 역배열")

        # 2. RSI
        if pd.notna(latest['RSI']) and pd.notna(prev['RSI']):
            if 30 < latest['RSI'] < 70 and latest['RSI'] > prev['RSI']:
                weighted_score += WEIGHTS['RSI']
                signal_details.append(f"✅ RSI 적정 ({latest['RSI']:.1f}) [+{WEIGHTS['RSI']}]")
            else:
                signal_details.append(f"❌ RSI ({latest['RSI']:.1f})")

        # 3. MACD
        if pd.notna(latest['MACD']) and pd.notna(latest['MACD_signal']):
            if latest['MACD'] > latest['MACD_signal'] and latest['MACD_hist'] > 0:
                weighted_score += WEIGHTS['MACD']
                signal_details.append(f"✅ MACD 골든크로스 [+{WEIGHTS['MACD']}]")
            else:
                signal_details.append(f"❌ MACD 약세")

        # 4. 거래량
        avg_volume = df['volume'].tail(20).mean()
        if latest['volume'] > avg_volume * 1.2:
            weighted_score += WEIGHTS['Volume']
            signal_details.append(f"✅ 거래량 급증 [+{WEIGHTS['Volume']}]")
        else:
            signal_details.append(f"❌ 거래량 부족")

        # 5. 볼린저 밴드
        if pd.notna(latest['BB_lower']) and pd.notna(latest['BB_middle']):
            if latest['BB_lower'] < latest['close'] < latest['BB_middle']:
                weighted_score += WEIGHTS['BB']
                signal_details.append(f"✅ 볼린저 중하단 [+{WEIGHTS['BB']}]")
            elif latest['close'] < latest['BB_lower']:
                weighted_score += WEIGHTS['BB']
                signal_details.append(f"✅ 볼린저 하단 돌파 [+{WEIGHTS['BB']}]")
            else:
                signal_details.append(f"❌ 볼린저 상단")

        # 정규화
        normalized_score = (weighted_score / MAX_WEIGHTED_SCORE) * 5.0
        signals = int(round(normalized_score))

        signal_details.append(f"\n📊 총점: {weighted_score:.1f}/{MAX_WEIGHTED_SCORE} → 신호: {signals}/5")

        return signals, signal_details

    def detect_market_regime(self, ticker, exchange="NAS"):
        """시장 상태 감지"""
        df = self.get_ohlcv(ticker, exchange, count=30)
        if df is None or len(df) < 20:
            return "unknown", {}

        # ADX
        adx_indicator = ta.trend.ADXIndicator(df['high'], df['low'], df['close'], window=14)
        df['ADX'] = adx_indicator.adx()

        # ATR
        df['ATR'] = ta.volatility.average_true_range(df['high'], df['low'], df['close'], window=14)

        df['MA5'] = df['close'].rolling(5).mean()
        df['MA20'] = df['close'].rolling(20).mean()

        latest = df.iloc[-1]
        prev_5 = df.iloc[-5:] if len(df) >= 5 else df

        price_change_5d = (latest['close'] - prev_5['close'].iloc[0]) / prev_5['close'].iloc[0] * 100

        try:
            current_price = float(self.api.get_overseas_current_price(ticker, exchange))
            intraday_change = (current_price - latest['close']) / latest['close'] * 100
        except:
            current_price = latest['close']
            intraday_change = 0

        volatility = df['close'].tail(20).std() / df['close'].tail(20).mean() * 100

        regime_info = {
            'adx': latest['ADX'],
            'atr': latest['ATR'],
            'price_change_5d': price_change_5d,
            'intraday_change': intraday_change,
            'current_price': current_price,
            'volatility': volatility,
            'ma5': latest['MA5'],
            'ma20': latest['MA20']
        }

        # 급락장 감지
        if price_change_5d < -10:
            return "crash", regime_info

        if price_change_5d < 0 and volatility > 10:
            return "crash", regime_info

        if intraday_change < -5:
            return "crash", regime_info

        # 횡보장
        if pd.notna(latest['ADX']) and latest['ADX'] < 25:
            ma_diff = abs(latest['MA5'] - latest['MA20']) / latest['MA20'] * 100
            if ma_diff < 2:
                return "sideways", regime_info

        # 추세장
        if pd.notna(latest['ADX']) and latest['ADX'] >= 25:
            return "trending", regime_info

        return "unknown", regime_info

    def calculate_position_size(self, ticker, exchange, account_balance, regime="unknown"):
        """✅ 포지션 사이징 (변동성 기반 + ATR 동적 목표가)"""
        df = self.get_ohlcv(ticker, exchange, count=30)
        if df is None or len(df) < 14:
            return 0, 0, 0, 0.05, 12.0, 20.0  # ✅ 기본 목표가 추가

        atr = ta.volatility.average_true_range(
            df['high'], df['low'], df['close'], window=14
        ).iloc[-1]

        current_price = float(self.api.get_overseas_current_price(ticker, exchange))

        # 변동성 기반 손절
        atr_pct = (atr / current_price) * 100
        base_stop_loss_pct = 0.03 if regime == "crash" else 0.05

        if atr_pct < 2.0:
            adjusted_stop_loss_pct = base_stop_loss_pct * 0.8
        elif atr_pct > 5.0:
            adjusted_stop_loss_pct = base_stop_loss_pct * 1.5
        else:
            adjusted_stop_loss_pct = base_stop_loss_pct

        adjusted_stop_loss_pct = max(0.03, min(adjusted_stop_loss_pct, 0.08))

        # ✅ ATR 기반 동적 목표가 설정
        if atr_pct < 2.0:
            profit_target_1 = 10.0  # 낮은 변동성: 보수적
            profit_target_2 = 18.0
        elif atr_pct > 5.0:
            profit_target_1 = 15.0  # 높은 변동성: 공격적
            profit_target_2 = 25.0
        else:
            profit_target_1 = 12.0  # 보통 변동성: 기본
            profit_target_2 = 20.0

        # 수량 계산 (2% 리스크)
        risk_amount = account_balance * 0.02
        stop_loss_amount = current_price * adjusted_stop_loss_pct
        shares = int(risk_amount / stop_loss_amount)

        # 횡보장 50% 축소
        if regime == "sideways":
            shares = int(shares * 0.5)

        # 한 종목 최대 10% (횡보장 5%)
        max_position_pct = 0.05 if regime == "sideways" else 0.10
        max_position = account_balance * max_position_pct
        max_shares = int(max_position / current_price)

        shares = min(shares, max_shares)

        return shares, current_price, atr, adjusted_stop_loss_pct, profit_target_1, profit_target_2

    def execute_strategy(self, ticker, stock_name, exchange):
        """전략 실행 (해외주식)"""
        print(f"\n{'=' * 60}")
        print(f"🇺🇸 해외주식 전략 실행: {stock_name} ({ticker}) [{exchange}]")
        print(f"{'=' * 60}\n")

        try:
            # 시장 상태 감지
            regime, regime_info = self.detect_market_regime(ticker, exchange)
            print(f"🌐 시장 상태: {regime.upper()}")
            if regime_info:
                print(f"  ADX: {regime_info.get('adx', 0):.1f}")
                print(f"  5일 변화율: {regime_info.get('price_change_5d', 0):.2f}%")
                print(f"  장중 변화율: {regime_info.get('intraday_change', 0):.2f}%")
                print(f"  변동성: {regime_info.get('volatility', 0):.2f}%\n")

            # 매수 신호 확인
            signals, details = self.check_buy_signals(ticker, exchange)

            print("📊 매수 신호 체크:")
            for detail in details:
                print(f"  {detail}")
            print(f"\n신호 점수: {signals}/5")

            # 잔고 확인
            balance = self.api.get_overseas_balance()
            cash_usd = 0
            holding_qty = 0
            profit_rate = 0

            if balance and 'output2' in balance:
                try:
                    output2 = balance['output2']
                    if isinstance(output2, dict):
                        # frcr_buy_amt_smtl1 = 외화 매수금액 합계 (예수금)
                        cash_usd = float(output2.get('frcr_buy_amt_smtl1', 0))
                    elif isinstance(output2, list) and len(output2) > 0:
                        cash_usd = float(output2[0].get('frcr_buy_amt_smtl1', 0))
                except (KeyError, IndexError, TypeError, ValueError) as e:
                    print(f"⚠️ 잔고 조회 실패: {e}")
                    cash_usd = 0

            # 해외주식 계좌에 돈이 없으면 기본값 사용 (테스트용)
            if cash_usd == 0:
                print(f"⚠️ 해외주식 계좌 잔고가 $0입니다. 기본값 $10,000 사용 (테스트 모드)")
                cash_usd = 10000
            else:
                print(f"✅ 해외주식 예수금 확인: ${cash_usd:,.2f}")

            if balance and 'output1' in balance:
                try:
                    for stock in balance['output1']:
                        if stock.get('ovrs_pdno') == ticker and float(stock.get('ovrs_cblc_qty', 0)) > 0:
                            holding_qty = int(float(stock.get('ovrs_cblc_qty', 0)))
                            profit_rate = float(stock.get('evlu_pfls_rt', 0))
                            break
                except (KeyError, TypeError, ValueError) as e:
                    print(f"⚠️ 보유 종목 조회 실패: {e}")

            print(f"\n💰 계좌 상태:")
            print(f"  예수금: ${cash_usd:,.2f}")
            print(f"  보유수량: {holding_qty}주")
            if holding_qty > 0:
                print(f"  수익률: {profit_rate}%")

            # 매매 결정
            if holding_qty > 0:
                self._manage_position(ticker, stock_name, exchange, holding_qty, profit_rate, regime)
            else:
                # 급락장 매수 금지
                if regime == "crash":
                    print(f"\n🚨 급락장 감지! 매수 금지")
                    return

                # 보유 종목 수 제한
                current_holdings = self.get_current_holdings_count()
                if current_holdings >= self.max_holdings:
                    print(f"\n⚠️ 보유 종목 한도 초과 ({current_holdings}/{self.max_holdings})")
                    return

                # 섹터 한도 체크 (30%)
                stock_sector = self.get_stock_sector(ticker)
                if stock_sector:
                    total_balance = cash_usd * 1300  # USD to KRW 환산 (대략)
                    sector_exposure = self.get_sector_exposure(stock_sector, total_balance)
                    if sector_exposure >= 0.30:
                        print(f"\n⚠️ 섹터 한도 초과 ({stock_sector}: {sector_exposure*100:.1f}% / 30%)")
                        return

                # 당일 익절 종목 재진입 방지
                if ticker in self.sold_today:
                    print(f"\n⚠️ 당일 익절 종목 - 재진입 방지")
                    return

                # 신호 기반 매수 (공격적 설정: 2개 이상)
                if regime == "sideways":
                    if signals >= 2:
                        print(f"\n📊 횡보장 - 매수! ({signals}/5) [공격적]")
                        self._execute_buy(ticker, stock_name, exchange, cash_usd, signals, regime)
                    else:
                        print(f"\n❌ 횡보장 - 신호 부족 ({signals}/5, 필요: 2+)")

                elif regime == "trending":
                    if signals >= 2:
                        print(f"\n📈 추세장 - 매수! ({signals}/5) [공격적]")
                        self._execute_buy(ticker, stock_name, exchange, cash_usd, signals, regime)
                    else:
                        print(f"\n❌ 추세장 - 신호 부족 ({signals}/5, 필요: 2+)")

                else:
                    if signals >= 4:
                        self._execute_buy(ticker, stock_name, exchange, cash_usd, signals, regime)
                    else:
                        print(f"\n❌ 신호 부족 ({signals}/5, 필요: 4+)")

        except Exception as e:
            error_msg = str(e)
            error_trace = traceback.format_exc()
            print(f"\n❌ 에러 발생: {error_msg}")
            print(error_trace)
            self.notifier.notify_error(
                location=f"{stock_name} ({ticker})",
                error=error_msg
            )

    def _execute_buy(self, ticker, stock_name, exchange, cash_usd, signals, regime):
        """매수 실행"""
        print(f"\n🎯 강한 매수 신호! ({signals}/5)")

        # USD 환산 (간단히 $10,000 초기자본 가정)
        total_balance_usd = cash_usd + 10000
        shares, current_price, atr, stop_loss_pct, target_1, target_2 = self.calculate_position_size(
            ticker, exchange, total_balance_usd * 1300, regime  # KRW 환산
        )

        if shares == 0:
            print("❌ 매수 가능 수량 없음")
            return

        # 피라미드 매수: 40% 먼저
        first_buy = int(shares * 0.4)

        if first_buy > 0:
            exchange_trading = self._convert_exchange_code(exchange)

            atr_pct = (atr / current_price) * 100
            print(f"\n💰 1차 매수: {first_buy}주 @ ${current_price:.2f}")
            print(f"  ATR: ${atr:.2f} ({atr_pct:.2f}%)")
            print(f"  손절: -{stop_loss_pct*100:.1f}%")
            print(f"  ✅ 익절 목표: 1차 +{target_1:.0f}% (50%), 2차 +{target_2:.0f}% (100%)")

            result = self.api.buy_overseas_stock(ticker, first_buy, exchange_trading)

            if result:
                print("✅ 매수 성공!")

                self.pyramid_tracker[ticker] = {
                    'first_buy_qty': first_buy,
                    'first_buy_price': current_price,
                    'target_qty': shares,
                    'remaining_qty': shares - first_buy,
                    'stop_loss_pct': stop_loss_pct,
                    'profit_target_1': target_1,  # ✅ 추가
                    'profit_target_2': target_2,  # ✅ 추가
                    'exchange': exchange
                }

                self.notifier.notify_buy(stock_name, ticker, first_buy, current_price)
            else:
                print("❌ 매수 실패")

    def _manage_position(self, ticker, stock_name, exchange, quantity, profit_rate, regime):
        """포지션 관리"""
        print(f"\n📊 포지션 관리 중...")

        current_price = float(self.api.get_overseas_current_price(ticker, exchange))
        exchange_trading = self._convert_exchange_code(exchange)

        # 급락장 차등 청산
        if regime == "crash":
            if profit_rate >= 8.0:
                sell_qty = int(quantity * 0.5)
                print(f"🚨 급락장 - 50% 부분 청산 (수익 {profit_rate:.2f}%)")
            else:
                sell_qty = quantity
                print(f"🚨 급락장 - 전량 청산")

            self.api.sell_overseas_stock(ticker, sell_qty, exchange_trading)
            return

        # 추세 반전 감지 (데드크로스)
        df = self.get_ohlcv(ticker, exchange, count=30)
        if df is not None and len(df) >= 20:
            df['MA5'] = df['close'].rolling(5).mean()
            df['MA20'] = df['close'].rolling(20).mean()
            latest = df.iloc[-1]

            if pd.notna(latest['MA5']) and pd.notna(latest['MA20']):
                if latest['MA5'] < latest['MA20'] and profit_rate > 0:
                    print(f"\n⚠️ 추세 반전! 익절 (수익률 {profit_rate:.2f}%)")
                    self.api.sell_overseas_stock(ticker, quantity, exchange_trading)
                    return

        # ✅ 트레일링 스탑 - 발동 기준 하향 (+15% → +10%)
        if ticker not in self.peak_profit or profit_rate > self.peak_profit[ticker]:
            self.peak_profit[ticker] = profit_rate
            print(f"  📊 최고 수익률 갱신: {profit_rate:.2f}%")

        if self.peak_profit.get(ticker, 0) >= 10.0:  # ✅ 15.0 → 10.0
            peak = self.peak_profit[ticker]
            drawdown = peak - profit_rate

            if drawdown >= 3.0:
                print(f"\n📉 트레일링 스탑! (최고 {peak:.2f}% → 현재 {profit_rate:.2f}%)")
                self.api.sell_overseas_stock(ticker, quantity, exchange_trading)
                # ✅ 영구 저장 추가
                self.sold_today[ticker] = {'profit_rate': profit_rate, 'reason': 'trailing_stop'}
                self._save_sold_today()
                if ticker in self.pyramid_tracker:
                    del self.pyramid_tracker[ticker]
                return

        # 피라미드 2차 매수
        if ticker in self.pyramid_tracker:
            tracker = self.pyramid_tracker[ticker]
            remaining_qty = tracker['remaining_qty']

            if profit_rate >= 3.0 and remaining_qty > 0:
                print(f"\n📈 피라미드 2차 매수! (수익률 {profit_rate:.2f}%)")
                signals, _ = self.check_buy_signals(ticker, exchange)

                if signals >= 3:
                    second_buy = remaining_qty
                    result = self.api.buy_overseas_stock(ticker, second_buy, exchange_trading)
                    if result:
                        print(f"✅ 2차 추가매수 완료: {second_buy}주")
                        del self.pyramid_tracker[ticker]

        # 손절
        if ticker in self.pyramid_tracker:
            stop_loss_pct = self.pyramid_tracker[ticker].get('stop_loss_pct', 0.05)
            stop_loss_threshold = -stop_loss_pct * 100
        else:
            stop_loss_threshold = -5.0 if regime != "crash" else -3.0

        if profit_rate <= stop_loss_threshold:
            print(f"\n🚨 손절! ({profit_rate:.2f}% <= {stop_loss_threshold:.2f}%)")
            self.api.sell_overseas_stock(ticker, quantity, exchange_trading)
            # ✅ 영구 저장
            self.sold_today[ticker] = {'profit_rate': profit_rate, 'reason': 'stop_loss'}
            self._save_sold_today()
            if ticker in self.pyramid_tracker:
                del self.pyramid_tracker[ticker]
            return

        # ✅ ATR 기반 동적 익절 목표 사용
        if ticker in self.pyramid_tracker:
            target_1 = self.pyramid_tracker[ticker].get('profit_target_1', 12.0)
            target_2 = self.pyramid_tracker[ticker].get('profit_target_2', 20.0)
        else:
            target_1, target_2 = 12.0, 20.0

        # 1차 익절 (50% 매도)
        if profit_rate >= target_1 and quantity > 1:
            sell_qty = int(quantity * 0.5)
            print(f"\n🎯 1차 익절! (+{target_1:.0f}%) - {sell_qty}주 매도")
            self.api.sell_overseas_stock(ticker, sell_qty, exchange_trading)

        # 2차 익절 (전량 매도)
        elif profit_rate >= target_2:
            print(f"\n🚀 2차 익절! (+{target_2:.0f}%) - 전량 매도")
            self.api.sell_overseas_stock(ticker, quantity, exchange_trading)
            # ✅ 영구 저장
            self.sold_today[ticker] = {'profit_rate': profit_rate, 'reason': '2nd_profit_take'}
            self._save_sold_today()
            if ticker in self.pyramid_tracker:
                del self.pyramid_tracker[ticker]
            if ticker in self.peak_profit:
                del self.peak_profit[ticker]

        else:
            print(f"\n⏳ 홀딩 중 (수익률: {profit_rate:.2f}%)")
            print(f"  ✅ 목표: +{target_1:.0f}% (1차), +{target_2:.0f}% (2차)")
            print(f"  손절: {stop_loss_threshold:.0f}%")


if __name__ == "__main__":
    from watchlist_us import get_all_us_stocks

    strategy = OverseasTradingStrategy()
    watchlist = get_all_us_stocks()

    for ticker, name, exchange in watchlist:
        strategy.execute_strategy(ticker, name, exchange)
        print("\n" + "-" * 60 + "\n")
