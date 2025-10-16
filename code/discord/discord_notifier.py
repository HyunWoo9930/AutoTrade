# discord_notifier.py
import os
from dotenv import load_dotenv
import requests
from datetime import datetime

load_dotenv()


class DiscordNotifier:
    def __init__(self, market='domestic'):
        """
        Discord 알림 클래스

        Args:
            market: 'domestic' (국내주식) 또는 'overseas' (해외주식)
        """
        self.market = market

        # 9개 웹훅 채널 (시장별 분리)
        self.webhooks = {
            # 매매 채널 (시장별)
            'trade-domestic': os.getenv('DISCORD_WEBHOOK_TRADE_DOMESTIC'),
            'trade-overseas': os.getenv('DISCORD_WEBHOOK_TRADE_OVERSEAS'),

            # 신호 채널 (시장별)
            'signal-domestic': os.getenv('DISCORD_WEBHOOK_SIGNAL_DOMESTIC'),
            'signal-overseas': os.getenv('DISCORD_WEBHOOK_SIGNAL_OVERSEAS'),

            # 시장 현황 채널 (시장별)
            'market-domestic': os.getenv('DISCORD_WEBHOOK_MARKET_DOMESTIC'),
            'market-overseas': os.getenv('DISCORD_WEBHOOK_MARKET_OVERSEAS'),

            # 공통 채널
            'report': os.getenv('DISCORD_WEBHOOK_REPORT'),
            'system-trading': os.getenv('DISCORD_WEBHOOK_SYSTEM_TRADING'),
            'system-deploy': os.getenv('DISCORD_WEBHOOK_SYSTEM_DEPLOY')
        }

        # 웹훅 설정 확인
        missing = [k for k, v in self.webhooks.items() if not v]
        if missing:
            print(f"⚠️ 설정되지 않은 웹훅: {', '.join(missing)}")

    def _get_channel(self, base_channel):
        """시장에 따라 적절한 채널 반환"""
        if base_channel in ['trade', 'signal', 'market']:
            return f"{base_channel}-{self.market}"
        return base_channel

    def _send(self, channel, message, color=0x3498db, title=None):
        """디스코드 메시지 전송"""
        webhook_url = self.webhooks.get(channel)

        if not webhook_url:
            print(f"⚠️ {channel} 웹훅 없음")
            return False

        try:
            embed = {
                "description": message,
                "color": color,
                "timestamp": datetime.utcnow().isoformat(),
                "footer": {"text": "주식 자동매매 봇"}
            }

            if title:
                embed["title"] = title

            data = {"embeds": [embed]}
            response = requests.post(webhook_url, json=data, timeout=10)

            return response.status_code == 204

        except Exception as e:
            print(f"❌ 디스코드 전송 실패 ({channel}): {e}")
            return False

    # ========== 시스템 알림 (system-trading 채널) ==========

    def notify_start(self, script_name):
        """스크립트 시작"""
        market_emoji = "🇰🇷" if self.market == 'domestic' else "🇺🇸"
        msg = f"""
🚀 **시스템 시작**

{market_emoji} 시장: {self.market.upper()}
📝 스크립트: `{script_name}`
⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        self._send('system-trading', msg, 0x2ecc71, "🚀 시작")

    def notify_end(self, script_name, success, total, duration):
        """스크립트 종료"""
        market_emoji = "🇰🇷" if self.market == 'domestic' else "🇺🇸"
        rate = (success / total * 100) if total > 0 else 0
        msg = f"""
✅ **시스템 종료**

{market_emoji} 시장: {self.market.upper()}
📝 스크립트: `{script_name}`
📊 성공: {success}/{total} ({rate:.1f}%)
⏱️ 실행시간: {duration:.1f}초
⏰ {datetime.now().strftime('%H:%M:%S')}
"""
        color = 0x2ecc71 if rate > 80 else 0xe67e22
        self._send('system-trading', msg, color, "✅ 종료")

    def notify_error(self, location, error):
        """에러 발생"""
        market_emoji = "🇰🇷" if self.market == 'domestic' else "🇺🇸"
        msg = f"""
🚨 **에러 발생**

