# Discord 채널 구조 가이드

이 프로젝트는 **9개의 Discord 웹훅 채널**을 사용하여 체계적으로 알림을 분류합니다.

## 📋 채널 구조 (9개)

### 1. 매매 채널 (시장별 분리)

#### 🇰🇷 trade-domestic (국내주식 매매)
- 매수 체결
- 매도 체결 (익절/손절)
- 피라미드 추가 매수
- 급락장 긴급 청산
- 매수/매도 실패

**웹훅 설정**: `DISCORD_WEBHOOK_TRADE_DOMESTIC`

#### 🇺🇸 trade-overseas (해외주식 매매)
- 매수 체결 (USD 표시)
- 매도 체결 (익절/손절)
- 피라미드 추가 매수
- 급락장 긴급 청산
- 매수/매도 실패

**웹훅 설정**: `DISCORD_WEBHOOK_TRADE_OVERSEAS`

---

### 2. 신호 채널 (시장별 분리)

#### 📊 signal-domestic (국내주식 신호)
- 강한 매수 신호 (4+/5)
- 보통 신호 (3/5)
- 보유 현황 (±5% 이상)
- 전략 메시지

**웹훅 설정**: `DISCORD_WEBHOOK_SIGNAL_DOMESTIC`

#### 📊 signal-overseas (해외주식 신호)
- 강한 매수 신호 (4+/5)
- 보통 신호 (3/5)
- 보유 현황 (±5% 이상)
- 전략 메시지

**웹훅 설정**: `DISCORD_WEBHOOK_SIGNAL_OVERSEAS`

---

### 3. 시장 현황 채널 (시장별 분리)

#### 🌅 market-domestic (국내 시장 현황)
- 아침 루틴 (장 시작 전 점검)
- 저녁 루틴 (장 마감 후 정리)
- 시장 상태 알림 (급락장 등)

**웹훅 설정**: `DISCORD_WEBHOOK_MARKET_DOMESTIC`

#### 🌅 market-overseas (해외 시장 현황)
- 아침 루틴 (미국 장 시작 전)
- 저녁 루틴 (미국 장 마감 후)
- 시장 상태 알림 (급락장 등)

**웹훅 설정**: `DISCORD_WEBHOOK_MARKET_OVERSEAS`

---

### 4. 공통 채널

#### 📊 report (일일 리포트)
- 일일 매매 결과
- 거래 통계
- 손익 분석
- 계좌 현황

**웹훅 설정**: `DISCORD_WEBHOOK_REPORT`

#### 🤖 system-trading (봇 시작/종료/에러)
- 스크립트 시작 알림
- 스크립트 종료 알림 (성공률, 실행시간)
- 에러 발생 알림
- 시스템 메시지

**웹훅 설정**: `DISCORD_WEBHOOK_SYSTEM_TRADING`

#### 🚀 system-deploy (배포 알림)
- GitHub Actions 배포 성공
- GitHub Actions 배포 실패
- 서버 배포 상태

**웹훅 설정**: `DISCORD_WEBHOOK_SYSTEM_DEPLOY`

---

## 🔧 환경 변수 설정

`.env` 파일에 다음 웹훅을 추가하세요:

```bash
# 매매 채널 (시장별)
DISCORD_WEBHOOK_TRADE_DOMESTIC=https://discord.com/api/webhooks/...
DISCORD_WEBHOOK_TRADE_OVERSEAS=https://discord.com/api/webhooks/...

# 신호 채널 (시장별)
DISCORD_WEBHOOK_SIGNAL_DOMESTIC=https://discord.com/api/webhooks/...
DISCORD_WEBHOOK_SIGNAL_OVERSEAS=https://discord.com/api/webhooks/...

# 시장 현황 채널 (시장별)
DISCORD_WEBHOOK_MARKET_DOMESTIC=https://discord.com/api/webhooks/...
DISCORD_WEBHOOK_MARKET_OVERSEAS=https://discord.com/api/webhooks/...

# 공통 채널
DISCORD_WEBHOOK_REPORT=https://discord.com/api/webhooks/...
DISCORD_WEBHOOK_SYSTEM_TRADING=https://discord.com/api/webhooks/...
DISCORD_WEBHOOK_SYSTEM_DEPLOY=https://discord.com/api/webhooks/...
```

---

## 💡 Kubernetes Secret 설정

```bash
kubectl create secret generic stock-trading-secret \
  --from-literal=DISCORD_WEBHOOK_TRADE_DOMESTIC=your_webhook_url \
  --from-literal=DISCORD_WEBHOOK_TRADE_OVERSEAS=your_webhook_url \
  --from-literal=DISCORD_WEBHOOK_SIGNAL_DOMESTIC=your_webhook_url \
  --from-literal=DISCORD_WEBHOOK_SIGNAL_OVERSEAS=your_webhook_url \
  --from-literal=DISCORD_WEBHOOK_MARKET_DOMESTIC=your_webhook_url \
  --from-literal=DISCORD_WEBHOOK_MARKET_OVERSEAS=your_webhook_url \
  --from-literal=DISCORD_WEBHOOK_REPORT=your_webhook_url \
  --from-literal=DISCORD_WEBHOOK_SYSTEM_TRADING=your_webhook_url \
  --from-literal=DISCORD_WEBHOOK_SYSTEM_DEPLOY=your_webhook_url \
  --from-literal=KIS_APP_KEY=your_app_key \
  --from-literal=KIS_APP_SECRET=your_app_secret \
  --from-literal=KIS_ACCOUNT_NO=your_account_no \
  --from-literal=DISCORD_BOT_TOKEN=your_bot_token
```

