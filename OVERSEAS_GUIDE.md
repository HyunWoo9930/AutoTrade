# 해외주식 트레이딩 가이드

## 🇺🇸 개요

국내주식과 동일한 **9가지 고급 전략**을 미국 주식에 적용합니다.

---

## 📁 파일 구조

```
code/
├─ kis_api.py                # KIS API (국내 + 해외 메서드 추가)
├─ watchlist.py              # 국내주식 워치리스트
├─ watchlist_us.py           # 🆕 해외주식 워치리스트
├─ advanced_strategy.py      # 국내주식 전략
├─ overseas_strategy.py      # 🆕 해외주식 전략
└─ test_overseas.py          # 🆕 해외주식 테스트
```

---

## 🎯 9가지 전략 (국내 = 해외)

### 1. 급락장 차등 청산
- 수익 중 (≥8%): 50%만 청산
- 손실/소폭 수익: 전량 청산

### 2. 동시 보유 종목 수 제한
- 최대 15개 (공격적 설정)

### 3. 추세 반전 감지
- MA5 < MA20 (데드크로스) → 익절

### 4. 섹터 분산 관리
- 섹터당 30% 한도 (공격적)

### 5. 트레일링 스탑
- +15% 이상 도달 후
- 최고점 대비 -3% 하락 시 매도

### 6. 매수 타이밍 최적화
- 국내: 9시대, 15시대 회피
- 해외: 장 시작/마감 시간대 회피

### 7. 익절 후 재진입 금지
- 당일 익절 종목 재매수 방지

### 8. 신호 가중치 적용
- MA: 2.0 (가장 중요)
- MACD/Volume: 1.5
- RSI/BB: 1.0
- 총점 → 5점 만점 정규화

### 9. 변동성 기반 손절 조정
- ATR 기반 동적 손절
- 낮은 변동성: 타이트한 손절 (-4%)
- 높은 변동성: 넓은 손절 (-7.5%)

---

## 📊 워치리스트 (49개 종목)

### 빅테크 (6개)
- Apple (AAPL)
- Microsoft (MSFT)
- Alphabet (GOOGL)
- Amazon (AMZN)
- Meta (META)
- NVIDIA (NVDA)

### 반도체 (5개)
- TSMC (TSM)
- Broadcom (AVGO)
- AMD (AMD)
- Qualcomm (QCOM)
- Intel (INTC)

### 전기차 (3개)
- Tesla (TSLA)
- Rivian (RIVN)
- Lucid (LCID)

### 금융 (4개)
- JPMorgan Chase (JPM)
- Bank of America (BAC)
- Wells Fargo (WFC)
- Goldman Sachs (GS)

### 헬스케어 (4개)
- Johnson & Johnson (JNJ)
- UnitedHealth (UNH)
- Pfizer (PFE)
- AbbVie (ABBV)

### AI/클라우드 (4개)
- Salesforce (CRM)
- Oracle (ORCL)
- Palantir (PLTR)
- Snowflake (SNOW)

### 소비재 (4개)
- Coca-Cola (KO)
- PepsiCo (PEP)
- Nike (NKE)
- Starbucks (SBUX)

### ETF (3개)
- S&P 500 ETF (SPY)
- NASDAQ-100 ETF (QQQ)
- Dow Jones ETF (DIA)

---

## 🚀 사용 방법

### 1. 워치리스트 확인

```bash
python3 code/watchlist_us.py
```

### 2. 테스트 실행

```bash
# 빅테크 3개 종목 테스트
python3 code/test_overseas.py
```

### 3. 전체 종목 실행

```python
from overseas_strategy import OverseasTradingStrategy
from watchlist_us import get_all_us_stocks

strategy = OverseasTradingStrategy()
watchlist = get_all_us_stocks()

for ticker, name, exchange in watchlist:
    strategy.execute_strategy(ticker, name, exchange)
```

---

## 🔧 커스터마이징

### 워치리스트 수정

`code/watchlist_us.py` 파일 수정:

```python
WATCHLIST_US = {
    "빅테크": [
        ("AAPL", "Apple", "NAS"),
        ("TSLA", "Tesla", "NAS"),  # 추가
    ],
}
```

### 초기 자본 변경

`overseas_strategy.py`의 `_execute_buy()` 메서드:

```python
# 기본: $10,000
total_balance_usd = cash_usd + 10000

# 변경: $50,000
total_balance_usd = cash_usd + 50000
```

### 신호 임계치 변경

`overseas_strategy.py`의 `execute_strategy()` 메서드:

```python
# 현재 (공격적):
if signals >= 2:  # 추세장
if signals >= 2:  # 횡보장

# 보수적으로 변경:
if signals >= 3:  # 추세장
if signals >= 4:  # 횡보장
```

---

## ⏰ 장 시간

### 미국 장 시간 (EST)
- 프리마켓: 04:00~09:30
- 정규장: 09:30~16:00
- 애프터마켓: 16:00~20:00

### 한국 시간 (KST 기준)
- 프리마켓: 18:00~23:30
- 정규장: **23:30~06:00** (다음날)
- 애프터마켓: 06:00~10:00

**최적 매수 시간**: 00:30~05:00 (장 초반/마감 회피)

---

## 💱 통화 및 환전

### USD 잔고 확인

```python
balance = api.get_overseas_balance()
cash_usd = float(balance['output2'][0].get('frcr_dncl_amt_2', 0))
print(f"USD 잔고: ${cash_usd:,.2f}")
```

### 환율 고려사항

- 모든 거래는 USD로 진행
- 손익률 계산도 USD 기준
- 원화 환산 필요 시: `usd * 1300` (대략)

---