{market_emoji} 시장: {self.market.upper()}
📍 위치: `{location}`
⚠️ 에러: {error}
⏰ {datetime.now().strftime('%H:%M:%S')}
"""
        self._send('system-trading', msg, 0xe74c3c, "🚨 에러")

    # ========== 매매 알림 (trade-domestic/overseas 채널) ==========

    def notify_buy(self, name, code, qty, price):
        """매수 체결"""
        amount = int(price) * qty
        market_emoji = "🇰🇷" if self.market == 'domestic' else "🇺🇸"
        currency = "원" if self.market == 'domestic' else "$"
        msg = f"""
🔵 **매수 체결**

{market_emoji} **{name}** (`{code}`)
💰 {qty}주 × {price:,}{currency}
💵 총 {amount:,}{currency}

⏰ {datetime.now().strftime('%H:%M:%S')}
"""
        self._send(self._get_channel('trade'), msg, 0x3498db, "🔵 매수")

    def notify_sell(self, name, code, qty, price, profit_rate):
        """매도 체결"""
        amount = int(price) * qty
        profit = int(amount * profit_rate / 100)
        emoji = "🟢" if profit_rate > 0 else "🔴"
        color = 0x2ecc71 if profit_rate > 0 else 0xe74c3c
        title = "🟢 익절" if profit_rate > 0 else "🔴 손절"
        market_emoji = "🇰🇷" if self.market == 'domestic' else "🇺🇸"
        currency = "원" if self.market == 'domestic' else "$"

        msg = f"""
{emoji} **매도 체결**

{market_emoji} **{name}** (`{code}`)
💰 {qty}주 × {price:,}{currency}
💵 총 {amount:,}{currency}

📈 수익률: **{profit_rate:+.2f}%**
💸 손익: **{profit:+,}{currency}**

⏰ {datetime.now().strftime('%H:%M:%S')}
"""
        self._send(self._get_channel('trade'), msg, color, title)

    def notify_buy_failed(self, name, code, reason):
        """매수 실패"""
        market_emoji = "🇰🇷" if self.market == 'domestic' else "🇺🇸"
        msg = f"""
❌ **매수 실패**

{market_emoji} **{name}** (`{code}`)
⚠️ 실패 원인: {reason}

⏰ {datetime.now().strftime('%H:%M:%S')}
"""
        self._send(self._get_channel('trade'), msg, 0xe74c3c, "❌ 매수 실패")

    def notify_sell_failed(self, name, code, reason):
        """매도 실패"""
        market_emoji = "🇰🇷" if self.market == 'domestic' else "🇺🇸"
        msg = f"""
❌ **매도 실패**

{market_emoji} **{name}** (`{code}`)
⚠️ 실패 원인: {reason}

⏰ {datetime.now().strftime('%H:%M:%S')}
"""
        self._send(self._get_channel('trade'), msg, 0xe74c3c, "❌ 매도 실패")

    # ========== 신호 분석 (signal-domestic/overseas 채널) ==========

    def notify_signal_strong(self, name, code, signals, details, price):
        """강한 매수 신호"""
        detail_text = "\n".join([f"  {d}" for d in details])
        market_emoji = "🇰🇷" if self.market == 'domestic' else "🇺🇸"
        currency = "원" if self.market == 'domestic' else "$"
        msg = f"""
🎯 **강한 매수 신호!**

{market_emoji} **{name}** (`{code}`)
💰 현재가: {price:,}{currency}
⭐ 신호: **{signals}/5**

{detail_text}

⏰ {datetime.now().strftime('%H:%M:%S')}
"""
        self._send(self._get_channel('signal'), msg, 0xf39c12, "🎯 강한 신호")

    def notify_signal_weak(self, name, code, signals):
        """보통 신호"""
        market_emoji = "🇰🇷" if self.market == 'domestic' else "🇺🇸"
        msg = f"""
⚠️ **보통 신호**

{market_emoji} {name} (`{code}`)
⭐ {signals}/5

조심스러운 진입 구간
"""
        self._send(self._get_channel('signal'), msg, 0x95a5a6)

    def notify_holding(self, name, code, qty, profit_rate):
        """보유 현황 (±5% 이상만)"""
        emoji = "📈" if profit_rate >= 0 else "📉"
        market_emoji = "🇰🇷" if self.market == 'domestic' else "🇺🇸"
        msg = f"""
{emoji} **보유 중**

{market_emoji} {name} ({code})
🔢 {qty}주
📊 수익률: {profit_rate:+.2f}%

