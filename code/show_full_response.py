#!/usr/bin/env python3
"""
해외주식 잔고 조회 API 전체 응답 출력
"""
from kis_api import KISApi
import json
import time

def show_full_balance_response():
    """해외주식 잔고 조회 전체 응답 출력"""
    print("\n" + "=" * 80)
    print("🔍 해외주식 잔고 조회 API - 전체 응답")
    print("=" * 80)

    api = KISApi()
    time.sleep(1)
    api.get_access_token()

    print("\n📡 API 호출 중...")
    balance = api.get_overseas_balance(exchange="NASD", currency="USD")

    if balance:
        print("\n✅ API 응답 성공!\n")

        # 예쁘게 출력
        print("=" * 80)
        print("📄 전체 JSON 응답:")
        print("=" * 80)
        print(json.dumps(balance, indent=2, ensure_ascii=False))
        print("=" * 80)

        # 파일로 저장
        output_file = 'data/overseas_balance_full.json'
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(balance, f, indent=2, ensure_ascii=False)
            print(f"\n💾 파일 저장 완료: {output_file}")
        except:
            pass

        # 요약 정보
        print("\n" + "=" * 80)
        print("📊 요약 정보:")
        print("=" * 80)

        print(f"\n🔑 응답 키: {list(balance.keys())}")
        print(f"   - rt_cd: {balance.get('rt_cd')} (0=성공)")
        print(f"   - msg1: {balance.get('msg1')}")

        # output1 (보유 종목)
        if 'output1' in balance:
            output1 = balance['output1']
            print(f"\n📦 output1 (보유 종목):")
            print(f"   - 타입: {type(output1)}")
            print(f"   - 개수: {len(output1)}개")

            if isinstance(output1, list) and len(output1) > 0:
                # 실제 보유 종목만 (빈 항목 제외)
                holdings = [s for s in output1 if s.get('ovrs_pdno')]
                print(f"   - 실제 보유: {len(holdings)}개")

                for i, stock in enumerate(holdings, 1):
                    print(f"\n   [{i}] {stock.get('ovrs_item_name')} ({stock.get('ovrs_pdno')})")
                    print(f"       수량: {stock.get('ovrs_cblc_qty')}주")
                    print(f"       평균단가: ${stock.get('pchs_avg_pric')}")
                    print(f"       현재가: ${stock.get('now_pric2')}")
                    print(f"       수익률: {stock.get('evlu_pfls_rt')}%")
                    print(f"       평가금액: ${stock.get('ovrs_stck_evlu_amt')}")

        # output2 (계좌 요약)
        if 'output2' in balance:
            output2 = balance['output2']
            print(f"\n💰 output2 (계좌 요약):")
            print(f"   - 타입: {type(output2)}")

            if isinstance(output2, dict):
                print(f"   - 필드 수: {len(output2)}개\n")

                # 중요 필드 강조
                important_fields = {
                    'frcr_buy_amt_smtl1': '예수금 (USD)',
                    'frcr_pchs_amt1': '매입금액 (USD)',
                    'ovrs_tot_pfls': '총손익 (USD)',
                    'tot_pftrt': '총수익률 (%)',
                    'tot_evlu_pfls_amt': '평가손익금액 (USD)'
                }

                print("   📌 주요 필드:")
                for key, desc in important_fields.items():
                    value = output2.get(key, 'N/A')
                    if value != 'N/A':
                        try:
                            val_float = float(value)
                            if val_float != 0:
                                print(f"      ⭐ {key:25s} = {value:>20s}  ({desc})")
                            else:
                                print(f"         {key:25s} = {value:>20s}  ({desc})")
                        except:
                            print(f"         {key:25s} = {value:>20s}  ({desc})")

                print("\n   📋 전체 필드:")
                for key, value in output2.items():
                    if key not in important_fields:
                        print(f"      {key:25s} = {value}")

        print("\n" + "=" * 80)
        print("💡 예수금 필드: frcr_buy_amt_smtl1")
        print("=" * 80)

    else:
        print("\n❌ API 응답 실패")

def main():
    try:
        show_full_balance_response()
    except Exception as e:
        print(f"\n❌ 에러: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
