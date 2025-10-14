# multi_stock_monitor.py
from kis_api import KISApi


class MultiStockMonitor:
    def __init__(self):
        self.api = KISApi()
        self.api.get_access_token()

    def monitor_stocks(self, stock_list):
        """
        여러 종목의 현재가를 모니터링

        Args:
            stock_list: 종목 리스트 [{"code": "005930", "name": "삼성전자"}, ...]
        """
        print("\n" + "=" * 60)
        print("📊 여러 종목 실시간 모니터링")
        print("=" * 60 + "\n")

        for stock in stock_list:
            code = stock['code']
            name = stock['name']

            # 현재가 조회
            current_price = self.api.get_current_price(code)

            if current_price:
                print(f"📈 {name} ({code}): {current_price}원")

        # 보유 종목 확인
        print("\n" + "=" * 60)
        print("💼 현재 보유 종목")
        print("=" * 60 + "\n")

        balance = self.api.get_balance()
        has_stock = False

        if balance and 'output1' in balance:
            for stock in balance['output1']:
                if int(stock.get('hldg_qty', 0)) > 0:
                    has_stock = True
                    print(f"📊 {stock.get('prdt_name')}: "
                          f"{stock.get('hldg_qty')}주, "
                          f"평가금액: {stock.get('evlu_amt')}원, "
                          f"수익률: {stock.get('evlu_pfls_rt')}%")

        if not has_stock:
            print("보유 종목 없음")

        if balance and 'output2' in balance:
            print(f"\n💰 예수금: {balance['output2'][0]['dnca_tot_amt']}원")


if __name__ == "__main__":
    monitor = MultiStockMonitor()

    # 모니터링할 종목 리스트
    stocks = [
        {"code": "005930", "name": "삼성전자"},
        {"code": "000660", "name": "SK하이닉스"},
        {"code": "035420", "name": "NAVER"},
        {"code": "005380", "name": "현대차"},
        {"code": "035720", "name": "카카오"}
    ]

    monitor.monitor_stocks(stocks)