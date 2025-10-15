#!/usr/bin/env python3
"""
해외주식 예수금 필드 찾기
API 문서 기반으로 다양한 파라미터 조합 테스트
"""
from kis_api import KISApi
import time
import json

def test_all_exchanges():
    """모든 거래소에 대해 잔고 조회"""
    api = KISApi()
    time.sleep(1)
    api.get_access_token()

    exchanges = [
        ("NASD", "나스닥"),
        ("NYSE", "뉴욕"),
        ("AMEX", "아멕스"),
        ("SEHK", "홍콩"),
        ("SHAA", "중국상해"),
        ("SZAA", "중국심천"),
        ("TKSE", "도쿄"),
        ("HASE", "하노이"),
        ("VNSE", "호치민")
    ]

    print("\n" + "=" * 80)
    print("🔍 거래소별 해외주식 잔고 조회 테스트")
    print("=" * 80)

    all_fields = set()

    for exc_code, exc_name in exchanges:
        print(f"\n{'=' * 80}")
        print(f"📊 {exc_name} ({exc_code})")
        print(f"{'=' * 80}")

        url = f"{api.config.BASE_URL}/uapi/overseas-stock/v1/trading/inquire-balance"

        headers = {
            "content-type": "application/json",
            "authorization": f"Bearer {api.access_token}",
            "appkey": api.config.APP_KEY,
            "appsecret": api.config.APP_SECRET,
            "tr_id": "VTTS3012R"
        }

        # USD, HKD, CNY, JPY, VND 등 다양한 통화
        currency_map = {
            "NASD": "USD", "NYSE": "USD", "AMEX": "USD",
            "SEHK": "HKD", "SHAA": "CNY", "SZAA": "CNY",
            "TKSE": "JPY", "HASE": "VND", "VNSE": "VND"
        }

        params = {
            "CANO": api.config.ACCOUNT_NO,
            "ACNT_PRDT_CD": "01",
            "OVRS_EXCG_CD": exc_code,
            "TR_CRCY_CD": currency_map.get(exc_code, "USD"),
            "CTX_AREA_FK200": "",
            "CTX_AREA_NK200": ""
        }

        time.sleep(0.6)  # Rate limit

        import requests
        res = requests.get(url, headers=headers, params=params)

        if res.status_code == 200:
            data = res.json()

            if data.get('rt_cd') == '0':
                print(f"✅ 성공!")

                if 'output2' in data and data['output2']:
                    output2 = data['output2']

                    # 모든 필드 수집
                    for key in output2.keys():
                        all_fields.add(key)

                    # 0이 아닌 값 찾기
                    non_zero = []
                    for key, value in output2.items():
                        try:
                            if float(value) != 0:
                                non_zero.append((key, value))
                        except:
                            pass

                    if non_zero:
                        print(f"  ⭐ 0이 아닌 값:")
                        for key, value in non_zero:
                            print(f"     {key:30s} = {value}")
                    else:
                        print(f"  ℹ️  모든 필드가 0 (잔고 없음)")
            else:
                print(f"❌ 실패: {data.get('msg1', 'Unknown')}")
        else:
            print(f"❌ HTTP 오류: {res.status_code}")

    # 전체 필드 목록
    print(f"\n{'=' * 80}")
    print(f"📋 발견된 모든 output2 필드 목록 ({len(all_fields)}개)")
    print(f"{'=' * 80}")
    for field in sorted(all_fields):
        print(f"  - {field}")

    print(f"\n{'=' * 80}")
    print("💡 예수금 가능성 높은 필드 추정:")
    print(f"{'=' * 80}")

    # 예수금 관련 키워드
    keywords = ['dncl', 'evlu', 'tota', 'amt', 'cash', 'balance']
    candidates = []

    for field in all_fields:
        for kw in keywords:
            if kw in field.lower():
                candidates.append(field)
                break

    for field in sorted(set(candidates)):
        print(f"  ✅ {field}")

def main():
    print("\n" + "=" * 80)
    print("🔍 해외주식 예수금 필드 완전 탐색")
    print("=" * 80)

    try:
        test_all_exchanges()

        print(f"\n{'=' * 80}")
        print("📝 결론:")
        print(f"{'=' * 80}")
        print("1. 모든 거래소에서 0이 아닌 값이 있으면 → 해당 필드가 예수금")
        print("2. 모두 0이면 → KIS 모의투자 사이트에서 USD 입금 필요")
        print("3. https://mock.koreainvestment.com")
        print(f"{'=' * 80}")

    except Exception as e:
        print(f"\n❌ 에러: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
