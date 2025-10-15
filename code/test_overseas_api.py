# test_overseas_api.py
"""
해외주식 API 응답 구조 확인용 스크립트
"""
from kis_api import KISApi
import json

def test_overseas_balance():
    """해외주식 잔고 조회 테스트"""
    print("\n" + "=" * 60)
    print("🧪 해외주식 잔고 조회 테스트")
    print("=" * 60)

    api = KISApi()
    api.get_access_token()

    balance = api.get_overseas_balance()

    if balance:
        print("\n✅ API 응답 성공!")
        print(f"\n📋 응답 키 목록: {list(balance.keys())}")

        # rt_cd, msg_cd 등 상태 코드 출력
        if 'rt_cd' in balance:
            print(f"\n응답 코드: {balance['rt_cd']}")
        if 'msg1' in balance:
            print(f"메시지: {balance['msg1']}")

        # output1 (보유 종목)
        if 'output1' in balance:
            print(f"\n📊 output1 타입: {type(balance['output1'])}")
            if isinstance(balance['output1'], list):
                print(f"📊 output1 개수: {len(balance['output1'])}개")
                if len(balance['output1']) > 0:
                    print(f"\n첫 번째 항목 키:")
                    for key in balance['output1'][0].keys():
                        print(f"  - {key}: {balance['output1'][0][key]}")
            elif isinstance(balance['output1'], dict):
                print(f"📊 output1 키:")
                for key in balance['output1'].keys():
                    print(f"  - {key}: {balance['output1'][key]}")

        # output2 (잔고 요약) - 상세 출력
        if 'output2' in balance:
            print(f"\n💰 output2 타입: {type(balance['output2'])}")
            if isinstance(balance['output2'], list):
                print(f"💰 output2 개수: {len(balance['output2'])}개")
                if len(balance['output2']) > 0:
                    print(f"\n잔고 정보 (모든 필드):")
                    for key, value in balance['output2'][0].items():
                        print(f"  {key:30s} = {value}")
            elif isinstance(balance['output2'], dict):
                print(f"💰 output2 키 개수: {len(balance['output2'])}개")
                print(f"\n잔고 정보 (모든 필드):")
                for key, value in balance['output2'].items():
                    print(f"  {key:30s} = {value}")

                # 예수금 관련 필드 추정
                print(f"\n💡 예수금 관련 추정 필드:")
                cash_candidates = [k for k in balance['output2'].keys() if 'dncl' in k.lower() or 'evlu' in k.lower() or 'tota' in k.lower()]
                for key in cash_candidates:
                    print(f"  ✅ {key:30s} = {balance['output2'][key]}")

        # 전체 JSON 저장
        with open('data/overseas_balance_response.json', 'w', encoding='utf-8') as f:
            json.dump(balance, f, indent=2, ensure_ascii=False)
        print(f"\n💾 전체 응답 저장: data/overseas_balance_response.json")

    else:
        print("\n❌ API 응답 실패")

def test_overseas_price():
    """해외주식 현재가 조회 테스트"""
    print("\n" + "=" * 60)
    print("🧪 해외주식 현재가 조회 테스트 (AAPL)")
    print("=" * 60)

    api = KISApi()
    api.get_access_token()

    price = api.get_overseas_current_price("AAPL", "NAS")

    if price:
        print(f"\n✅ Apple 현재가: ${price}")
    else:
        print("\n❌ 현재가 조회 실패")

def test_overseas_ohlcv():
    """해외주식 OHLCV 조회 테스트"""
    print("\n" + "=" * 60)
    print("🧪 해외주식 OHLCV 조회 테스트 (AAPL)")
    print("=" * 60)

    api = KISApi()
    api.get_access_token()

    df = api.get_overseas_ohlcv("AAPL", "NAS", "D", 10)

    if df is not None and len(df) > 0:
        print(f"\n✅ {len(df)}개 데이터 수신")
        print(f"\n최근 5일 데이터:")
        print(df.tail(5).to_string())
    else:
        print("\n❌ OHLCV 조회 실패")

if __name__ == "__main__":
    # 1. 잔고 조회 (가장 중요!)
    test_overseas_balance()

    print("\n" + "=" * 60 + "\n")

    # 2. 현재가 조회
    test_overseas_price()

    print("\n" + "=" * 60 + "\n")

    # 3. OHLCV 조회
    test_overseas_ohlcv()

    print("\n" + "=" * 60)
    print("✅ 테스트 완료!")
    print("=" * 60)
