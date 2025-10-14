# main.py
from kis_api import KISApi
import json


def main():
    api = KISApi()

    # 토큰 발급
    if api.get_access_token():

        # 1. 현재 보유 종목 확인
        print("\n=== 현재 보유 종목 확인 ===")
        balance = api.get_balance()
        if balance and 'output1' in balance and balance['output1']:
            for stock in balance['output1']:
                if int(stock.get('hldg_qty', 0)) > 0:
                    stock_name = stock.get('prdt_name', 'N/A')
                    stock_code = stock.get('pdno', '')
                    quantity = int(stock.get('hldg_qty', 0))
                    profit_rate = stock.get('evlu_pfls_rt', 0)

                    print(f"📊 {stock_name} ({stock_code}): {quantity}주, 수익률: {profit_rate}%")

        # 2. 현재가 확인
        print("\n=== 삼성전자 현재가 조회 ===")
        price = api.get_current_price("005930")
        if price:
            print(f"📈 현재가: {price}원")

        # 3. 매도 주문 (보유 중인 삼성전자 전량 매도)
        print("\n=== 매도 주문 테스트 ===")
        result = api.sell_stock("005930", 1)  # 1주 매도
        if result:
            print(f"주문번호: {result.get('output', {}).get('ODNO', 'N/A')}")

        # 4. 매도 후 잔고 확인
        print("\n=== 매도 후 잔고 확인 ===")
        balance = api.get_balance()
        if balance:
            if 'output2' in balance and len(balance['output2']) > 0:
                print(f"💰 예수금: {balance['output2'][0]['dnca_tot_amt']}원")

            if 'output1' in balance and balance['output1']:
                has_stock = False
                for stock in balance['output1']:
                    if int(stock.get('hldg_qty', 0)) > 0:
                        has_stock = True
                        print(f"📊 {stock.get('prdt_name', 'N/A')}: {stock.get('hldg_qty', 0)}주")

                if not has_stock:
                    print("📊 보유 종목 없음")


if __name__ == "__main__":
    main()