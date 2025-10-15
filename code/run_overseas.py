# run_overseas.py
"""
해외주식(미국 주식) 자동매매 전략 실행 스크립트
- 미국 장 시간에 실행 (한국 시간 23:30 ~ 06:00)
- 최적 실행 시간: 00:30 (장 시작 1시간 후)
"""
from overseas_strategy import OverseasTradingStrategy
from watchlist_us import get_all_us_stocks
from datetime import datetime

print(f"\n{'='*60}")
print(f"🇺🇸 해외주식 자동매매 시작 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"{'='*60}\n")

# 전략 초기화
strategy = OverseasTradingStrategy()

# 워치리스트 가져오기
watchlist = get_all_us_stocks()

print(f"📊 총 {len(watchlist)}개 종목 분석 시작\n")

# 각 종목 전략 실행
success_count = 0
error_count = 0

for ticker, name, exchange in watchlist:
    try:
        strategy.execute_strategy(ticker, name, exchange)
        success_count += 1
    except Exception as e:
        print(f"❌ {name} ({ticker}) 처리 실패: {e}")
        error_count += 1

    print("\n" + "-" * 60 + "\n")

print(f"\n{'='*60}")
print(f"✅ 해외주식 전략 실행 완료")
print(f"{'='*60}")
print(f"  성공: {success_count}개")
print(f"  실패: {error_count}개")
print(f"  완료 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"{'='*60}\n")
