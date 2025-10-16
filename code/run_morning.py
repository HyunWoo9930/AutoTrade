# run_morning.py
from multi_stock_monitor import MultiStockMonitor
from watchlist import get_all_stocks, WATCHLIST
from discord.discord_notifier import DiscordNotifier
from kis_api import KISApi
from datetime import datetime

print(f"\n{'='*60}")
print(f"🌅 아침 루틴 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"{'='*60}\n")

# API 초기화
api = KISApi()
api.get_access_token()

notifier = DiscordNotifier(market='domestic')

# 감시 종목 목록
watchlist = get_all_stocks()
print(f"📊 감시 종목: {len(watchlist)}개\n")

# 주요 종목 현재가 조회
top_stocks = []
print("💰 주요 종목 현재가 조회 중...\n")

for code, name in watchlist[:10]:  # 상위 10개만 조회 (시간 절약)
    try:
        price = api.get_current_price(code)
        if price:
            price_int = int(price)
            top_stocks.append((name, code, price_int))
            print(f"  ✅ {name} ({code}): {price_int:,}원")
    except Exception as e:
        print(f"  ❌ {name} 조회 실패: {e}")

# 디스코드 알림
notifier.notify_morning(
    stock_count=len(watchlist),
    top_stocks=top_stocks
)

# 섹터별 요약
print("\n" + "="*60)
print("📋 섹터별 종목 수")
print("="*60)
for sector, stock_list in WATCHLIST.items():
    print(f"  {sector}: {len(stock_list)}개")
print(f"\n  총 {len(watchlist)}개 종목")

print("\n✅ 아침 루틴 완료!")