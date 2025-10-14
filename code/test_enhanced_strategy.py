# test_enhanced_strategy.py
"""
강화된 전략 테스트 스크립트
- 시장 상태 감지 (추세장/횡보장/급락장)
- 피라미드 매수 (40% + 60% 분할)
- 급락장 보호 메커니즘
"""

from advanced_strategy import AdvancedTradingStrategy
from watchlist import get_all_stocks

def test_market_regime(strategy):
    """시장 상태 감지 테스트"""
    print("\n" + "=" * 80)
    print("📊 시장 상태 감지 테스트")
    print("=" * 80)

    # 테스트 종목들
    test_stocks = [
        ("005930", "삼성전자"),
        ("000660", "SK하이닉스"),
        ("035420", "NAVER")
    ]

    for code, name in test_stocks:
        print(f"\n📌 {name} ({code})")
        regime, regime_info = strategy.detect_market_regime(code)

        regime_emoji = {
            "trending": "📈",
            "sideways": "📊",
            "crash": "🚨",
            "unknown": "❓"
        }

        print(f"  시장 상태: {regime_emoji.get(regime, '❓')} {regime.upper()}")
        if regime_info:
            print(f"  • ADX: {regime_info.get('adx', 0):.1f}")
            print(f"  • 5일 변화율: {regime_info.get('price_change_5d', 0):.2f}%")
            print(f"  • 변동성: {regime_info.get('volatility', 0):.2f}%")

def test_buy_signals(strategy):
    """매수 신호 체크 및 임계치 테스트"""
    print("\n" + "=" * 80)
    print("🎯 매수 신호 및 시장별 임계치 테스트")
    print("=" * 80)

    test_stocks = [
        ("005930", "삼성전자"),
        ("000660", "SK하이닉스")
    ]

    for code, name in test_stocks:
        print(f"\n📌 {name} ({code})")

        # 시장 상태 확인
        regime, regime_info = strategy.detect_market_regime(code)
        print(f"  시장 상태: {regime}")

        # 매수 신호 확인
        signals, details = strategy.check_buy_signals(code)
        print(f"  신호 점수: {signals}/5")

        # 임계치 체크
        if regime == "crash":
            print(f"  ❌ 급락장 - 매수 금지")
        elif regime == "sideways":
            if signals >= 4:
                print(f"  ✅ 횡보장 - 매수 가능 (4+)")
            else:
                print(f"  ❌ 횡보장 - 신호 부족 (필요: 4+, 현재: {signals})")
        elif regime == "trending":
            if signals >= 3:
                print(f"  ✅ 추세장 - 매수 가능 (3+)")
            else:
                print(f"  ❌ 추세장 - 신호 부족 (필요: 3+, 현재: {signals})")
        else:
            if signals >= 4:
                print(f"  ✅ 불명확 - 매수 가능 (4+)")
            else:
                print(f"  ❌ 불명확 - 신호 부족 (필요: 4+, 현재: {signals})")

def test_pyramid_logic():
    """피라미드 매수 로직 시뮬레이션"""
    print("\n" + "=" * 80)
    print("📈 피라미드 매수 로직 테스트")
    print("=" * 80)

    print("\n피라미드 매수 흐름:")
    print("  1️⃣ 1차 매수: 목표 수량의 40% 진입")
    print("  2️⃣ 수익률 +3~5% 구간 도달")
    print("  3️⃣ 신호 재확인 (3개 이상)")
    print("  4️⃣ 2차 추가매수: 목표 수량의 60% 진입")
    print("  5️⃣ 평균 단가 재조정 완료")

    print("\n예시:")
    print("  목표 수량: 100주")
    print("  1차 매수: 40주 @ 50,000원")
    print("  2차 매수: 60주 @ 52,000원 (수익률 +4% 시)")
    print("  평균 단가: 51,200원")

def test_crash_protection():
    """급락장 보호 메커니즘 테스트"""
    print("\n" + "=" * 80)
    print("🚨 급락장 보호 메커니즘 테스트")
    print("=" * 80)

    print("\n급락장 감지 조건:")
    print("  • 5일간 -10% 이상 하락")
    print("  • 변동성 8% 초과")

    print("\n급락장 감지 시 보호 조치:")
    print("  1️⃣ 신호가 강해도 신규 매수 금지")
    print("  2️⃣ 보유 포지션 즉시 긴급 청산")
    print("  3️⃣ 손절 라인 강화 (-5% → -3%)")
    print("  4️⃣ 디스코드 긴급 알림 발송")

def main():
    """전체 테스트 실행"""
    print("\n" + "=" * 80)
    print("🚀 강화된 3단 로켓 전략 테스트")
    print("=" * 80)

    print("\n✨ 추가된 기능:")
    print("  1. 시장 상태 감지 (ADX 기반)")
    print("  2. 횡보장 대응 (신호 임계치 상향: 3→4)")
    print("  3. 급락장 보호 (매수 금지 + 긴급 청산)")
    print("  4. 피라미드 매수 (40% + 60% 분할)")
    print("  5. 강화된 손절 (급락장: -5% → -3%)")

    # ⚠️ 토큰을 한 번만 발급받아 재사용
    print("\n⏳ KIS API 토큰 발급 중... (1분당 1회 제한)")
    strategy = AdvancedTradingStrategy()

    if not strategy.api.access_token:
        print("❌ 토큰 발급 실패. 1분 후 다시 시도하세요.")
        return

    # 테스트 실행 (같은 strategy 객체 재사용)
    test_market_regime(strategy)
    test_buy_signals(strategy)
    test_pyramid_logic()
    test_crash_protection()

    print("\n" + "=" * 80)
    print("✅ 테스트 완료!")
    print("=" * 80)

    print("\n📝 다음 단계:")
    print("  1. Docker 이미지 빌드 및 푸시")
    print("  2. K8s CronJob으로 자동 실행")
    print("  3. Discord로 실시간 모니터링")
    print("  4. 매매 일지 확인 (data/trading_journal.json)")

if __name__ == "__main__":
    main()
