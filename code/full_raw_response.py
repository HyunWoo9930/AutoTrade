#!/usr/bin/env python3
"""
해외주식 잔고 조회 - RAW 응답 전체 출력 (축약 없음)
"""
from kis_api import KISApi
import json
import time

api = KISApi()
print("토큰 발급 중...")
time.sleep(1)
api.get_access_token()

print("\nAPI 호출 중...\n")
time.sleep(1)

balance = api.get_overseas_balance(exchange="NASD", currency="USD")

if balance:
    print("=" * 100)
    print("전체 RAW JSON 응답:")
    print("=" * 100)

    # 축약 없이 전체 출력
    response_str = json.dumps(balance, indent=2, ensure_ascii=False)
    print(response_str)

    print("\n" + "=" * 100)
    print(f"총 문자 수: {len(response_str)}")
    print("=" * 100)

    # 파일 저장
    with open('overseas_balance_raw.json', 'w', encoding='utf-8') as f:
        f.write(response_str)
    print("\n✅ 파일 저장: overseas_balance_raw.json")

else:
    print("❌ 응답 실패")