---

## 📱 사용 예시

### 국내주식 전략
```python
from discord.discord_notifier import DiscordNotifier

# 국내주식용 notifier
notifier = DiscordNotifier(market='domestic')

# 매수 알림 → trade-domestic 채널로 전송
notifier.notify_buy("삼성전자", "005930", 10, 90000)

# 신호 알림 → signal-domestic 채널로 전송
notifier.notify_signal_strong("삼성전자", "005930", 5, details, 90000)

# 아침 루틴 → market-domestic 채널로 전송
notifier.notify_morning(stock_count=25, top_stocks=[...])
```

### 해외주식 전략
```python
from discord.discord_notifier import DiscordNotifier

# 해외주식용 notifier
notifier = DiscordNotifier(market='overseas')

# 매수 알림 → trade-overseas 채널로 전송 (USD 표시)
notifier.notify_buy("Apple", "AAPL", 5, 180.50)

# 신호 알림 → signal-overseas 채널로 전송
notifier.notify_signal_strong("Apple", "AAPL", 5, details, 180.50)

# 아침 루틴 → market-overseas 채널로 전송
notifier.notify_morning(stock_count=49, top_stocks=[...])
```

---

## 🎨 채널별 색상 및 아이콘

| 채널 | 색상 | 주요 아이콘 |
|------|------|-------------|
| trade-domestic | 파란색 (매수), 녹색/빨간색 (매도) | 🇰🇷 🔵 🟢 🔴 |
| trade-overseas | 파란색 (매수), 녹색/빨간색 (매도) | 🇺🇸 🔵 🟢 🔴 |
| signal-domestic | 주황색 (강한 신호), 회색 (보통) | 🇰🇷 🎯 ⚠️ |
| signal-overseas | 주황색 (강한 신호), 회색 (보통) | 🇺🇸 🎯 ⚠️ |
| market-domestic | 주황색 (아침), 보라색 (저녁) | 🇰🇷 🌅 🌙 |
| market-overseas | 주황색 (아침), 보라색 (저녁) | 🇺🇸 🌅 🌙 |
| report | 녹색 (수익), 빨간색 (손실) | 📊 |
| system-trading | 녹색 (시작/종료), 빨간색 (에러) | 🤖 🚀 ✅ 🚨 |
| system-deploy | 녹색 (성공), 빨간색 (실패) | 🚀 ✅ ❌ |

---

## 📌 주요 특징

1. **시장별 분리**: 국내주식과 해외주식 알림이 완전히 분리되어 있습니다.
2. **통화 자동 표시**: 국내는 `원`, 해외는 `$`로 자동 표시됩니다.
3. **국기 이모지**: 각 알림에 🇰🇷 또는 🇺🇸 표시로 한눈에 구분 가능합니다.
4. **배포 분리**: 시스템 운영 알림과 배포 알림이 분리되어 있습니다.

---

## 🔄 마이그레이션 가이드 (기존 5채널 → 신규 9채널)

### 기존 설정 (5개)
```bash
DISCORD_WEBHOOK_SYSTEM      # → DISCORD_WEBHOOK_SYSTEM_TRADING + DISCORD_WEBHOOK_SYSTEM_DEPLOY
DISCORD_WEBHOOK_TRADE       # → DISCORD_WEBHOOK_TRADE_DOMESTIC + DISCORD_WEBHOOK_TRADE_OVERSEAS
DISCORD_WEBHOOK_SIGNAL      # → DISCORD_WEBHOOK_SIGNAL_DOMESTIC + DISCORD_WEBHOOK_SIGNAL_OVERSEAS
DISCORD_WEBHOOK_MARKET      # → DISCORD_WEBHOOK_MARKET_DOMESTIC + DISCORD_WEBHOOK_MARKET_OVERSEAS
DISCORD_WEBHOOK_REPORT      # → 유지 (변경 없음)
```

### 마이그레이션 단계
1. Discord 서버에 4개의 새 채널 생성
2. 각 채널의 웹훅 URL 복사
3. `.env` 파일 업데이트 (9개 웹훅)
4. Kubernetes Secret 재생성
5. 배포 및 테스트

---

## 🧪 테스트

```bash
# 테스트 스크립트 (국내)
python -c "
from discord.discord_notifier import DiscordNotifier
notifier = DiscordNotifier(market='domestic')
notifier.notify_start('test.py')
"

# 테스트 스크립트 (해외)
python -c "
from discord.discord_notifier import DiscordNotifier
notifier = DiscordNotifier(market='overseas')
notifier.notify_start('test_overseas.py')
"
```

---

## 🙋 문의

채널 구조나 설정에 문제가 있으면 GitHub Issues로 문의하세요!
