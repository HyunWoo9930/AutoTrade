# run_overseas_evening.py
"""
해외주식 저녁 루틴 (미국 장 마감 후)
- 실행 시간: 화~토 06:10 (한국 시간, 미국 장 마감 10분 후)
- 미국 정규장: 23:30~06:00 (KST)
"""
from kis_api import KISApi
from discord.discord_notifier import DiscordNotifier
from datetime import datetime

print(f"\n{'='*60}")
print(f"🇺🇸 해외주식 저녁 루틴 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"{'='*60}\n")

# API 초기화
api = KISApi()
api.get_access_token()

notifier = DiscordNotifier()

# 해외 잔고 조회
balance = api.get_overseas_balance()
cash_usd = 0
holdings_list = []
total_stock_value_usd = 0

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
        for stock in balance['output1']:
            qty = float(stock.get('ovrs_cblc_qty', 0))
            if qty > 0:
                current_price = float(stock.get('now_pric2', 0))
                profit_rate = float(stock.get('evlu_pfls_rt', 0))
                stock_value = qty * current_price

                holdings_list.append({
                    'name': stock.get('ovrs_item_name', 'N/A'),
                    'ticker': stock.get('ovrs_pdno', ''),
                    'qty': int(qty),
                    'current_price': current_price,
                    'profit_rate': profit_rate,
                    'value': stock_value
                })
                total_stock_value_usd += stock_value
    except Exception as e:
        print(f"⚠️ 보유 종목 조회 실패: {e}")

total_asset_usd = cash_usd + total_stock_value_usd

print(f"💵 예수금: ${cash_usd:,.2f}")
print(f"📊 보유 종목: {len(holdings_list)}개")
print(f"📈 평가금액: ${total_stock_value_usd:,.2f}")
print(f"💎 총 자산: ${total_asset_usd:,.2f}")

if holdings_list:
    print(f"\n📌 보유 종목 상세:")
    for item in holdings_list:
        emoji = "🟢" if item['profit_rate'] >= 0 else "🔴"
        print(f"  {emoji} {item['name']}: {item['qty']}주 (${item['current_price']:.2f}, {item['profit_rate']:+.2f}%)")

# Discord 알림 - 해외주식 보유 현황
notifier.notify_evening(
    cash=int(cash_usd * 1300),  # 원화 환산 (대략)
    holdings_list=[{
        'name': f"🇺🇸 {h['name']}",
        'code': h['ticker'],
        'qty': h['qty'],
        'avg_price': int(h['current_price'] * 1300),
        'current_price': int(h['current_price'] * 1300),
        'profit_rate': h['profit_rate']
    } for h in holdings_list],
    total=int(total_asset_usd * 1300)
)

# 해외주식 일일 리포트
notifier.notify_daily_report({
    'buys': 0,  # TODO: 해외주식 저널 추가 시 업데이트
    'sells': 0,
    'wins': 0,
    'losses': 0,
    'win_rate': 0,
    'profit': 0,
    'avg_win': 0,
    'avg_loss': 0,
    'cash': int(cash_usd * 1300),
    'stocks': int(total_stock_value_usd * 1300),
    'total': int(total_asset_usd * 1300)
})

print("\n✅ 해외주식 저녁 루틴 완료!")
