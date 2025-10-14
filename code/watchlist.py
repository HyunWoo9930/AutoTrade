# watchlist.py

# ✅ 섹터별 관심 종목 (방어주, 배당주 추가)
WATCHLIST = {
    "대형주": [
        ("005930", "삼성전자"),
        ("000660", "SK하이닉스"),
        ("035420", "NAVER"),
        ("005380", "현대차"),
        ("051910", "LG화학"),
    ],

    "2차전지": [
        ("373220", "LG에너지솔루션"),
        ("006400", "삼성SDI"),
        ("247540", "에코프로비엠"),
        ("086520", "에코프로"),
    ],

    "바이오": [
        ("068270", "셀트리온"),
        ("207940", "삼성바이오로직스"),
        ("326030", "SK바이오팜"),
    ],

    "엔터테인먼트": [
        ("352820", "하이브"),
        ("035900", "JYP Ent."),
        ("041510", "SM"),
    ],

    "IT/플랫폼": [
        ("035720", "카카오"),
        ("036570", "엔씨소프트"),
        ("251270", "넷마블"),
        ("293490", "카카오게임즈"),
    ],

    "금융": [
        ("055550", "신한지주"),
        ("105560", "KB금융"),
        ("086790", "하나금융지주"),
    ],

    "반도체": [
        ("000990", "DB하이텍"),
        ("042700", "한미반도체"),
    ],

    # ✅ 방어주/배당주 추가
    "방어주": [
        ("097950", "CJ제일제당"),      # 식품
        ("271560", "오리온"),           # 식품
        ("000270", "기아"),             # 자동차
    ],

    "배당주": [
        ("033780", "KT&G"),             # 담배 (고배당)
        ("017670", "SK텔레콤"),         # 통신 (안정배당)
        ("000120", "CJ대한통운"),       # 물류
    ]
}


def get_all_stocks():
    """모든 종목을 하나의 리스트로 반환"""
    all_stocks = []
    for sector, stocks in WATCHLIST.items():
        all_stocks.extend(stocks)
    return all_stocks


def get_stocks_by_sector(sector):
    """특정 섹터의 종목만 반환"""
    return WATCHLIST.get(sector, [])


def print_watchlist():
    """관심 종목 출력"""
    print("\n" + "=" * 60)
    print("📋 관심 종목 리스트")
    print("=" * 60)

    for sector, stocks in WATCHLIST.items():
        print(f"\n🏷️  {sector} ({len(stocks)}개)")
        for code, name in stocks:
            print(f"   - {name} ({code})")

    total = sum(len(stocks) for stocks in WATCHLIST.values())
    print(f"\n📊 총 {total}개 종목")


if __name__ == "__main__":
    print_watchlist()