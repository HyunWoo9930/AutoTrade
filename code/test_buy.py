#!/usr/bin/env python3
# test_buy.py - 매수 테스트 스크립트

from kis_api import KISApi
import sys

def test_buy():
    """삼성전자 1주 매수 테스트"""
    api = KISApi()

    # 1. 토큰 발급
    print("\n=== 1단계: 토큰 발급 ===")
    if not api.get_access_token():
        print("❌ 토큰 발급 실패")
        return False

    # 2. 잔고 확인
    print("\n=== 2단계: 잔고 확인 ===")
    balance = api.get_balance()
    if balance and 'output2' in balance:
        cash = balance['output2'][0]['dnca_tot_amt']
        print(f"💰 예수금: {cash}원")
    else:
        print("❌ 잔고 조회 실패")
        return False

    # 3. 현재가 확인
    print("\n=== 3단계: 삼성전자 현재가 확인 ===")
    price = api.get_current_price("005930")
    if price:
        print(f"📈 삼성전자 현재가: {price}원")
    else:
        print("❌ 현재가 조회 실패")
        return False

    # 4. 매수 테스트
    print("\n=== 4단계: 매수 주문 (1주) ===")
    print("⚠️  실제로 주문합니다! 계속하시겠습니까? (y/N): ", end='')

    # 자동 실행 모드
    if len(sys.argv) > 1 and sys.argv[1] == '--auto':
        confirm = 'y'
        print("y (자동 모드)")
    else:
        confirm = input().lower()

    if confirm != 'y':
        print("❌ 매수 취소")
        return False

    result = api.buy_stock("005930", 1)  # 삼성전자 1주

    if result:
        # 응답 코드 확인
        rt_cd = result.get('rt_cd', '')
        msg_cd = result.get('msg_cd', '')
        msg1 = result.get('msg1', '')

        print(f"📋 응답:")
        print(f"  rt_cd: {rt_cd}")
        print(f"  msg_cd: {msg_cd}")
        print(f"  msg1: {msg1}")

        # rt_cd가 '0'이면 성공, '1'이면 실패
        if rt_cd == '0':
            print("\n✅ 매수 주문 성공!")
            print(f"  주문번호: {result.get('output', {}).get('ODNO', 'N/A')}")
        else:
            print(f"\n❌ 매수 주문 실패: {msg1}")
            return False

        # 5. 잔고 재확인
        print("\n=== 5단계: 매수 후 잔고 확인 ===")
        import time
        time.sleep(2)  # 2초 대기

        balance = api.get_balance()
        if balance and 'output1' in balance:
            for stock in balance['output1']:
                if stock.get('pdno') == '005930' and int(stock.get('hldg_qty', 0)) > 0:
                    print(f"✅ 삼성전자 보유 확인!")
                    print(f"  수량: {stock.get('hldg_qty')}주")
                    print(f"  평단가: {stock.get('pchs_avg_pric')}원")
                    return True

        print("⚠️  주문은 성공했으나 잔고에는 아직 반영 안됨 (체결 대기 중)")
        return True
    else:
        print("❌ 매수 주문 실패")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("🧪 매수 테스트 스크립트")
    print("=" * 60)

    success = test_buy()

    print("\n" + "=" * 60)
    if success:
        print("✅ 테스트 성공!")
    else:
        print("❌ 테스트 실패!")
    print("=" * 60)