목표: +10%(1차), +20%(2차)
손절: -5%
"""
        self._send(self._get_channel('signal'), msg, 0x3498db)

    # ========== 시장 현황 (market-domestic/overseas 채널) ==========

    def notify_morning(self, stock_count, top_stocks=None):
        """아침 루틴 - 주요 종목 현황 포함"""
        market_emoji = "🇰🇷" if self.market == 'domestic' else "🇺🇸"
        currency = "원" if self.market == 'domestic' else "$"
        msg = f"""
    🌅 **장 시작 전 점검**

    {market_emoji} 시장: {self.market.upper()}
    📊 감시 종목: **{stock_count}개**
    ⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    """

        # 주요 종목 현황 추가
        if top_stocks:
            msg += "\n**💎 주요 종목 현황**\n"
            for name, code, price in top_stocks[:10]:  # 상위 10개만
                msg += f"  • {name} (`{code}`): {price:,}{currency}\n"

        msg += "\n오늘도 안전한 매매 되세요! 💪"

        self._send(self._get_channel('market'), msg, 0xf39c12, "🌅 아침 루틴")

    def notify_evening(self, cash, holdings_list, total):
        """저녁 루틴 - 보유 종목 상세 정보 포함"""
        holdings_count = len(holdings_list) if holdings_list else 0
        market_emoji = "🇰🇷" if self.market == 'domestic' else "🇺🇸"
        currency = "원" if self.market == 'domestic' else "$"

        msg = f"""
    🌙 **장 마감 후 정리**

    {market_emoji} 시장: {self.market.upper()}
    💰 예수금: **{cash:,}{currency}**
    📊 보유: **{holdings_count}개 종목**
    📈 평가금액: **{total:,}{currency}**
    """

        # 보유 종목 상세
        if holdings_list:
            msg += "\n**📌 보유 종목**\n"
            for item in holdings_list:
                name = item.get('name', 'N/A')
                qty = item.get('qty', 0)
                avg_price = item.get('avg_price', 0)
                current_price = item.get('current_price', 0)
                profit_rate = item.get('profit_rate', 0)
                emoji = "🟢" if profit_rate >= 0 else "🔴"

                msg += f"  {emoji} {name}: {qty}주 ({profit_rate:+.2f}%)\n"
                msg += f"      매수: {avg_price:,}{currency} → 현재: {current_price:,}{currency}\n"
        else:
            msg += "\n보유 종목이 없습니다.\n"

        msg += f"\n⏰ {datetime.now().strftime('%H:%M:%S')}"

        self._send(self._get_channel('market'), msg, 0x9b59b6, "🌙 저녁 루틴")

    # ========== 일일 리포트 (report 채널) ==========

    def notify_daily_report(self, stats):
        """일일 리포트"""
        msg = f"""
📊 **오늘의 매매 결과**

**거래 통계**
  • 매수: {stats.get('buys', 0)}회
  • 매도: {stats.get('sells', 0)}회
  • 승: {stats.get('wins', 0)}회 | 패: {stats.get('losses', 0)}회
  • 승률: {stats.get('win_rate', 0):.1f}%

**손익 분석**
  • 총 손익: {stats.get('profit', 0):+,}원
  • 평균 수익: {stats.get('avg_win', 0):+,.0f}원
  • 평균 손실: {stats.get('avg_loss', 0):+,.0f}원

**계좌 현황**
  • 예수금: {stats.get('cash', 0):,}원
  • 평가액: {stats.get('stocks', 0):,}원
  • 총자산: {stats.get('total', 0):,}원

⏰ {datetime.now().strftime('%Y-%m-%d')}
"""
        color = 0x2ecc71 if stats.get('profit', 0) > 0 else 0xe74c3c
        self._send('report', msg, color, "📊 일일 리포트")

    # ========== 시장 상태 알림 (market-domestic/overseas 채널) ==========

    def notify_market_regime(self, stock_name, code, regime, regime_info):
        """시장 상태 감지 알림"""
        regime_emoji = {
            "trending": "📈",
            "sideways": "📊",
            "crash": "🚨",
            "unknown": "❓"
        }
        regime_color = {
            "trending": 0x2ecc71,
            "sideways": 0xf39c12,
            "crash": 0xe74c3c,
            "unknown": 0x95a5a6
        }

        emoji = regime_emoji.get(regime, "❓")
        color = regime_color.get(regime, 0x95a5a6)
        market_emoji = "🇰🇷" if self.market == 'domestic' else "🇺🇸"

        # None 값을 안전하게 처리
        adx = regime_info.get('adx', 0) or 0
        price_change_5d = regime_info.get('price_change_5d', 0) or 0
        volatility = regime_info.get('volatility', 0) or 0

        msg = f"""
{emoji} **시장 상태: {regime.upper()}**

