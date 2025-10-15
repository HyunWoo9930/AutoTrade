# test_overseas.py
"""
해외주식 전략 테스트 스크립트
"""
from overseas_strategy import OverseasTradingStrategy
from watchlist_us import get_all_us_stocks, get_us_stocks_by_sector, print_us_watchlist

def test_single_stock():
    """단일 종목 테스트"""
    print("\n" + "=" * 80)
    print("🧪 단일 종목 테스트 (Apple)")
    print("=" * 80)

    strategy = OverseasTradingStrategy()

    # Apple 테스트
    strategy.execute_strategy("AAPL", "Apple", "NAS")

def test_sector():
    """섹터별 테스트"""
    print("\n" + "=" * 80)
    print("🧪 섹터별 테스트 (빅테크)")
    print("=" * 80)

    strategy = OverseasTradingStrategy()

    # 빅테크 섹터만
    big_tech = get_us_stocks_by_sector("빅테크")

    for ticker, name, exchange in big_tech[:3]:  # 처음 3개만
        strategy.execute_strategy(ticker, name, exchange)
        print("\n" + "-" * 60 + "\n")

def test_all_stocks():
    """전체 종목 테스트"""
    print("\n" + "=" * 80)
    print("🧪 전체 종목 테스트")
    print("=" * 80)

    # 워치리스트 출력
    print_us_watchlist()

    strategy = OverseasTradingStrategy()
    watchlist = get_all_us_stocks()

    print(f"\n📊 총 {len(watchlist)}개 종목 분석 시작...\n")

    for ticker, name, exchange in watchlist:
        try:
            strategy.execute_strategy(ticker, name, exchange)
        except Exception as e:
            print(f"❌ {name} ({ticker}) 에러: {e}")
        print("\n" + "-" * 60 + "\n")

def compare_strategies():
    """국내주식 vs 해외주식 전략 비교"""
    print("\n" + "=" * 80)
    print("📊 전략 비교: 국내 vs 해외")
    print("=" * 80)

    print("\n✅ 공통 전략 (9가지):")
    print("  1. 급락장 차등 청산 (수익 중 50%, 손실 100%)")
    print("  2. 동시 보유 종목 수 제한 (최대 15개) [공격적]")
    print("  3. 추세 반전 감지 (데드크로스 익절)")
    print("  4. 섹터 분산 관리 (섹터당 30%) [공격적]")
    print("  5. 트레일링 스탑 (최고점 대비 -3%)")
    print("  6. 매수 타이밍 최적화 (장 시간대별)")
    print("  7. 익절 후 재진입 금지 (당일)")
    print("  8. 신호 가중치 적용 (MA: 2.0, MACD/Volume: 1.5)")
    print("  9. 변동성 기반 손절 조정 (ATR 기반)")

    print("\n🔄 차이점:")
    print("  국내주식:")
    print("    - 장 시간: 09:00~15:30 (KST)")
    print("    - 통화: KRW (원)")
    print("    - 시장: 코스피/코스닥")
    print("    - API: domestic-stock")

    print("\n  해외주식:")
    print("    - 장 시간: 23:30~06:00 (KST 기준)")
    print("    - 통화: USD (달러)")
    print("    - 시장: 나스닥/NYSE/AMEX")
    print("    - API: overseas-stock")

    print("\n📈 신호 임계치 (공격적 설정):")
    print("  - 추세장: 2개 이상 (기존 3개)")
    print("  - 횡보장: 2개 이상 (기존 3개)")
    print("  - 불명확: 4개 이상")

def main():
    """메인 메뉴"""
    print("\n" + "=" * 80)
    print("🇺🇸 해외주식 전략 테스트")
    print("=" * 80)

    print("\n선택:")
    print("  1. 단일 종목 테스트 (AAPL)")
    print("  2. 섹터별 테스트 (빅테크 3개)")
    print("  3. 전체 종목 테스트")
    print("  4. 전략 비교 (국내 vs 해외)")

    choice = input("\n선택 (1-4): ").strip()

    if choice == "1":
        test_single_stock()
    elif choice == "2":
        test_sector()
    elif choice == "3":
        test_all_stocks()
    elif choice == "4":
        compare_strategies()
    else:
        print("❌ 잘못된 선택")

if __name__ == "__main__":
    # 자동 실행: 섹터별 테스트
    test_sector()
