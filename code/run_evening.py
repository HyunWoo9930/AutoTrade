# run_evening.py
from trading_journal import TradingJournal
from watchlist import get_all_stocks
from kis_api import KISApi
from discord.discord_notifier import DiscordNotifier
from datetime import datetime

print(f"\n{'='*60}")
print(f"🌙 저녁 루틴 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"{'='*60}\n")

# API 초기화
api = KISApi()
api.get_access_token()

notifier = DiscordNotifier()

# 잔고 조회
balance = api.get_balance()
cash = 0
holdings_list = []
total_stock_value = 0

print(f"🔍 잔고 조회 결과: {balance is not None}")
if balance:
    print(f"   - output1 존재: {'output1' in balance}")
    print(f"   - output2 존재: {'output2' in balance}")
else:
    print(f"   ❌ 잔고 조회 실패!")

if balance and 'output2' in balance:
    cash = int(balance['output2'][0]['dnca_tot_amt'])
    print(f"   ✅ 예수금 조회 성공: {cash:,}원")

if balance and 'output1' in balance:
    for stock in balance['output1']:
        qty = int(stock.get('hldg_qty', 0))
        if qty > 0:
            holdings_list.append({
                'name': stock.get('prdt_name', 'N/A'),
                'code': stock.get('pdno', ''),
                'qty': qty,
                'avg_price': int(float(stock.get('pchs_avg_pric', 0))),
                'current_price': int(float(stock.get('prpr', 0))),
                'profit_rate': float(stock.get('evlu_pfls_rt', 0))
            })
            total_stock_value += int(float(stock.get('evlu_amt', 0)))

total_asset = cash + total_stock_value

print(f"💰 예수금: {cash:,}원")
print(f"📊 보유 종목: {len(holdings_list)}개")
print(f"📈 평가금액: {total_stock_value:,}원")
print(f"💎 총 자산: {total_asset:,}원")

if holdings_list:
    print(f"\n📌 보유 종목 상세:")
    for item in holdings_list:
        emoji = "🟢" if item['profit_rate'] >= 0 else "🔴"
        print(f"  {emoji} {item['name']}: {item['qty']}주 ({item['profit_rate']:+.2f}%)")

# 🔔 디스코드 알림 (보유 종목 상세 포함)
notifier.notify_evening(
    cash=cash,
    holdings_list=holdings_list,
    total=total_asset
)

# 매매 일지에서 통계 가져오기
print("\n" + "="*60)
print("📊 오늘의 매매 통계")
print("="*60)

journal = TradingJournal()

# 통계 계산
buys = [t for t in journal.trades if t['type'] == 'BUY']
sells = [t for t in journal.trades if t['type'] == 'SELL']
closed_trades = [t for t in buys if t.get('result') == 'CLOSED']

wins = [t for t in closed_trades if t.get('profit_amount', 0) > 0]
losses = [t for t in closed_trades if t.get('profit_amount', 0) < 0]

total_profit = sum([t.get('profit_amount', 0) for t in closed_trades])
avg_win = sum([t.get('profit_amount', 0) for t in wins]) / len(wins) if wins else 0
avg_loss = sum([t.get('profit_amount', 0) for t in losses]) / len(losses) if losses else 0
win_rate = (len(wins) / len(closed_trades) * 100) if closed_trades else 0

# 콘솔 출력
journal.get_statistics()
journal.get_recent_trades(5)

# 🔔 일일 리포트 디스코드 알림
notifier.notify_daily_report({
    'buys': len(buys),
    'sells': len(sells),
    'wins': len(wins),
    'losses': len(losses),
    'win_rate': win_rate,
    'profit': total_profit,
    'avg_win': avg_win,
    'avg_loss': avg_loss,
    'cash': cash,
    'stocks': total_stock_value,
    'total': total_asset
})

# 감시 종목 수
watchlist = get_all_stocks()
print(f"\n📊 현재 감시 중: {len(watchlist)}개 종목")

print("\n✅ 저녁 루틴 완료!")