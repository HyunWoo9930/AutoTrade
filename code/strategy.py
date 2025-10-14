# strategy.py
from kis_api import KISApi
from code.discord.discord_notifier import DiscordNotifier


class TradingStrategy:
    def __init__(self):
        self.api = KISApi()
        self.api.get_access_token()
        self.notifier = DiscordNotifier()

    def simple_strategy(self, stock_code, stock_name, buy_price, sell_profit_rate, sell_loss_rate):
        """
        간단한 자동매매 전략 (디스코드 알림 포함)

        Args:
            stock_code: 종목코드 (예: "005930")
            stock_name: 종목명 (예: "삼성전자")
            buy_price: 매수 목표가 (이 가격 이하면 매수)
            sell_profit_rate: 목표 수익률 (%) - 이 수익률 달성하면 매도
            sell_loss_rate: 손절 수익률 (%) - 이 수익률 이하로 떨어지면 손절
        """
        print(f"\n{'=' * 50}")
        print(f"전략 실행: {stock_name} ({stock_code})")
        print(f"매수 목표가: {buy_price}원 이하")
        print(f"목표 수익률: {sell_profit_rate}%")
        print(f"손절 수익률: {sell_loss_rate}%")
        print(f"{'=' * 50}\n")

        # 1. 현재가 확인
        current_price = int(self.api.get_current_price(stock_code))
        print(f"📈 현재가: {current_price}원")

        # 2. 잔고 확인
        balance = self.api.get_balance()
        holding_qty = 0
        profit_rate = 0.0

        if balance and 'output1' in balance:
            for stock in balance['output1']:
                if stock.get('pdno') == stock_code and int(stock.get('hldg_qty', 0)) > 0:
                    holding_qty = int(stock.get('hldg_qty', 0))
                    profit_rate = float(stock.get('evlu_pfls_rt', 0))
                    print(f"📊 보유 수량: {holding_qty}주")
                    print(f"💹 현재 수익률: {profit_rate}%")
                    break

        # 3. 매매 판단
        if holding_qty > 0:
            # 보유 중일 때: 매도 조건 확인
            if profit_rate >= sell_profit_rate:
                print(f"\n🎯 목표 수익률 달성! ({profit_rate}% >= {sell_profit_rate}%)")
                print("💰 매도 주문 실행...")
                result = self.api.sell_stock(stock_code, holding_qty)
                if result:
                    print(f"✅ 매도 성공!")
                    # 디스코드 알림
                    self.notifier.notify_sell(stock_name, stock_code, holding_qty, current_price, profit_rate)
            elif profit_rate <= sell_loss_rate:
                print(f"\n🚨 손절 라인 도달! ({profit_rate}% <= {sell_loss_rate}%)")
                print("💰 손절 매도 실행...")
                result = self.api.sell_stock(stock_code, holding_qty)
                if result:
                    print(f"✅ 손절 매도 성공!")
                    # 디스코드 알림
                    self.notifier.notify_sell(stock_name, stock_code, holding_qty, current_price, profit_rate)
            else:
                print(f"\n⏳ 대기 중... (목표: {sell_profit_rate}%, 손절: {sell_loss_rate}%)")
        else:
            # 미보유 중일 때: 매수 조건 확인
            if current_price <= buy_price:
                print(f"\n🎯 매수 조건 충족! ({current_price}원 <= {buy_price}원)")
                print("💰 매수 주문 실행...")
                result = self.api.buy_stock(stock_code, 1)
                if result:
                    print(f"✅ 매수 성공!")
                    # 디스코드 알림
                    self.notifier.notify_buy(stock_name, stock_code, 1, current_price)
            else:
                print(f"\n⏳ 매수 대기 중... (목표가: {buy_price}원)")


if __name__ == "__main__":
    strategy = TradingStrategy()

    # 삼성전자 자동매매 전략 실행
    strategy.simple_strategy(
        stock_code="005930",
        stock_name="삼성전자",
        buy_price=95000,
        sell_profit_rate=3.0,
        sell_loss_rate=-2.0
    )