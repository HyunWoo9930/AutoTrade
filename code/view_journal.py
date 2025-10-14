# view_journal.py
from trading_journal import TradingJournal


def main():
    journal = TradingJournal()

    while True:
        print("\n" + "=" * 60)
        print("📝 매매 일지 메뉴")
        print("=" * 60)
        print("1. 최근 거래 보기")
        print("2. 통계 보기")
        print("3. 엑셀로 내보내기")
        print("4. 종료")

        choice = input("\n선택: ")

        if choice == "1":
            n = input("몇 개 보시겠습니까? (기본 10): ")
            n = int(n) if n.isdigit() else 10
            journal.get_recent_trades(n)

        elif choice == "2":
            journal.get_statistics()

        elif choice == "3":
            filename = input("파일명 (기본 trading_journal.xlsx): ")
            filename = filename if filename else "trading_journal.xlsx"
            journal.export_to_excel(filename)

        elif choice == "4":
            print("\n👋 종료합니다")
            break

        else:
            print("❌ 잘못된 입력입니다")


if __name__ == "__main__":
    main()