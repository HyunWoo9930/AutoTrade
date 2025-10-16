# run_overseas_morning.py
"""
해외주식 아침 루틴 (미국 장 시작 전)
- 실행 시간: 화~토 23:20 (한국 시간, 미국 장 시작 10분 전)
- 미국 정규장: 23:30~06:00 (KST)
"""
from kis_api import KISApi
from discord.discord_notifier import DiscordNotifier
from datetime import datetime

print(f"\n{'='*60}")
print(f"🇺🇸 해외주식 아침 루틴 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"{'='*60}\n")

# API 초기화
api = KISApi()
api.get_access_token()

notifier = DiscordNotifier(market='overseas')

# 해외 잔고 조회
balance = api.get_overseas_balance()
cash_usd = 0
holdings_count = 0

if balance and 'output2' in balance:
    try:
        output2 = balance['output2']
        if isinstance(output2, dict):
            cash_usd = float(output2.get('frcr_buy_amt_smtl1', 0))
        elif isinstance(output2, list) and len(output2) > 0:
            cash_usd = float(output2[0].get('frcr_buy_amt_smtl1', 0))
    except (KeyError, IndexError, TypeError, ValueError) as e:
        print(f"⚠️ 잔고 조회 실패: {e}")

if balance and 'output1' in balance:
    try:
        if isinstance(balance['output1'], list):
            holdings_count = len([s for s in balance['output1'] if float(s.get('ovrs_cblc_qty', 0)) > 0])
    except:
        pass

print(f"💵 해외주식 예수금: ${cash_usd:,.2f}")
print(f"📊 보유 종목: {holdings_count}개")

# Discord 알림
notifier.notify_system(
    "🇺🇸 해외주식 장 시작 전 체크",
    f"예수금: ${cash_usd:,.2f}\n"
    f"보유 종목: {holdings_count}개\n"
    f"🕐 미국 장 시작: 10분 후 (23:30 KST)"
)

print("\n✅ 해외주식 아침 루틴 완료!")
