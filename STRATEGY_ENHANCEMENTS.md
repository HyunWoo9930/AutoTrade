# 강화된 3단 로켓 전략 - 업데이트 요약

## 📊 추가된 기능 (2025-10-14)

### 1. 시장 상태 감지 (Market Regime Detection)

**감지 방식:**
- **ADX (Average Directional Index)**: 추세 강도 측정
- **변동성 분석**: 최근 20일 표준편차
- **가격 변화율**: 최근 5일 변화율 추적

**시장 상태 분류:**

#### 📈 추세장 (Trending)
- 조건: ADX ≥ 25
- 매수 전략: 신호 3개 이상이면 매수 (기존 전략)
- 손절 라인: -5%

#### 📊 횡보장 (Sideways)
- 조건: ADX < 25 + MA5와 MA20 간격 2% 이내
- 매수 전략: **신호 4개 이상만 매수** (임계치 상향)
- 이유: 횡보장에서는 가짜 신호가 많아 보수적 접근
- 손절 라인: -5%

#### 🚨 급락장 (Crash)
- 조건: 5일간 -10% 이상 하락 또는 변동성 8% 초과
- 매수 전략: **매수 완전 금지**
- 보유 포지션: **즉시 긴급 청산**
- 손절 라인: **-3%로 강화** (평상시 -5%)

#### ❓ 불명확 (Unknown)
- 조건: 위 조건에 모두 해당 안 됨
- 매수 전략: 신호 4개 이상만 매수 (보수적)
- 손절 라인: -5%

---

### 2. 피라미드 매수 (Pyramid Buying)

**기존 문제:**
- 1차 매수만 구현 (40%)
- 나머지 60%는 미구현 상태

**새로운 로직:**

#### 1차 매수 (40%)
- 신호 충족 시 목표 수량의 40% 진입
- `pyramid_tracker`에 추적 정보 저장
  - 1차 매수가, 수량
  - 목표 총 수량
  - 남은 수량 (60%)
  - 손절가, ATR, 시장 상태

#### 2차 추가 매수 (60%)
- **조건:**
  - 수익률 +3% ~ +5% 구간
  - 신호 재확인 (3개 이상)
- **실행:**
  - 나머지 60% 추가 매수
  - 평균 단가 재조정
  - Discord 피라미드 전용 알림

**예시:**
```
목표 수량: 100주
1차 매수: 40주 @ 50,000원
2차 매수: 60주 @ 52,000원 (수익률 +4% 시)
평균 단가: (40×50,000 + 60×52,000) / 100 = 51,200원
```

---

### 3. 급락장 보호 메커니즘

**보호 조치:**

1. **신규 매수 금지**
   - 급락장 감지 시 신호가 강해도 진입 차단
   - "🚨 급락장 감지! 매수 금지" 메시지 출력

2. **보유 포지션 긴급 청산**
   - 기존 보유 종목 즉시 전량 매도
   - 수익/손실 관계없이 보호 매도
   - Discord 긴급 청산 알림

3. **손절 라인 강화**
   - 평상시: -5%
   - 급락장: **-3%** (빠른 손절)

4. **피라미드 추적 정보 삭제**
   - 청산 시 분할 매수 계획 취소

---

### 4. Discord 알림 추가

#### 신규 알림 메서드:

**`notify_market_regime()`**
- 시장 상태 감지 알림 (급락장/횡보장)
- 표시 정보: ADX, 5일 변화율, 변동성
- 채널: `market`

**`notify_pyramid_buy()`**
- 피라미드 추가 매수 알림 (2차)
- 표시 정보: 수량, 단가, 평균단가 재조정
- 채널: `trade`

**`notify_crash_protection()`**
- 급락장 긴급 청산 알림
- 표시 정보: 수익률, 손익, 긴급 청산 사유
- 채널: `trade`
- 색상: 빨강 (경고)

---

## 🎯 전략 흐름도

### 매수 결정 프로세스

```
1. 시장 상태 감지
   ├─ 급락장? → 매수 금지
   ├─ 횡보장? → 신호 4개 이상 필요
   ├─ 추세장? → 신호 3개 이상 필요
   └─ 불명확? → 신호 4개 이상 필요 (보수적)

2. 매수 실행 (40%)
   └─ pyramid_tracker에 정보 저장

3. 보유 중 관리
   ├─ +3~5% 도달 + 신호 3개 → 2차 추가매수 (60%)
   ├─ +10% 도달 → 1차 익절 (50% 매도)
   ├─ +20% 도달 → 2차 익절 (전량 매도)
   └─ -5% 도달 → 손절 (전량 매도)
```