## 📈 전략 비교: 국내 vs 해외

| 항목 | 국내주식 | 해외주식 |
|------|---------|---------|
| 전략 | 9가지 고급 전략 | 9가지 고급 전략 (동일) |
| 시장 | 코스피/코스닥 | 나스닥/NYSE/AMEX |
| 통화 | KRW | USD |
| 장 시간 | 09:00~15:30 | 23:30~06:00 (KST) |
| 보유 한도 | 15개 | 15개 |
| 섹터 한도 | 30% | 30% |
| 신호 임계치 | 2개 (공격적) | 2개 (공격적) |
| API 경로 | `/domestic-stock/` | `/overseas-stock/` |

---

## 🔍 API 차이점

### 국내주식 API

```python
# 현재가
api.get_current_price(stock_code)

# 매수
api.buy_stock(stock_code, quantity)

# 잔고
api.get_balance()
```

### 해외주식 API

```python
# 현재가
api.get_overseas_current_price(ticker, exchange="NAS")

# 매수
api.buy_overseas_stock(ticker, quantity, exchange="NASD")

# 잔고
api.get_overseas_balance()
```

**거래소 코드:**
- 나스닥: `"NAS"` (현재가), `"NASD"` (거래)
- 뉴욕: `"NYSE"` (현재가/거래 동일)
- 아멕스: `"AMS"` (현재가), `"AMEX"` (거래)

---

## 🧪 테스트 예시

### 단일 종목 (Apple)

```bash
python3 -c "
from overseas_strategy import OverseasTradingStrategy
strategy = OverseasTradingStrategy()
strategy.execute_strategy('AAPL', 'Apple', 'NAS')
"
```

### 섹터별 (빅테크)

```bash
python3 -c "
from overseas_strategy import OverseasTradingStrategy
from watchlist_us import get_us_stocks_by_sector

strategy = OverseasTradingStrategy()
for ticker, name, exchange in get_us_stocks_by_sector('빅테크'):
    strategy.execute_strategy(ticker, name, exchange)
"
```

---

## ⚠️ 주의사항

### 1. API 제한

- KIS API는 분당 호출 제한 있음 (초당 2회)
- 전체 49개 종목 실행 시 약 25분 소요

### 2. 시차

- 한국 밤 시간 = 미국 낮 시간
- 미국 장이 열릴 때 국내 장은 닫혀 있음
- **24시간 자동매매 가능!**

### 3. 환율 변동

- USD/KRW 환율 변동 리스크
- 원화 평가 시 환차익/환차손 고려

### 4. 세금

- 해외주식 양도소득세: 22% (250만원 공제)
- 배당 소득세: 15%

---

## 🚀 실전 배포

### Docker 이미지 빌드

```bash
# Dockerfile에 해외주식 코드 추가
docker build -t stock-trading-overseas:latest .
docker push your-registry/stock-trading-overseas:latest
```

### K8s CronJob 설정

```yaml
# overseas-cronjob.yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: overseas-trading
spec:
  schedule: "30 0 * * 2-6"  # 화-토 00:30 (미국 장 시작)
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: overseas-trading
            image: your-registry/stock-trading-overseas:latest
            command: ["python3", "code/overseas_strategy.py"]
```

### 이중 전략 운영

**아침 (09:00)**: 국내주식 전략 실행
**밤 (00:30)**: 해외주식 전략 실행

```yaml
# 국내주식 CronJob
schedule: "0 9 * * 1-5"  # 월-금 09:00

# 해외주식 CronJob
schedule: "30 0 * * 2-6"  # 화-토 00:30
```

---

## 📊 예상 성과

### 거래 빈도 (공격적 설정)

- **국내주식**: 30일 기준 5~10건 예상
- **해외주식**: 30일 기준 10~20건 예상 (변동성 큼)
- **합계**: 월 15~30건

### 포트폴리오 구성

```
전체 자본: 5,000만원

국내주식: 3,000만원 (60%)
- 코스피/코스닥 15개 종목

해외주식: 2,000만원 (40%)
- 나스닥/NYSE 15개 종목

→ 최대 30개 종목 동시 보유
```

---

## 🎯 백테스팅

해외주식 백테스팅은 추후 추가 예정:

```python
# 향후 추가 예정
from backtest_overseas import OverseasBacktester

backtester = OverseasBacktester(initial_cash=10000)  # $10,000
backtester.run(start_date="20240101", end_date="20241231")
```

---

## 💡 팁

### 1. ETF 활용

- SPY, QQQ 등 ETF는 변동성 낮음
- 안정적 수익 추구 시 ETF 비중 높이기

### 2. 빅테크 집중

- AAPL, MSFT, GOOGL은 유동성 최고
- 초보자는 빅테크만 매매 권장

### 3. 뉴스 확인

- 미국 경제지표 발표일 주의
- FOMC, 고용지표, CPI 등

### 4. 분산 투자

- 섹터 분산 (빅테크 + 금융 + 헬스케어)
- 국내 + 해외 분산으로 리스크 감소

---

## 📞 디스코드 알림

국내주식과 동일한 Discord 채널 사용:

- `#신호-감지`: 매수 신호
- `#매매-내역`: 매수/매도 기록
- `#보유-현황`: 수익률 모니터링
- `#시장-상태`: 급락장/횡보장 감지
- `#에러-로그`: 오류 알림

**해외주식 알림 구분**:
```
🇺🇸 [AAPL] 매수 신호 감지! (4/5)
💰 [TSLA] 매수 완료: 10주 @ $250.00
```

---

**작성일**: 2025-10-14
**작성자**: Claude Code
**버전**: 1.0.0 (해외주식 초기 버전)
