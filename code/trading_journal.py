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

    def get_statistics(self):
        """통계 분석"""
        if not self.trades:
            print("❌ 거래 기록이 없습니다")
            return

        # 매수/매도 분리
        buys = [t for t in self.trades if t['type'] == 'BUY']
        sells = [t for t in self.trades if t['type'] == 'SELL']

        # 청산된 거래만 (손익 계산 가능)
        closed_trades = [t for t in buys if t['result'] == 'CLOSED']

        print("\n" + "=" * 60)
        print("📊 매매 통계")
        print("=" * 60)

        print(f"\n전체 거래:")
        print(f"  총 매수: {len(buys)}회")
        print(f"  총 매도: {len(sells)}회")
        print(f"  청산 완료: {len(closed_trades)}회")
        print(f"  보유 중: {len(buys) - len(closed_trades)}회")

        if closed_trades:
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

            # 손익비
            profit_loss_ratio = abs(avg_profit / avg_loss) if avg_loss != 0 else 0

            print(f"\n손익 분석:")
            print(f"  승: {len(wins)}회 ({len(wins) / len(closed_trades) * 100:.1f}%)")
            print(f"  패: {len(losses)}회 ({len(losses) / len(closed_trades) * 100:.1f}%)")
            print(f"  무: {len(breakeven)}회")
            print(f"  승률: {win_rate:.1f}%")

            print(f"\n금액 분석:")
            print(f"  총 손익: {total_profit:+,}원")
            print(f"  평균 수익: {avg_profit:+,.0f}원")
            print(f"  평균 손실: {avg_loss:+,.0f}원")
            print(f"  손익비: {profit_loss_ratio:.2f}")

            # 최대 수익/손실
            max_profit_trade = max(closed_trades, key=lambda x: x.get('profit_amount', 0))
            max_loss_trade = min(closed_trades, key=lambda x: x.get('profit_amount', 0))

            print(f"\n극값:")
            print(f"  최대 수익: {max_profit_trade.get('profit_amount', 0):+,}원 "
                  f"({max_profit_trade['stock_name']}, {max_profit_trade.get('profit_rate', 0):+.2f}%)")
            print(f"  최대 손실: {max_loss_trade.get('profit_amount', 0):+,}원 "
                  f"({max_loss_trade['stock_name']}, {max_loss_trade.get('profit_rate', 0):+.2f}%)")

    def get_recent_trades(self, n=10):
        """최근 거래 조회"""
        recent = self.trades[-n:][::-1]  # 최근 n개, 역순

        print("\n" + "=" * 60)
        print(f"📋 최근 {min(n, len(self.trades))}개 거래")
        print("=" * 60)

        for trade in recent:
            trade_type = "🔵 매수" if trade['type'] == 'BUY' else "🔴 매도"
            status = trade.get('result', 'OPEN')

            print(f"\n[ID:{trade['id']}] {trade_type} - {trade['stock_name']} ({trade['stock_code']})")
            print(f"  날짜: {trade['date']}")
            print(f"  수량: {trade['quantity']}주 @ {trade['price']:,}원")
            print(f"  금액: {trade['total_amount']:,}원")

            if trade['type'] == 'BUY':
                print(f"  신호: {trade.get('signals', 0)}/5")
                print(f"  전략: {trade.get('strategy_note', '-')}")
                print(f"  상태: {'✅ 청산' if status == 'CLOSED' else '⏳ 보유 중'}")

                if status == 'CLOSED':
                    profit = trade.get('profit_amount', 0)
                    profit_rate = trade.get('profit_rate', 0)
                    emoji = "🟢" if profit > 0 else "🔴"
                    print(f"  손익: {emoji} {profit:+,}원 ({profit_rate:+.2f}%)")

            elif trade['type'] == 'SELL':
                profit = trade.get('profit_amount', 0)
                profit_rate = trade.get('profit_rate', 0)
                emoji = "🟢" if profit > 0 else "🔴"
                print(f"  손익: {emoji} {profit:+,}원 ({profit_rate:+.2f}%)")
                print(f"  이유: {trade.get('sell_reason', '-')}")

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