### 급락장 감지 시 프로세스

```
1. 급락장 감지 (5일 -10% 또는 변동성 8%+)
   ├─ Discord 시장 상태 알림 발송
   └─ 전략 실행 분기

2. 보유 포지션 있음?
   ├─ YES → 즉시 전량 긴급 청산
   │         └─ Discord 긴급 청산 알림
   └─ NO → 매수 차단
             └─ "급락장 감지! 매수 금지" 출력
```

---

## 📝 파일 변경 사항

### 1. `code/advanced_strategy.py`

**추가된 메서드:**
- `detect_market_regime()`: 시장 상태 감지
- `pyramid_tracker`: 분할 매수 추적 딕셔너리

**수정된 메서드:**
- `execute_strategy()`: 시장 상태 감지 추가
- `_execute_buy()`: regime 파라미터 추가, 피라미드 추적 저장
- `_manage_position()`: regime 파라미터 추가, 피라미드 2차 매수, 급락장 보호

**주요 변경:**
```python
# 피라미드 추적
self.pyramid_tracker = {
    stock_code: {
        'first_buy_qty': 40,
        'first_buy_price': 50000,
        'target_qty': 100,
        'remaining_qty': 60,
        'stop_loss': 48000,
        'atr': 1000,
        'regime': 'trending'
    }
}

# 시장별 매수 임계치
if regime == "crash":
    # 매수 금지
elif regime == "sideways":
    if signals >= 4:  # 4개 이상
        self._execute_buy(...)
elif regime == "trending":
    if signals >= 3:  # 3개 이상
        self._execute_buy(...)

# 피라미드 2차 매수
if 3.0 <= profit_rate <= 5.0 and remaining_qty > 0:
    if signals >= 3:
        # 60% 추가 매수
```

---

### 2. `code/discord/discord_notifier.py`

**추가된 메서드:**
- `notify_market_regime()`: 시장 상태 알림
- `notify_pyramid_buy()`: 피라미드 매수 알림
- `notify_crash_protection()`: 급락장 긴급 청산 알림

**기존 메서드:**
- `notify_buy()`: 일반 매수
- `notify_sell()`: 일반 매도
- `notify_buy_failed()`: 매수 실패
- `notify_sell_failed()`: 매도 실패
- `notify_signal_strong()`: 강한 신호
- `notify_holding()`: 보유 현황

---

### 3. `code/test_enhanced_strategy.py` (신규)

**테스트 함수:**
- `test_market_regime()`: 시장 상태 감지 테스트
- `test_buy_signals()`: 매수 신호 및 임계치 테스트
- `test_pyramid_logic()`: 피라미드 로직 시뮬레이션
- `test_crash_protection()`: 급락장 보호 테스트

---

## 🚀 배포 방법

### 1. Docker 이미지 빌드 & 푸시

```bash
# GitHub Actions가 자동으로 실행됨
git add .
git commit -m "feat: 시장 상태 감지 및 피라미드 매수 추가"
git push origin main
```

GitHub Actions가:
1. Docker 이미지 빌드
2. Docker Hub에 푸시 (`hyunwoo12/stock_trading:latest`)
3. EC2 서버 SSH 접속
4. K8s deployment 재시작

---

### 2. 수동 배포 (필요 시)

```bash
# EC2 서버 접속
ssh ec2-user@your-server-ip

# K8s CronJob 재시작
kubectl delete cronjob stock-trading-strategy
kubectl apply -f k8s/cronjob-strategy.yaml

# 로그 확인
kubectl get cronjobs
kubectl get jobs
kubectl logs -f <job-pod-name>
```

---

## 📊 실행 결과 확인

### 1. Discord 알림 확인

5개 채널에서 알림 확인:
- **system**: 시작/종료
- **trade**: 매수/매도/피라미드/긴급청산
- **signal**: 신호 분석/보유 현황
- **market**: 시장 상태/아침저녁 루틴
- **report**: 일일 리포트

### 2. 매매 일지 확인

