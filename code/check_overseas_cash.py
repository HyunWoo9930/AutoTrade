#!/usr/bin/env python3
# check_overseas_cash.py
"""
해외주식 예수금 조회 - 다양한 방법 테스트
"""
from kis_api import KISApi
import json
import time

def check_method_1():
    """방법 1: 기존 잔고조회 API (VTTS3012R) - 나스닥"""
    print("\n" + "=" * 70)
    print("방법 1: 해외주식 잔고조회 API (나스닥)")
    print("=" * 70)

    api = KISApi()
    time.sleep(1)
    api.get_access_token()

    url = f"{api.config.BASE_URL}/uapi/overseas-stock/v1/trading/inquire-balance"

    headers = {
        "content-type": "application/json",
        "authorization": f"Bearer {api.access_token}",
        "appkey": api.config.APP_KEY,
        "appsecret": api.config.APP_SECRET,
        "tr_id": "VTTS3012R"
    }

    params = {
        "CANO": api.config.ACCOUNT_NO,
        "ACNT_PRDT_CD": "01",
        "OVRS_EXCG_CD": "NASD",
        "TR_CRCY_CD": "USD",
        "CTX_AREA_FK200": "",
        "CTX_AREA_NK200": ""
    }

    time.sleep(0.5)
    import requests
    res = requests.get(url, headers=headers, params=params)

    if res.status_code == 200:
        data = res.json()
        print(f"\n✅ 응답 성공!")
        print(f"\nrt_cd: {data.get('rt_cd')}")
        print(f"msg1: {data.get('msg1')}")

        if 'output2' in data:
            print(f"\n📊 output2 필드 ({len(data['output2'])}개):")
            for key, value in data['output2'].items():
                # 0이 아닌 값 또는 중요 키워드 포함
                if float(value) != 0 or any(kw in key.lower() for kw in ['dncl', 'cash', 'evlu', 'tota']):
                    print(f"  ⭐ {key:30s} = {value}")
                else:
                    print(f"     {key:30s} = {value}")
    else:
        print(f"❌ 실패: {res.text}")

def check_method_2():
    """방법 2: 해외주식 잔고조회 API (뉴욕)"""
    print("\n" + "=" * 70)
    print("방법 2: 해외주식 잔고조회 API (뉴욕)")
    print("=" * 70)

    api = KISApi()

    url = f"{api.config.BASE_URL}/uapi/overseas-stock/v1/trading/inquire-balance"

    headers = {
        "content-type": "application/json",
        "authorization": f"Bearer {api.access_token}",
        "appkey": api.config.APP_KEY,
        "appsecret": api.config.APP_SECRET,
        "tr_id": "VTTS3012R"
    }

    params = {
        "CANO": api.config.ACCOUNT_NO,
        "ACNT_PRDT_CD": "01",
        "OVRS_EXCG_CD": "NYSE",  # 뉴욕 거래소
        "TR_CRCY_CD": "USD",
        "CTX_AREA_FK200": "",
        "CTX_AREA_NK200": ""
    }

    time.sleep(0.5)
    import requests
    res = requests.get(url, headers=headers, params=params)

    if res.status_code == 200:
        data = res.json()
        print(f"\n✅ 응답 성공!")

        if 'output2' in data:
            print(f"\n📊 output2 필드:")
            for key, value in data['output2'].items():
                if float(value) != 0:
                    print(f"  ⭐ {key:30s} = {value}")
    else:
        print(f"❌ 실패: {res.text}")

def check_method_3():
    """방법 3: 통합 계좌 조회 (국내+해외)"""
    print("\n" + "=" * 70)
    print("방법 3: 통합 계좌 조회 시도")
    print("=" * 70)

    api = KISApi()

    # 국내주식 잔고 조회로 해외주식 예수금도 나오는지 확인
    url = f"{api.config.BASE_URL}/uapi/domestic-stock/v1/trading/inquire-balance"

    headers = {
        "content-type": "application/json",
        "authorization": f"Bearer {api.access_token}",
        "appkey": api.config.APP_KEY,
        "appsecret": api.config.APP_SECRET,
        "tr_id": "VTTC8434R"
    }

    params = {
        "CANO": api.config.ACCOUNT_NO,
        "ACNT_PRDT_CD": "01",
        "AFHR_FLPR_YN": "N",
        "OFL_YN": "",
        "INQR_DVSN": "02",
        "UNPR_DVSN": "01",
        "FUND_STTL_ICLD_YN": "N",
        "FNCG_AMT_AUTO_RDPT_YN": "N",
        "PRCS_DVSN": "01",
        "CTX_AREA_FK100": "",
        "CTX_AREA_NK100": ""
    }

    time.sleep(0.5)
    import requests
    res = requests.get(url, headers=headers, params=params)

    if res.status_code == 200:
        data = res.json()
        print(f"\n✅ 국내주식 잔고 조회 성공!")

        if 'output2' in data and len(data['output2']) > 0:
            output2 = data['output2'][0]
            print(f"\n📊 주요 필드:")
            print(f"  예수금: {output2.get('dnca_tot_amt', 'N/A')}원")
            print(f"  총평가금액: {output2.get('tot_evlu_amt', 'N/A')}원")

            # 외화 관련 필드 찾기
            print(f"\n🔍 외화 관련 필드:")
            for key, value in output2.items():
                if 'frcr' in key.lower() or 'ovrs' in key.lower() or 'usd' in key.lower():
                    print(f"  {key:30s} = {value}")
    else:
        print(f"❌ 실패: {res.text}")

def main():
    print("\n" + "=" * 70)
    print("🔍 해외주식 예수금 조회 - 다양한 방법 테스트")
    print("=" * 70)

    try:
        check_method_1()  # 나스닥
        time.sleep(2)

        check_method_2()  # 뉴욕
        time.sleep(2)

        check_method_3()  # 통합 조회

    except Exception as e:
        print(f"\n❌ 에러: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 70)
    print("✅ 테스트 완료!")
    print("=" * 70)
    print("\n💡 결론:")
    print("  - output2에 0이 아닌 값이 있으면 → 해당 필드가 예수금")
    print("  - 모두 0이면 → KIS 모의투자 사이트에서 USD 입금 필요")
    print("  - https://mock.koreainvestment.com")
    print("=" * 70)

if __name__ == "__main__":
    main()
