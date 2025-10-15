# backtest.py
"""
백테스팅 시스템
- 과거 데이터로 전략 성과 테스트
- 수익률, 승률, MDD, 샤프 비율 계산
"""

from advanced_strategy import AdvancedTradingStrategy
from kis_api import KISApi
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
from typing import Dict, List, Tuple
import time


class Backtester:
    def __init__(self, initial_cash=30000000):
        """
        초기 자본금으로 백테스트 초기화

        Args:
            initial_cash: 초기 자본 (기본 3천만원)
        """
        self.initial_cash = initial_cash
        self.cash = initial_cash
        self.positions = {}  # {stock_code: {'qty': int, 'avg_price': float, 'buy_date': str}}
        self.trade_history = []  # 매매 기록
        self.equity_curve = []  # 일별 자산 변화

        self.strategy = AdvancedTradingStrategy()
        self.api = self.strategy.api

    def get_historical_data(self, stock_code: str, start_date: str, end_date: str) -> pd.DataFrame:
        """
        과거 데이터 조회

        Args:
            stock_code: 종목 코드
            start_date: 시작일 (YYYYMMDD) - 참고용
            end_date: 종료일 (YYYYMMDD) - 참고용

        Returns:
            DataFrame with OHLCV data
        """
        print(f"  데이터 조회 중: {stock_code}")

        # KIS API로 과거 데이터 조회 (최근 30일만 가능)
        df = self.strategy.get_ohlcv(stock_code, count=100)  # 최대한 많이

        if df is None or len(df) == 0:
            return pd.DataFrame()

        # 날짜 문자열 추가
        df['date_str'] = df['date'].dt.strftime('%Y%m%d')

        print(f"    ✅ {len(df)}일 데이터 수집")

        return df

    def simulate_buy(self, stock_code: str, stock_name: str, price: float,
                     date: str, signals: int, regime: str) -> bool:
        """
        매수 시뮬레이션

        Returns:
            매수 성공 여부
        """
        # 포지션 사이징 (현재가로 포트폴리오 평가)
        current_prices = {stock_code: price}
        shares, _, _, stop_loss_pct, _, _ = self.strategy.calculate_position_size(
            stock_code, self.cash + self._get_portfolio_value(current_prices), regime
        )

        if shares == 0:
            return False

        # 40% 1차 매수 (피라미드 전략)
        first_buy = int(shares * 0.4)
        cost = first_buy * price

        if cost > self.cash:
            # 자금 부족
            return False

        # 매수 체결
        self.cash -= cost
        self.positions[stock_code] = {
            'qty': first_buy,
            'avg_price': price,
            'buy_date': date,
            'stop_loss_pct': stop_loss_pct,
            'target_qty': shares,
            'remaining_qty': shares - first_buy,
            'regime': regime,
            'name': stock_name
        }

        # 기록
        self.trade_history.append({
            'date': date,
            'action': 'BUY',
            'stock_code': stock_code,
            'stock_name': stock_name,
            'price': price,
            'qty': first_buy,
            'cost': cost,
            'signals': signals,
            'regime': regime,
            'cash_after': self.cash
        })

        print(f"    ✅ 매수: {stock_name} {first_buy}주 @ {price:,.0f}원 (신호 {signals}/5)")
        return True

    def simulate_sell(self, stock_code: str, price: float, date: str,
                      reason: str, partial: bool = False) -> bool:
        """
        매도 시뮬레이션

        Args:
            partial: True면 50% 매도, False면 전량 매도

        Returns:
            매도 성공 여부
        """
        if stock_code not in self.positions:
            return False

        position = self.positions[stock_code]

        if partial:
            sell_qty = int(position['qty'] * 0.5)
        else:
            sell_qty = position['qty']

        if sell_qty == 0:
            return False

        # 매도 체결
        revenue = sell_qty * price
        self.cash += revenue

        # 수익률 계산
        profit_rate = (price - position['avg_price']) / position['avg_price'] * 100
        profit_amount = (price - position['avg_price']) * sell_qty

        # 기록
        self.trade_history.append({
            'date': date,
            'action': 'SELL',
            'stock_code': stock_code,
            'stock_name': position['name'],
            'price': price,
            'qty': sell_qty,
            'revenue': revenue,
            'profit_rate': profit_rate,
            'profit_amount': profit_amount,
            'reason': reason,
            'cash_after': self.cash,
            'hold_days': (datetime.strptime(date, '%Y%m%d') -
                         datetime.strptime(position['buy_date'], '%Y%m%d')).days
        })

        # 포지션 업데이트
        if partial:
            position['qty'] -= sell_qty
            print(f"    🔵 부분 매도: {position['name']} {sell_qty}주 @ {price:,.0f}원 ({profit_rate:+.2f}%) - {reason}")
        else:
            del self.positions[stock_code]
            print(f"    {'🟢' if profit_rate > 0 else '🔴'} 전량 매도: {position['name']} {sell_qty}주 @ {price:,.0f}원 ({profit_rate:+.2f}%) - {reason}")

        return True

    def _get_portfolio_value(self, current_prices: Dict[str, float] = None) -> float:
        """현재 보유 포지션 평가액"""
        if current_prices is None:
            current_prices = {}

        total = 0
        for code, pos in self.positions.items():
            price = current_prices.get(code, pos['avg_price'])
            total += pos['qty'] * price

        return total

    def run(self, stock_codes: List[Tuple[str, str]], start_date: str, end_date: str):
        """
        백테스팅 실행

        Args:
            stock_codes: [(code, name), ...] 테스트할 종목 리스트
            start_date: 시작일 (YYYYMMDD)
            end_date: 종료일 (YYYYMMDD)
        """
        print("\n" + "="*80)
        print("🚀 백테스팅 시작")
        print("="*80)
        print(f"기간: {start_date} ~ {end_date}")
        print(f"초기 자본: {self.initial_cash:,}원")
        print(f"테스트 종목: {len(stock_codes)}개")
        print("="*80 + "\n")

        # 1. 과거 데이터 수집
        print("📊 1단계: 과거 데이터 수집 중...")
        historical_data = {}

        for code, name in stock_codes[:10]:  # 10개 종목 테스트
            df = self.get_historical_data(code, start_date, end_date)
            if len(df) > 0:
                historical_data[code] = {
                    'name': name,
                    'data': df
                }
            time.sleep(0.1)  # API 레이트 리밋

        print(f"✅ {len(historical_data)}개 종목 데이터 수집 완료\n")

        if len(historical_data) == 0:
            print("❌ 데이터가 없습니다. 백테스트를 종료합니다.")
            return

        # 2. 날짜별 시뮬레이션
        print("⚙️ 2단계: 전략 시뮬레이션 중...\n")

        # 모든 날짜 목록 생성
        all_dates = set()
        for info in historical_data.values():
            all_dates.update(info['data']['date_str'].tolist())

        all_dates = sorted(list(all_dates))

        for i, date in enumerate(all_dates):
            if i % 10 == 0:
                print(f"  진행: {i+1}/{len(all_dates)} ({date})")

            current_prices = {}

            # 각 종목 처리
            for code, info in historical_data.items():
                name = info['name']
                df = info['data']

                # 해당 날짜 데이터
                day_data = df[df['date_str'] == date]
                if len(day_data) == 0:
                    continue

                current_price = float(day_data.iloc[0]['close'])
                current_prices[code] = current_price

                # 보유 중인 종목 관리
                if code in self.positions:
                    position = self.positions[code]
                    profit_rate = (current_price - position['avg_price']) / position['avg_price'] * 100

                    # 손절 체크
                    stop_loss_threshold = -position['stop_loss_pct'] * 100
                    if profit_rate <= stop_loss_threshold:
                        self.simulate_sell(code, current_price, date, f"손절 ({profit_rate:.2f}%)")
                        continue

                    # 1차 익절 (+10%)
                    if profit_rate >= 10.0 and position['qty'] > 1:
                        self.simulate_sell(code, current_price, date, "1차 익절 (+10%)", partial=True)
                        continue

                    # 2차 익절 (+20%)
                    if profit_rate >= 20.0:
                        self.simulate_sell(code, current_price, date, "2차 익절 (+20%)")
                        continue

                # 신규 매수 체크 (보유 중이 아니고, 포지션 여유 있으면)
                elif len(self.positions) < 10:
                    # 과거 30일 데이터로 신호 계산
                    past_data = df[df['date_str'] <= date].tail(30)

                    if len(past_data) >= 20:
                        # 시장 상태 감지 (간소화)
                        regime = "trending"  # 실제로는 detect_market_regime 사용

                        # 신호 계산 (간소화)
                        signals = self._calculate_signals_simple(past_data)

                        # 매수 조건 체크
                        if signals >= 3:
                            self.simulate_buy(code, name, current_price, date, signals, regime)

            # 일별 자산 기록
            portfolio_value = self._get_portfolio_value(current_prices)
            total_value = self.cash + portfolio_value

            self.equity_curve.append({
                'date': date,
                'cash': self.cash,
                'portfolio': portfolio_value,
                'total': total_value,
                'positions': len(self.positions)
            })

        # 3. 결과 분석
        print("\n" + "="*80)
        print("📊 3단계: 결과 분석")
        print("="*80 + "\n")

        self.analyze_results()

    def _calculate_signals_simple(self, df: pd.DataFrame) -> int:
        """간단한 신호 계산 (백테스팅용)"""
        if len(df) < 20:
            return 0

        signals = 0

        # MA
        df['MA5'] = df['close'].rolling(5).mean()
        df['MA20'] = df['close'].rolling(20).mean()
        if df.iloc[-1]['MA5'] > df.iloc[-1]['MA20']:
            signals += 1

        # RSI
        import ta
        df['RSI'] = ta.momentum.rsi(df['close'], window=14)
        if 30 < df.iloc[-1]['RSI'] < 70:
            signals += 1

        # 거래량
        avg_vol = df['volume'].tail(20).mean()
        if df.iloc[-1]['volume'] > avg_vol * 1.2:
            signals += 1

        return signals

    def analyze_results(self):
        """결과 분석 및 출력"""
        if len(self.trade_history) == 0:
            print("❌ 매매 기록이 없습니다.")
            return

        # 최종 자산
        final_value = self.cash + self._get_portfolio_value()
        total_return = (final_value - self.initial_cash) / self.initial_cash * 100

        # 매매 통계
        trades = [t for t in self.trade_history if t['action'] == 'SELL']

        if len(trades) == 0:
            print("❌ 매도 거래가 없습니다. (모든 포지션 보유 중)")
            print(f"\n💼 **현재 포지션**")
            print(f"  보유 종목: {len(self.positions)}개")
            for code, pos in self.positions.items():
                print(f"    - {pos['name']}: {pos['qty']}주 @ {pos['avg_price']:,.0f}원")

            # 자산 평가
            portfolio_value = self._get_portfolio_value()
            total = self.cash + portfolio_value
            unrealized_return = (total - self.initial_cash) / self.initial_cash * 100

            print(f"\n💰 **자산 평가**")
            print(f"  현금: {self.cash:,}원")
            print(f"  포지션: {portfolio_value:,.0f}원")
            print(f"  총 자산: {total:,.0f}원")
            print(f"  미실현 수익률: {unrealized_return:+.2f}%")

            self.save_results()
            return

        wins = [t for t in trades if t['profit_rate'] > 0]
        losses = [t for t in trades if t['profit_rate'] <= 0]

        win_rate = len(wins) / len(trades) * 100 if len(trades) > 0 else 0
        avg_profit = np.mean([t['profit_rate'] for t in wins]) if len(wins) > 0 else 0
        avg_loss = np.mean([t['profit_rate'] for t in losses]) if len(losses) > 0 else 0

        # MDD (Maximum Drawdown)
        equity = [e['total'] for e in self.equity_curve]
        peak = equity[0]
        max_dd = 0

        for value in equity:
            if value > peak:
                peak = value
            dd = (peak - value) / peak * 100
            if dd > max_dd:
                max_dd = dd

        # 샤프 비율 (간소화)
        daily_returns = []
        for i in range(1, len(equity)):
            daily_return = (equity[i] - equity[i-1]) / equity[i-1]
            daily_returns.append(daily_return)

        sharpe = 0
        if len(daily_returns) > 0 and np.std(daily_returns) > 0:
            sharpe = np.mean(daily_returns) / np.std(daily_returns) * np.sqrt(252)

        # 결과 출력
        print("📈 **수익률 분석**")
        print(f"  초기 자본: {self.initial_cash:,}원")
        print(f"  최종 자산: {final_value:,}원")
        print(f"  총 수익률: {total_return:+.2f}%")
        print(f"  최대 낙폭(MDD): {max_dd:.2f}%")
        print(f"  샤프 비율: {sharpe:.2f}")

        print(f"\n💼 **매매 통계**")
        print(f"  총 거래: {len(trades)}회")
        print(f"  승: {len(wins)}회 | 패: {len(losses)}회")
        print(f"  승률: {win_rate:.1f}%")
        print(f"  평균 수익: {avg_profit:+.2f}%")
        print(f"  평균 손실: {avg_loss:+.2f}%")

        if len(wins) > 0 and len(losses) > 0:
            profit_factor = abs(avg_profit * len(wins) / (avg_loss * len(losses)))
            print(f"  손익비: {profit_factor:.2f}")

        # 보유 기간
        hold_days = [t['hold_days'] for t in trades]
        if len(hold_days) > 0:
            print(f"\n⏱️ **보유 기간**")
            print(f"  평균: {np.mean(hold_days):.1f}일")
            print(f"  최소: {min(hold_days)}일")
            print(f"  최대: {max(hold_days)}일")
        else:
            print(f"\n⏱️ **보유 기간**")
            print(f"  매도 거래 없음 (아직 보유 중)")

        # 상세 매매 기록 저장
        self.save_results()

    def save_results(self):
        """결과를 JSON 파일로 저장"""
        results = {
            'config': {
                'initial_cash': self.initial_cash,
                'final_cash': self.cash,
                'positions': len(self.positions)
            },
            'trades': self.trade_history,
            'equity_curve': self.equity_curve
        }

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"data/backtest_result_{timestamp}.json"

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        print(f"\n💾 결과 저장: {filename}")


if __name__ == "__main__":
    # 백테스팅 실행
    from watchlist import get_all_stocks

    # 테스트 설정
    backtester = Backtester(initial_cash=30000000)

    # 종목 목록
    stocks = get_all_stocks()

    # 백테스팅 기간 (KIS API는 최근 30일만 제공)
    end_date = datetime.now().strftime('%Y%m%d')
    start_date = (datetime.now() - timedelta(days=30)).strftime('%Y%m%d')

    print(f"\n⚠️ 백테스팅 기간: {start_date} ~ {end_date}")
    print(f"⚠️ 제한사항: KIS API는 최근 30일 데이터만 제공")
    print(f"⚠️ 테스트 종목: 10개 (전체 {len(stocks)}개 중)\n")

    # 실행
    backtester.run(stocks, start_date, end_date)