```bash
# EC2 서버에서
kubectl exec -it <strategy-pod> -- cat /app/data/trading_journal.json
```

또는 PVC 직접 확인:
```bash
kubectl get pvc
kubectl describe pvc trading-journal-pvc
```

---

## 🔍 예상 시나리오

### 시나리오 1: 추세장에서 정상 매수

```
1. ADX = 35 (강한 추세)
2. 신호 = 4/5 (강한 신호)
3. 결과: ✅ 1차 매수 40%
4. 수익률 +4% 도달
5. 신호 재확인 = 3/5
6. 결과: ✅ 2차 추가매수 60%
7. 수익률 +10% 도달
8. 결과: ✅ 1차 익절 50% 매도
```

---

### 시나리오 2: 횡보장에서 신호 부족

```
1. ADX = 18 (약한 추세)
2. MA5와 MA20 간격 = 1.5%
3. 판단: 📊 횡보장
4. 신호 = 3/5
5. 결과: ❌ 매수 거부 (4개 필요)
```

---

### 시나리오 3: 급락장 보호

```
1. 5일 변화율 = -12%
2. 변동성 = 9.5%
3. 판단: 🚨 급락장 감지
4. 보유 중 종목 2개
5. 결과: ⚡ 전량 긴급 청산
6. Discord: "🚨 급락장 긴급 청산!" 알림
7. 신규 매수: 차단
```

---

### 시나리오 4: 피라미드 매수 실패

```
1. 1차 매수 40% 완료
2. 수익률 +4% 도달
3. 신호 재확인 = 2/5 (약화)
4. 결과: ⚠️ 추가 매수 보류
5. 계속 홀딩 중 (1차 익절 대기)
```

---

## ⚙️ 설정 값 조정 (필요시)

### `advanced_strategy.py`에서 수정 가능:

```python
# 급락장 감지 임계치
if price_change_5d < -10 or volatility > 8:  # -10% 또는 8% 변동성

# 횡보장 감지
if latest['ADX'] < 25:  # ADX 25 미만
    ma_diff < 2:  # MA 간격 2% 이내

# 피라미드 매수 타이밍
if 3.0 <= profit_rate <= 5.0:  # +3~5% 구간

# 손절 라인
stop_loss_threshold = -5.0  # 평상시
if regime == "crash":
    stop_loss_threshold = -3.0  # 급락장
```

---

## 📈 기대 효과

1. **횡보장 대응**: 가짜 신호 필터링으로 손실 감소
2. **급락장 보호**: 큰 손실 방지 (빠른 청산)
3. **수익 극대화**: 피라미드 매수로 추세 활용
4. **리스크 관리**: 시장별 차별화된 전략

---

## 🎓 학습 포인트

### ADX (Average Directional Index)
- 0~100 사이 값
- 25 미만: 약한 추세 또는 횡보
- 25~50: 강한 추세
- 50 이상: 매우 강한 추세

### 피라미드 매수 (Pyramid Buying)
- 수익이 나는 포지션에 추가 매수
- 장점: 추세 확인 후 진입으로 안전
- 주의: 평균단가 상승, 과도한 집중 리스크

### 시장 상태별 전략
- **추세장**: 공격적 (낮은 임계치)
- **횡보장**: 보수적 (높은 임계치)
- **급락장**: 방어적 (매수 금지 + 청산)

---

## ✅ 체크리스트

- [x] 시장 상태 감지 구현 (ADX, 변동성)
- [x] 횡보장 대응 (신호 임계치 상향)
- [x] 급락장 보호 (매수 금지 + 긴급 청산)
- [x] 피라미드 매수 완성 (40% + 60%)
- [x] Discord 알림 추가 (3가지)
- [x] 테스트 스크립트 작성
- [x] 문서화 완료

---

## 🔄 다음 개선 사항 (추후)

1. **백테스팅 시스템**: 과거 데이터로 전략 검증
2. **뉴스 감지**: 공시/뉴스 기반 급락장 조기 감지
3. **분봉 데이터**: 일봉 외 분봉으로 정밀도 향상
4. **포트폴리오 리밸런싱**: 섹터별 비중 조정
5. **기계학습 모델**: 시장 상태 예측 정확도 향상

---

**작성일**: 2025-10-14
**작성자**: Claude Code
**버전**: 2.0.0
