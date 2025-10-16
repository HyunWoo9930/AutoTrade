# trading_journal.py
import os
import json
from datetime import datetime
import pandas as pd


class TradingJournal:
    def __init__(self, journal_file="data/trading_journal.json"):
        # 디렉토리 생성 (없으면)
        os.makedirs(os.path.dirname(journal_file), exist_ok=True)
        self.journal_file = journal_file
        self.trades = self._load_journal()

    def _load_journal(self):
        """일지 불러오기"""
        if os.path.exists(self.journal_file):
            with open(self.journal_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []

    def _save_journal(self):
        """일지 저장"""
        with open(self.journal_file, 'w', encoding='utf-8') as f:
            json.dump(self.trades, f, ensure_ascii=False, indent=2)

    def log_buy(self, stock_code, stock_name, quantity, price, signals, strategy_note=""):
        """매수 기록"""
        trade = {
            "id": len(self.trades) + 1,
            "type": "BUY",
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "stock_code": stock_code,
            "stock_name": stock_name,
            "quantity": quantity,
            "price": price,
            "total_amount": quantity * price,
            "signals": signals,
            "strategy_note": strategy_note,
            "emotion": "",  # 나중에 추가 가능
            "result": "OPEN"  # OPEN, CLOSED
        }

        self.trades.append(trade)
        self._save_journal()

        print(f"\n✅ 매수 기록 완료 (ID: {trade['id']})")
        return trade['id']

    def log_sell(self, buy_id, stock_code, stock_name, quantity, price, profit_rate, sell_reason=""):
        """매도 기록"""
        # 매수 기록 찾기
        buy_trade = None
        for trade in self.trades:
            if trade.get('id') == buy_id:
                buy_trade = trade
                break

        if not buy_trade:
            print(f"❌ 매수 기록을 찾을 수 없습니다 (ID: {buy_id})")
            return

        # 손익 계산
        buy_amount = buy_trade['total_amount']
        sell_amount = quantity * price
        profit_amount = sell_amount - buy_amount

        trade = {
            "id": len(self.trades) + 1,
            "type": "SELL",
            "buy_id": buy_id,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "stock_code": stock_code,
            "stock_name": stock_name,
            "quantity": quantity,
            "price": price,
            "total_amount": sell_amount,
            "profit_rate": profit_rate,
            "profit_amount": profit_amount,
            "sell_reason": sell_reason,
            "emotion": "",
            "result": "CLOSED"
        }

        # 매수 기록 상태 업데이트
        buy_trade['result'] = "CLOSED"
        buy_trade['sell_id'] = trade['id']
        buy_trade['profit_rate'] = profit_rate
        buy_trade['profit_amount'] = profit_amount

        self.trades.append(trade)
        self._save_journal()

        print(f"\n✅ 매도 기록 완료 (ID: {trade['id']})")
        print(f"   손익: {profit_amount:,}원 ({profit_rate:+.2f}%)")

        return trade['id']

    def add_note(self, trade_id, note):
        """메모 추가"""
        for trade in self.trades:
            if trade['id'] == trade_id:
                trade['note'] = note
                self._save_journal()
                print(f"✅ 메모 추가 완료 (ID: {trade_id})")
                return
        print(f"❌ 거래 기록을 찾을 수 없습니다 (ID: {trade_id})")

    def add_emotion(self, trade_id, emotion):
        """감정 기록"""
        for trade in self.trades:
            if trade['id'] == trade_id:
                trade['emotion'] = emotion
                self._save_journal()
                print(f"✅ 감정 기록 완료 (ID: {trade_id})")
                return
        print(f"❌ 거래 기록을 찾을 수 없습니다 (ID: {trade_id})")

    def find_open_buy(self, stock_code):
        """종목 코드로 미청산 매수 기록 찾기 (가장 최근 것)"""
        for trade in reversed(self.trades):  # 역순으로 탐색 (최신 것 먼저)
            if (trade.get('type') == 'BUY' and
                trade.get('stock_code') == stock_code and
                trade.get('result') == 'OPEN'):
                return trade.get('id')
        return None

    def get_statistics(self):
        """통계 분석 - 딕셔너리 반환"""
        if not self.trades:
            return {
                'total_trades': 0,
                'wins': 0,
                'losses': 0,
                'draws': 0,
                'win_rate': 0,
                'total_profit': 0,
                'avg_win': 0,
                'avg_loss': 0,
                'avg_holding_days': 0
            }

        # 매수/매도 분리
        buys = [t for t in self.trades if t['type'] == 'BUY']
        sells = [t for t in self.trades if t['type'] == 'SELL']

        # 청산된 거래만 (손익 계산 가능)
        closed_trades = [t for t in buys if t['result'] == 'CLOSED']

        if not closed_trades:
            return {
                'total_trades': len(buys),
                'wins': 0,
                'losses': 0,
                'draws': 0,
                'win_rate': 0,
                'total_profit': 0,
                'avg_win': 0,
                'avg_loss': 0,
                'avg_holding_days': 0
            }

        # 승률 계산
        wins = [t for t in closed_trades if t.get('profit_amount', 0) > 0]
        losses = [t for t in closed_trades if t.get('profit_amount', 0) < 0]
        breakeven = [t for t in closed_trades if t.get('profit_amount', 0) == 0]

        win_rate = len(wins) / len(closed_trades) * 100

        # 평균 손익
        avg_profit = sum([t.get('profit_amount', 0) for t in wins]) / len(wins) if wins else 0
        avg_loss = sum([t.get('profit_amount', 0) for t in losses]) / len(losses) if losses else 0

        # 총 손익
        total_profit = sum([t.get('profit_amount', 0) for t in closed_trades])

        return {
            'total_trades': len(closed_trades),
            'wins': len(wins),
            'losses': len(losses),
            'draws': len(breakeven),
            'win_rate': win_rate,
            'total_profit': total_profit,
            'avg_win': avg_profit,
            'avg_loss': avg_loss,
            'avg_holding_days': 0  # TODO: 보유일 계산
        }

    def print_statistics(self):
        """통계 출력 (기존 기능 유지)"""
        stats = self.get_statistics()

        print("\n" + "=" * 60)
        print("📊 매매 통계")
        print("=" * 60)

        print(f"\n전체 거래:")
        print(f"  청산 완료: {stats['total_trades']}회")
        print(f"  승률: {stats['win_rate']:.1f}%")

        print(f"\n손익 분석:")
        print(f"  승: {stats['wins']}회")
        print(f"  패: {stats['losses']}회")
        print(f"  무: {stats['draws']}회")

        print(f"\n금액 분석:")
        print(f"  총 손익: {stats['total_profit']:+,}원")
        print(f"  평균 수익: {stats['avg_win']:+,.0f}원")
        print(f"  평균 손실: {stats['avg_loss']:+,.0f}원")

    def get_recent_trades(self, n=10, days=None):
        """최근 거래 조회

        Args:
            n: 최근 N개 거래 (days가 None일 때)
            days: 최근 N일 거래 (지정하면 n 무시)

        Returns:
            list: 거래 리스트 (딕셔너리 형태)
        """
        from datetime import datetime, timedelta

        if days is not None:
            # 최근 N일 거래 필터링
            cutoff_date = datetime.now() - timedelta(days=days)
            filtered = []

            for trade in self.trades:
                try:
                    trade_date = datetime.strptime(trade['date'], "%Y-%m-%d %H:%M:%S")
                    if trade_date >= cutoff_date:
                        filtered.append(trade)
                except:
                    continue

            recent = filtered[::-1]  # 역순 (최신순)
        else:
            # 최근 N개 거래
            recent = self.trades[-n:][::-1]

        # 딕셔너리 형태로 변환 (Discord Bot용)
        result = []
        for trade in recent:
            result.append({
                'type': 'buy' if trade['type'] == 'BUY' else 'sell',
                'stock_code': trade['stock_code'],
                'stock_name': trade['stock_name'],
                'quantity': trade['quantity'],
                'price': trade['price'],
                'timestamp': trade['date'],
                'profit_rate': trade.get('profit_rate', 0),
                'profit': trade.get('profit_amount', 0),
                'sell_reason': trade.get('sell_reason', '')
            })

        return result

    def print_recent_trades(self, n=10):
        """최근 거래 출력 (기존 기능 유지)"""
        trades = self.get_recent_trades(n=n)

        print("\n" + "=" * 60)
        print(f"📋 최근 {len(trades)}개 거래")
        print("=" * 60)

        for trade in trades:
            trade_type = "🔵 매수" if trade['type'] == 'buy' else "🔴 매도"

            print(f"\n{trade_type} - {trade['stock_name']} ({trade['stock_code']})")
            print(f"  날짜: {trade['timestamp']}")
            print(f"  수량: {trade['quantity']}주 @ {trade['price']:,}원")

            if trade['type'] == 'sell':
                profit = trade.get('profit', 0)
                profit_rate = trade.get('profit_rate', 0)
                emoji = "🟢" if profit > 0 else "🔴"
                print(f"  손익: {emoji} {profit:+,}원 ({profit_rate:+.2f}%)")
                if trade.get('sell_reason'):
                    print(f"  이유: {trade['sell_reason']}")

    def export_to_excel(self, filename="trading_journal.xlsx"):
        """엑셀로 내보내기"""
        if not self.trades:
            print("❌ 거래 기록이 없습니다")
            return

        df = pd.DataFrame(self.trades)
        df.to_excel(filename, index=False, engine='openpyxl')
        print(f"✅ 엑셀 파일 생성: {filename}")


# 테스트
if __name__ == "__main__":
    journal = TradingJournal()

    # 테스트 데이터 추가 (실제로는 advanced_strategy에서 자동 기록)
    # buy_id = journal.log_buy(
    #     stock_code="005930",
    #     stock_name="삼성전자",
    #     quantity=10,
    #     price=90000,
    #     signals=4,
    #     strategy_note="정배열 + RSI 적정 + MACD 골든크로스 + 거래량 급증"
    # )

    # journal.log_sell(
    #     buy_id=buy_id,
    #     stock_code="005930",
    #     stock_name="삼성전자",
    #     quantity=10,
    #     price=99000,
    #     profit_rate=10.0,
    #     sell_reason="1차 익절 (목표 +10% 달성)"
    # )

    # 통계 조회
    journal.get_statistics()

    # 최근 거래 조회
    journal.get_recent_trades(10)