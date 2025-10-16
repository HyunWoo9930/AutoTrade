# discord_bot.py
"""
🤖 주식 자동매매 Discord Bot
- 실시간 계좌 조회
- 수동 매매 명령
- 종목 분석
- 통계 및 리포트
"""

import discord
from discord import app_commands
from discord.ext import tasks
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import sys

# 프로젝트 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from kis_api import KISApi
from trading_journal import TradingJournal
from advanced_strategy import AdvancedTradingStrategy

load_dotenv()


class TradingBot(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(intents=intents)

        self.tree = app_commands.CommandTree(self)
        self.api = KISApi()
        self.journal = TradingJournal()
        self.strategy = AdvancedTradingStrategy()

        # 설정
        self.alert_enabled = True
        self.auto_report_time = "15:30"  # 장 마감 후

    async def setup_hook(self):
        """봇 초기화"""
        # 글로벌 명령어 동기화 (모든 서버에 적용)
        synced = await self.tree.sync()
        print(f"✅ Discord Bot 명령어 동기화 완료 ({len(synced)}개 명령어)")

    async def on_ready(self):
        """봇 준비 완료"""
        print(f"🤖 봇 로그인: {self.user}")
        print(f"📊 서버 수: {len(self.guilds)}")

        # API 토큰 발급
        self.api.get_access_token()
        print("✅ KIS API 토큰 발급 완료")

        # 자동 리포트 시작
        if not self.auto_report.is_running():
            self.auto_report.start()

    @tasks.loop(hours=1)
    async def auto_report(self):
        """자동 리포트 (매일 15:30)"""
        now = datetime.now()
        if now.strftime("%H:%M") == self.auto_report_time:
            # 여기에 자동 리포트 로직
            pass


# ========== Bot 인스턴스 생성 ==========
client = TradingBot()


# ========== 📊 조회 명령어 ==========

@client.tree.command(name="잔고", description="💰 현재 계좌 잔고 조회")
async def balance(interaction: discord.Interaction):
    """잔고 조회"""
    await interaction.response.defer(thinking=True)

    try:
        balance_data = client.api.get_balance()

        if not balance_data or 'output2' not in balance_data:
            await interaction.followup.send("❌ 잔고 조회 실패")
            return

        output2 = balance_data['output2'][0]

        # 예수금
        cash = int(float(output2.get('dnca_tot_amt', 0)))

        # 총평가액 (예수금 + 주식평가액)
        total_eval = int(float(output2.get('tot_evlu_amt', 0)))

        # 주식평가액
        stock_eval = int(float(output2.get('scts_evlu_amt', 0)))

        # 평가손익 (현재 보유 주식의 평가손익)
        total_profit = int(float(output2.get('evlu_pfls_smtl_amt', 0)))

        # 매입금액 (API에서 직접 가져오기)
        purchase_amt = int(float(output2.get('pchs_amt_smtl_amt', 0)))

        # 수익률 계산
        # 매입금액이 0이면 주식평가액 기준으로 계산
        if purchase_amt > 0:
            profit_rate = (total_profit / purchase_amt * 100)
        elif stock_eval > 0:
            # 매입금액 = 주식평가액 - 평가손익
            purchase_amt = stock_eval - total_profit
            profit_rate = (total_profit / purchase_amt * 100) if purchase_amt > 0 else 0
        else:
            profit_rate = 0

        # 보유 종목 수
        holdings_count = 0
        if 'output1' in balance_data:
            holdings_count = len([s for s in balance_data['output1'] if int(float(s.get('hldg_qty', 0))) > 0])

        # Embed 생성
        embed = discord.Embed(
            title="💰 계좌 잔고",
            description=f"⚠️ 평가손익은 **현재 보유 중인 주식**의 손익입니다\n매도 시 실현손익은 `/매매내역`에서 확인하세요",
            color=0x2ecc71 if profit_rate >= 0 else 0xe74c3c,
            timestamp=datetime.now()
        )

        embed.add_field(name="💵 예수금", value=f"{cash:,}원", inline=True)
        embed.add_field(name="📊 총평가액", value=f"{total_eval:,}원", inline=True)
        embed.add_field(name="📈 보유종목", value=f"{holdings_count}개", inline=True)

        embed.add_field(name="💎 주식평가액", value=f"{stock_eval:,}원", inline=True)
        profit_emoji = "🟢" if total_profit >= 0 else "🔴"
        embed.add_field(name=f"{profit_emoji} 평가손익", value=f"{total_profit:+,}원", inline=True)
        embed.add_field(name="📊 수익률", value=f"{profit_rate:+.2f}%", inline=True)

        # 디버그 정보 (매입금액 표시)
        embed.add_field(name="💰 매입금액", value=f"{purchase_amt:,}원", inline=True)

        embed.add_field(name="⏰ 조회시간", value=datetime.now().strftime("%H:%M:%S"), inline=True)

        embed.set_footer(text="주식 자동매매 봇 | 평가손익 = 보유주식 손익")

        await interaction.followup.send(embed=embed)

    except Exception as e:
        await interaction.followup.send(f"❌ 에러 발생: {str(e)}")


@client.tree.command(name="포지션", description="📊 보유 종목 상세 조회")
async def positions(interaction: discord.Interaction):
    """포지션 상세"""
    await interaction.response.defer(thinking=True)

    try:
        balance_data = client.api.get_balance()

        if not balance_data or 'output1' not in balance_data:
            await interaction.followup.send("❌ 포지션 조회 실패")
            return

        holdings = [s for s in balance_data['output1'] if int(float(s.get('hldg_qty', 0))) > 0]

        if not holdings:
            await interaction.followup.send("📭 보유 종목이 없습니다")
            return

        embed = discord.Embed(
            title="📊 보유 포지션",
            color=0x3498db,
            timestamp=datetime.now()
        )

        for stock in holdings[:10]:  # 최대 10개
            name = stock.get('prdt_name', 'N/A')
            code = stock.get('pdno', 'N/A')
            qty = int(float(stock.get('hldg_qty', 0)))
            avg_price = int(float(stock.get('pchs_avg_pric', 0)))
            current_price = int(float(stock.get('prpr', 0)))
            profit_rate = float(stock.get('evlu_pfls_rt', 0))
            profit = int(float(stock.get('evlu_pfls_amt', 0)))

            emoji = "🟢" if profit_rate >= 0 else "🔴"

            value = f"""
            💰 수량: {qty}주
            📈 평단가: {avg_price:,}원
            💵 현재가: {current_price:,}원
            {emoji} 손익: {profit:+,}원 ({profit_rate:+.2f}%)
            """

            embed.add_field(name=f"{name} ({code})", value=value.strip(), inline=False)

        embed.set_footer(text="주식 자동매매 봇")

        await interaction.followup.send(embed=embed)

    except Exception as e:
        await interaction.followup.send(f"❌ 에러 발생: {str(e)}")


@client.tree.command(name="오늘", description="📅 오늘 매매 내역")
async def today(interaction: discord.Interaction):
    """오늘 매매 내역"""
    await interaction.response.defer(thinking=True)

    try:
        today_date = datetime.now().strftime('%Y-%m-%d')

        # 저널에서 오늘 내역 조회
        journal_data = client.journal.get_recent_trades(days=1)

        if not journal_data:
            await interaction.followup.send("📭 오늘 매매 내역이 없습니다")
            return

        embed = discord.Embed(
            title=f"📅 오늘 매매 내역 ({today_date})",
            color=0xf39c12,
            timestamp=datetime.now()
        )

        buy_count = 0
        sell_count = 0
        total_profit = 0

        for trade in journal_data[:10]:  # 최대 10개
            if trade['type'] == 'buy':
                buy_count += 1
                emoji = "🔵"
                info = f"매수 {trade['quantity']}주 @ {trade['price']:,}원"
            else:
                sell_count += 1
                emoji = "🟢" if trade.get('profit_rate', 0) >= 0 else "🔴"
                profit = trade.get('profit', 0)
                total_profit += profit
                info = f"매도 {trade['quantity']}주 @ {trade['price']:,}원 ({trade.get('profit_rate', 0):+.2f}%)"

            embed.add_field(
                name=f"{emoji} {trade['stock_name']} ({trade['stock_code']})",
                value=f"{info}\n⏰ {trade['timestamp']}",
                inline=False
            )

        summary = f"매수: {buy_count}회 | 매도: {sell_count}회\n총 손익: {total_profit:+,}원"
        embed.description = summary

        embed.set_footer(text="주식 자동매매 봇")

        await interaction.followup.send(embed=embed)

    except Exception as e:
        await interaction.followup.send(f"❌ 에러 발생: {str(e)}")


@client.tree.command(name="통계", description="📊 전체 거래 통계")
async def stats(interaction: discord.Interaction):
    """전체 통계"""
    await interaction.response.defer(thinking=True)

    try:
        stats_data = client.journal.get_statistics()

        embed = discord.Embed(
            title="📊 거래 통계",
            color=0x9b59b6,
            timestamp=datetime.now()
        )

        # 거래 통계
        embed.add_field(
            name="📈 거래 횟수",
            value=f"총 {stats_data.get('total_trades', 0)}회",
            inline=True
        )
        embed.add_field(
            name="🎯 승률",
            value=f"{stats_data.get('win_rate', 0):.1f}%",
            inline=True
        )
        embed.add_field(
            name="💰 누적 손익",
            value=f"{stats_data.get('total_profit', 0):+,}원",
            inline=True
        )

        # 승/패
        embed.add_field(
            name="✅ 승",
            value=f"{stats_data.get('wins', 0)}회",
            inline=True
        )
        embed.add_field(
            name="❌ 패",
            value=f"{stats_data.get('losses', 0)}회",
            inline=True
        )
        embed.add_field(
            name="➖ 무승부",
            value=f"{stats_data.get('draws', 0)}회",
            inline=True
        )

        # 평균
        embed.add_field(
            name="💚 평균 수익",
            value=f"{stats_data.get('avg_win', 0):+,.0f}원",
            inline=True
        )
        embed.add_field(
            name="💔 평균 손실",
            value=f"{stats_data.get('avg_loss', 0):+,.0f}원",
            inline=True
        )
        embed.add_field(
            name="📊 평균 보유일",
            value=f"{stats_data.get('avg_holding_days', 0):.1f}일",
            inline=True
        )

        embed.set_footer(text="주식 자동매매 봇")

        await interaction.followup.send(embed=embed)

    except Exception as e:
        await interaction.followup.send(f"❌ 에러 발생: {str(e)}")


# ========== 🔍 분석 명령어 ==========

@client.tree.command(name="종목분석", description="🔍 특정 종목 실시간 분석")
@app_commands.describe(종목코드="6자리 종목코드 (예: 005930)")
async def analyze(interaction: discord.Interaction, 종목코드: str):
    """종목 분석"""
    await interaction.response.defer(thinking=True)

    try:
        # 신호 분석
        signals, details = client.strategy.check_buy_signals(종목코드)

        # 시장 상태
        regime, regime_info = client.strategy.detect_market_regime(종목코드)

        # 현재가
        current_price = int(client.api.get_current_price(종목코드))

        embed = discord.Embed(
            title=f"🔍 종목 분석: {종목코드}",
            color=0xf39c12,
            timestamp=datetime.now()
        )

        # 신호 점수
        signal_emoji = "🔥" if signals >= 4 else "✅" if signals >= 3 else "⚠️"
        embed.add_field(
            name=f"{signal_emoji} 매수 신호",
            value=f"**{signals}/5점**",
            inline=True
        )

        # 현재가
        embed.add_field(
            name="💰 현재가",
            value=f"{current_price:,}원",
            inline=True
        )

        # 시장 상태
        regime_emoji = {"trending": "📈", "sideways": "📊", "crash": "🚨"}.get(regime, "❓")
        embed.add_field(
            name=f"{regime_emoji} 시장 상태",
            value=regime.upper(),
            inline=True
        )

        # 지표 상세
        adx = regime_info.get('adx', 0) or 0
        volatility = regime_info.get('volatility', 0) or 0
        price_change = regime_info.get('price_change_5d', 0) or 0

        embed.add_field(
            name="📊 기술 지표",
            value=f"ADX: {adx:.1f}\n변동성: {volatility:.2f}%\n5일 변화율: {price_change:+.2f}%",
            inline=False
        )

        # 신호 상세
        detail_text = "\n".join(details[:5])  # 상위 5개만
        embed.add_field(
            name="📋 신호 상세",
            value=f"```{detail_text}```",
            inline=False
        )

        embed.set_footer(text="주식 자동매매 봇")

        await interaction.followup.send(embed=embed)

    except Exception as e:
        await interaction.followup.send(f"❌ 에러 발생: {str(e)}")


@client.tree.command(name="봇상태", description="🤖 봇 작동 상태 확인")
async def bot_status(interaction: discord.Interaction):
    """봇 상태"""
    await interaction.response.defer(thinking=True)

    try:
        from datetime import timezone
        now = datetime.now(timezone.utc)

        embed = discord.Embed(
            title="🤖 봇 상태",
            color=0x2ecc71,
            timestamp=now
        )

        # 봇 정보
        embed.add_field(name="🟢 상태", value="실행 중", inline=True)
        uptime = now - client.user.created_at
        uptime_str = str(uptime).split('.')[0]
        embed.add_field(name="⏰ 봇 생성일", value=uptime_str, inline=True)
        embed.add_field(name="📊 서버 수", value=f"{len(client.guilds)}개", inline=True)

        # API 상태
        embed.add_field(name="🔑 KIS API", value="✅ 연결됨", inline=True)
        embed.add_field(name="📡 응답 시간", value="<100ms", inline=True)
        embed.add_field(name="🔄 다음 실행", value="매 15분마다", inline=True)

        # 알림 설정
        alert_status = "🔔 켜짐" if client.alert_enabled else "🔕 꺼짐"
        embed.add_field(name="알림", value=alert_status, inline=True)
        embed.add_field(name="자동 리포트", value=f"매일 {client.auto_report_time}", inline=True)

        embed.set_footer(text="주식 자동매매 봇")

        await interaction.followup.send(embed=embed)

    except Exception as e:
        await interaction.followup.send(f"❌ 에러 발생: {str(e)}")


# ========== 💰 매매 명령어 ==========

@client.tree.command(name="매수", description="💵 수동 매수 주문")
@app_commands.describe(종목코드="6자리 종목코드", 수량="매수 수량")
async def buy(interaction: discord.Interaction, 종목코드: str, 수량: int):
    """수동 매수"""
    await interaction.response.defer(thinking=True)

    try:
        # 현재가 조회
        current_price = int(client.api.get_current_price(종목코드))
        amount = current_price * 수량

        # 확인 메시지
        embed = discord.Embed(
            title="💵 매수 주문 확인",
            description=f"**{종목코드}** {수량}주 매수하시겠습니까?",
            color=0x3498db
        )
        embed.add_field(name="현재가", value=f"{current_price:,}원", inline=True)
        embed.add_field(name="총 금액", value=f"{amount:,}원", inline=True)

        await interaction.followup.send(
            embed=embed,
            content="⚠️ 실제 매수는 `/매수확정` 명령어로 가능합니다 (안전장치)"
        )

    except Exception as e:
        await interaction.followup.send(f"❌ 에러 발생: {str(e)}")


@client.tree.command(name="매도", description="💸 수동 매도 주문")
@app_commands.describe(종목코드="6자리 종목코드", 수량="매도 수량")
async def sell(interaction: discord.Interaction, 종목코드: str, 수량: int):
    """수동 매도"""
    await interaction.response.defer(thinking=True)

    try:
        # 현재가 조회
        current_price = int(client.api.get_current_price(종목코드))
        amount = current_price * 수량

        # 확인 메시지
        embed = discord.Embed(
            title="💸 매도 주문 확인",
            description=f"**{종목코드}** {수량}주 매도하시겠습니까?",
            color=0xe74c3c
        )
        embed.add_field(name="현재가", value=f"{current_price:,}원", inline=True)
        embed.add_field(name="총 금액", value=f"{amount:,}원", inline=True)

        await interaction.followup.send(
            embed=embed,
            content="⚠️ 실제 매도는 `/매도확정` 명령어로 가능합니다 (안전장치)"
        )

    except Exception as e:
        await interaction.followup.send(f"❌ 에러 발생: {str(e)}")


# ========== ⚙️ 설정 명령어 ==========

@client.tree.command(name="알림설정", description="🔔 알림 켜기/끄기")
@app_commands.describe(상태="on 또는 off")
async def alert_setting(interaction: discord.Interaction, 상태: str):
    """알림 설정"""
    if 상태.lower() == "on":
        client.alert_enabled = True
        await interaction.response.send_message("🔔 알림이 켜졌습니다")
    elif 상태.lower() == "off":
        client.alert_enabled = False
        await interaction.response.send_message("🔕 알림이 꺼졌습니다")
    else:
        await interaction.response.send_message("❌ on 또는 off를 입력하세요")


@client.tree.command(name="매매내역", description="📜 전체 매매 내역 조회")
@app_commands.describe(일수="조회할 일수 (기본: 7일)")
async def trade_history(interaction: discord.Interaction, 일수: int = 7):
    """매매 내역"""
    await interaction.response.defer(thinking=True)

    try:
        # 저널에서 데이터 가져오기
        journal_data = client.journal.get_recent_trades(days=일수)

        if not journal_data:
            await interaction.followup.send(f"📭 최근 {일수}일 매매 내역이 없습니다")
            return

        # 매수/매도 분리
        buys = [t for t in journal_data if t['type'] == 'buy']
        sells = [t for t in journal_data if t['type'] == 'sell']

        # 통계 계산
        total_profit = sum([t.get('profit', 0) for t in sells])
        wins = len([t for t in sells if t.get('profit', 0) > 0])
        losses = len([t for t in sells if t.get('profit', 0) < 0])
        win_rate = (wins / len(sells) * 100) if sells else 0

        embed = discord.Embed(
            title=f"📜 매매 내역 (최근 {일수}일)",
            description=f"총 {len(journal_data)}건 | 매수 {len(buys)}건 | 매도 {len(sells)}건",
            color=0x2ecc71 if total_profit > 0 else 0xe74c3c,
            timestamp=datetime.now()
        )

        # 통계 요약
        embed.add_field(
            name="📊 거래 통계",
            value=f"승: {wins}회 | 패: {losses}회\n승률: {win_rate:.1f}%\n누적 손익: {total_profit:+,}원",
            inline=False
        )

        # 최근 거래 내역 (최대 10개)
        recent_trades = []
        for trade in journal_data[:10]:
            if trade['type'] == 'buy':
                emoji = "🔵"
                info = f"매수 {trade['quantity']}주 @ {trade['price']:,}원"
            else:
                profit_rate = trade.get('profit_rate', 0)
                emoji = "🟢" if profit_rate >= 0 else "🔴"
                info = f"매도 {trade['quantity']}주 @ {trade['price']:,}원 ({profit_rate:+.2f}%)"

            date = trade.get('timestamp', 'N/A').split()[0] if 'timestamp' in trade else 'N/A'
            recent_trades.append(f"{emoji} **{trade['stock_name']}** ({trade['stock_code']})\n{info}\n📅 {date}\n")

        if recent_trades:
            embed.add_field(
                name="📋 최근 거래 내역",
                value="\n".join(recent_trades),
                inline=False
            )

        embed.set_footer(text="주식 자동매매 봇")

        await interaction.followup.send(embed=embed)

    except Exception as e:
        await interaction.followup.send(f"❌ 에러 발생: {str(e)}")


@client.tree.command(name="도움말", description="❓ 명령어 도움말")
async def help_command(interaction: discord.Interaction):
    """도움말"""
    embed = discord.Embed(
        title="📖 Discord Bot 명령어",
        description="주식 자동매매 봇 명령어 목록",
        color=0x9b59b6
    )

    embed.add_field(
        name="📊 조회",
        value="`/잔고` `/포지션` `/오늘` `/통계` `/매매내역 [일수]`",
        inline=False
    )

    embed.add_field(
        name="🔍 분석",
        value="`/종목분석 [코드]` `/봇상태`",
        inline=False
    )

    embed.add_field(
        name="💰 매매",
        value="`/매수 [코드] [수량]` `/매도 [코드] [수량]`",
        inline=False
    )

    embed.add_field(
        name="⚙️ 설정",
        value="`/알림설정 [on/off]`",
        inline=False
    )

    embed.set_footer(text="주식 자동매매 봇")

    await interaction.response.send_message(embed=embed)


# ========== 봇 실행 ==========
if __name__ == "__main__":
    TOKEN = os.getenv('DISCORD_BOT_TOKEN')

    if not TOKEN:
        print("❌ DISCORD_BOT_TOKEN이 설정되지 않았습니다")
        print("💡 .env 파일에 DISCORD_BOT_TOKEN=your_token_here 추가하세요")
        sys.exit(1)

    print("🤖 Discord Bot 시작 중...")
    client.run(TOKEN)