{market_emoji} {stock_name} (`{code}`)

**지표**
  • ADX: {adx:.1f}
  • 5일 변화율: {price_change_5d:.2f}%
  • 변동성: {volatility:.2f}%

⏰ {datetime.now().strftime('%H:%M:%S')}
"""
        self._send(self._get_channel('market'), msg, color, f"{emoji} 시장 상태")

    def notify_pyramid_buy(self, stock_name, code, qty, price, phase="2차"):
        """피라미드 추가 매수 알림"""
        amount = int(price) * qty
        market_emoji = "🇰🇷" if self.market == 'domestic' else "🇺🇸"
        currency = "원" if self.market == 'domestic' else "$"
        msg = f"""
📈 **피라미드 매수 ({phase})**

{market_emoji} **{stock_name}** (`{code}`)
💰 {qty}주 × {price:,}{currency}
💵 총 {amount:,}{currency}

✅ 수익 확인 후 추가 진입
📊 평균 단가 재조정

⏰ {datetime.now().strftime('%H:%M:%S')}
"""
        self._send(self._get_channel('trade'), msg, 0x3498db, f"📈 추가매수 ({phase})")

    def notify_crash_protection(self, stock_name, code, qty, price, profit_rate):
        """급락장 긴급 청산 알림"""
        amount = int(price) * qty
        profit = int(amount * profit_rate / 100)
        market_emoji = "🇰🇷" if self.market == 'domestic' else "🇺🇸"
        currency = "원" if self.market == 'domestic' else "$"

        msg = f"""
🚨 **급락장 긴급 청산!**

{market_emoji} **{stock_name}** (`{code}`)
💰 {qty}주 × {price:,}{currency}
💵 총 {amount:,}{currency}

📉 수익률: **{profit_rate:+.2f}%**
💸 손익: **{profit:+,}{currency}**

⚠️ 급락장 감지로 인한 보호 매도

⏰ {datetime.now().strftime('%H:%M:%S')}
"""
        self._send(self._get_channel('trade'), msg, 0xe74c3c, "🚨 긴급 청산")

    # ========== 기존 호환성 메서드 ==========

    def notify_strategy(self, title, message):
        """기존 코드 호환용"""
        self._send(self._get_channel('signal'), f"**{title}**\n\n{message}", 0x9b59b6)

    def notify_system(self, title, message):
        """시스템 알림 (간단한 메시지용)"""
        msg = f"""
**{title}**

{message}

⏰ {datetime.now().strftime('%H:%M:%S')}
"""
        self._send('system-trading', msg, 0x3498db)


# discord_notifier.py 맨 아래 테스트 부분
if __name__ == "__main__":
    notifier = DiscordNotifier()

    print("\n테스트 시작...\n")

    import time

    # ... (기존 테스트들)

    # 2. 아침 루틴 (주요 종목 포함)
    print("2️⃣ 아침 루틴 테스트...")
    notifier.notify_morning(
        stock_count=25,
        top_stocks=[
            ("삼성전자", "005930", 90000),
            ("SK하이닉스", "000660", 125000),
            ("NAVER", "035420", 180000),
            ("카카오", "035720", 45000),
            ("현대차", "005380", 250000),
        ]
    )
    time.sleep(1)

    # ... (중간 테스트들)

    # 7. 저녁 루틴 (보유 종목 상세 포함)
    print("7️⃣ 저녁 루틴 테스트...")
    notifier.notify_evening(
        cash=29500000,
        holdings_list=[
            {
                'name': '삼성전자',
                'code': '005930',
                'qty': 10,
                'avg_price': 88000,
                'current_price': 90000,
                'profit_rate': 2.27
            },
            {
                'name': 'SK하이닉스',
                'code': '000660',
                'qty': 5,
                'avg_price': 130000,
                'current_price': 125000,
                'profit_rate': -3.85
            },
            {
                'name': 'NAVER',
                'code': '035420',
                'qty': 3,
                'avg_price': 175000,
                'current_price': 180000,
                'profit_rate': 2.86
            }
        ],
        total=30500000
    )
    time.sleep(1)

    print("\n✅ 테스트 완료!")
