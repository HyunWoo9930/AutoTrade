# run_strategy.py
from advanced_strategy import AdvancedTradingStrategy
from watchlist import get_all_stocks
from discord.discord_notifier import DiscordNotifier
from datetime import datetime
import time


def main():
    start_time = time.time()

    print(f"\n{'=' * 60}")
    print(f"🎯 전략 실행 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'=' * 60}\n")

    # 디스코드 알림
    notifier = DiscordNotifier()
    notifier.notify_start("run_strategy.py")

    strategy = AdvancedTradingStrategy()
    watchlist = get_all_stocks()

    print(f"📊 분석 대상: {len(watchlist)}개 종목\n")

    success_count = 0
    error_count = 0
    buy_signals = []

    for i, (code, name) in enumerate(watchlist, 1):
        try:
            print(f"\n{'=' * 60}")
            print(f"[{i}/{len(watchlist)}] {name} ({code}) 분석 중...")
            print(f"{'=' * 60}")

            # 신호 체크
            signals, _ = strategy.check_buy_signals(code)

            # 전략 실행
            strategy.execute_strategy(code, name)

            # 강한 신호 기록
            if signals >= 4:
                buy_signals.append(f"{name} ({signals}/5)")

            success_count += 1

            # API 호출 간격 (과부하 방지)
            if i < len(watchlist):
                time.sleep(1)

        except Exception as e:
            print(f"❌ 에러 발생: {name} - {e}")
            error_count += 1

    # 실행 시간 계산
    duration = time.time() - start_time

    # 요약 출력
    print("\n" + "=" * 60)
    print("📊 실행 결과 요약")
    print("=" * 60)
    print(f"✅ 성공: {success_count}/{len(watchlist)} 종목")
    print(f"❌ 실패: {error_count}/{len(watchlist)} 종목")
    print(f"⏱️ 실행시간: {duration:.1f}초")

    if buy_signals:
        print(f"\n🎯 강한 매수 신호 ({len(buy_signals)}개):")
        for signal in buy_signals:
            print(f"  - {signal}")
    else:
        print("\n⏳ 강한 매수 신호 없음")

    print("=" * 60)

    # 🔔 디스코드 종료 알림
    notifier.notify_end(
        script_name="run_strategy.py",
        success=success_count,
        total=len(watchlist),
        duration=duration
    )


if __name__ == "__main__":
    main()