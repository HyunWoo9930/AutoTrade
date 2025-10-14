# scheduler_advanced.py
import schedule
import time
from advanced_strategy import AdvancedTradingStrategy
from multi_stock_monitor import MultiStockMonitor
from datetime import datetime


def is_market_open():
    """장 운영 시간 확인"""
    now = datetime.now()

    # 주말 제외
    if now.weekday() >= 5:
        return False

    # 9시~15시 30분
    market_start = now.replace(hour=9, minute=0, second=0)
    market_end = now.replace(hour=15, minute=30, second=0)

    return market_start <= now <= market_end


def morning_routine():
    """장 시작 전 루틴"""
    if not is_market_open():
        return

    print("\n" + "=" * 60)
    print("🌅 아침 루틴 - 시장 분석")
    print("=" * 60)

    monitor = MultiStockMonitor()
    stocks = [
        {"code": "005930", "name": "삼성전자"},
        {"code": "000660", "name": "SK하이닉스"},
        {"code": "035420", "name": "NAVER"},
        {"code": "373220", "name": "LG에너지솔루션"},
        {"code": "207940", "name": "삼성바이오로직스"}
    ]

    monitor.monitor_stocks(stocks)


def execute_strategies():
    """전략 실행"""
    if not is_market_open():
        return

    print("\n" + "=" * 60)
    print("🎯 전략 실행")
    print("=" * 60)

    strategy = AdvancedTradingStrategy()

    # 관심 종목 리스트
    watchlist = [
        {"code": "005930", "name": "삼성전자"},
        {"code": "000660", "name": "SK하이닉스"},
        {"code": "035420", "name": "NAVER"}
    ]

    for stock in watchlist:
        try:
            strategy.execute_strategy(stock['code'], stock['name'])
            time.sleep(2)  # API 호출 간격
        except Exception as e:
            print(f"❌ 에러 발생: {stock['name']} - {e}")


def evening_routine():
    """장 마감 후 루틴"""
    print("\n" + "=" * 60)
    print("🌙 저녁 루틴 - 오늘 결과 정리")
    print("=" * 60)

    monitor = MultiStockMonitor()
    stocks = [{"code": "005930", "name": "삼성전자"}]
    monitor.monitor_stocks(stocks)


# 스케줄 설정
def setup_schedule():
    """스케줄 설정"""
    # 평일 08:50 - 아침 루틴
    schedule.every().monday.at("08:50").do(morning_routine)
    schedule.every().tuesday.at("08:50").do(morning_routine)
    schedule.every().wednesday.at("08:50").do(morning_routine)
    schedule.every().thursday.at("08:50").do(morning_routine)
    schedule.every().friday.at("08:50").do(morning_routine)

    # 평일 10:00, 14:00 - 전략 실행
    schedule.every().monday.at("10:00").do(execute_strategies)
    schedule.every().monday.at("14:00").do(execute_strategies)
    schedule.every().tuesday.at("10:00").do(execute_strategies)
    schedule.every().tuesday.at("14:00").do(execute_strategies)
    schedule.every().wednesday.at("10:00").do(execute_strategies)
    schedule.every().wednesday.at("14:00").do(execute_strategies)
    schedule.every().thursday.at("10:00").do(execute_strategies)
    schedule.every().thursday.at("14:00").do(execute_strategies)
    schedule.every().friday.at("10:00").do(execute_strategies)
    schedule.every().friday.at("14:00").do(execute_strategies)

    # 평일 15:40 - 저녁 루틴
    schedule.every().monday.at("15:40").do(evening_routine)
    schedule.every().tuesday.at("15:40").do(evening_routine)
    schedule.every().wednesday.at("15:40").do(evening_routine)
    schedule.every().thursday.at("15:40").do(evening_routine)
    schedule.every().friday.at("15:40").do(evening_routine)

    print("📅 스케줄러 시작!")
    print("  - 08:50: 아침 루틴")
    print("  - 10:00, 14:00: 전략 실행")
    print("  - 15:40: 저녁 루틴")


if __name__ == "__main__":
    setup_schedule()

    # 무한 루프
    while True:
        schedule.run_pending()
        time.sleep(60)  # 1분마다 체크