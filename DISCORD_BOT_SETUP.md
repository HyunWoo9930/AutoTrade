# 🤖 Discord Bot 설정 가이드

## 1️⃣ Discord Bot 생성

### Discord Developer Portal에서 Bot 만들기

1. **Discord Developer Portal 접속**
   - https://discord.com/developers/applications

2. **New Application 클릭**
   - 이름: `주식 자동매매 봇` (원하는 이름)

3. **Bot 탭으로 이동**
   - `Add Bot` 클릭
   - `Reset Token` 클릭 → 토큰 복사 (⚠️ 절대 공유 금지!)

4. **Bot 권한 설정**
   - **Privileged Gateway Intents**에서:
     - ✅ `MESSAGE CONTENT INTENT` 활성화
     - ✅ `SERVER MEMBERS INTENT` 활성화

5. **OAuth2 → URL Generator**
   - **Scopes**:
     - ✅ `bot`
     - ✅ `applications.commands`
   - **Bot Permissions**:
     - ✅ `Send Messages`
     - ✅ `Embed Links`
     - ✅ `Read Message History`
     - ✅ `Use Slash Commands`

6. **생성된 URL로 봇 초대**
   - 하단의 Generated URL 복사
   - 브라우저에 붙여넣기
   - 서버 선택 후 초대

---

## 2️⃣ 환경변수 설정

### .env 파일에 추가

```bash
# Discord Bot Token (Discord Developer Portal에서 복사)
DISCORD_BOT_TOKEN=your_discord_bot_token_here
```

**⚠️ 주의사항:**
- 토큰은 절대 GitHub에 올리지 마세요!
- `.env` 파일은 `.gitignore`에 포함되어 있습니다

---

## 3️⃣ 로컬에서 테스트

### Python 패키지 설치

```bash
pip install discord.py==2.3.2
```

### 봇 실행

```bash
cd /Users/hyunwoo/Desktop/Project/stock_trading
python code/discord_bot.py
```

**성공 메시지:**
```
✅ Discord Bot 명령어 동기화 완료
🤖 봇 로그인: 주식 자동매매 봇#1234
📊 서버 수: 1
✅ KIS API 토큰 발급 완료
```

---

## 4️⃣ Discord에서 명령어 테스트

### 기본 명령어

```
/도움말          - 명령어 목록
/봇상태          - 봇 작동 상태
/잔고            - 계좌 잔고 조회
/포지션          - 보유 종목 상세
/오늘            - 오늘 매매 내역
/통계            - 전체 거래 통계
/종목분석 005930 - 삼성전자 분석
/알림설정 on     - 알림 켜기
```

---

## 5️⃣ K8s에 배포

### Secret 업데이트 (Discord Bot Token 추가)

```bash
kubectl create secret generic stock-trading-secret \
  --from-literal=APP_KEY=your_app_key \
  --from-literal=APP_SECRET=your_app_secret \
  --from-literal=ACCOUNT_NO=your_account_no \
  --from-literal=DISCORD_WEBHOOK_SYSTEM=your_webhook_url \
  --from-literal=DISCORD_WEBHOOK_TRADE=your_webhook_url \
  --from-literal=DISCORD_WEBHOOK_SIGNAL=your_webhook_url \
  --from-literal=DISCORD_WEBHOOK_MARKET=your_webhook_url \
  --from-literal=DISCORD_WEBHOOK_REPORT=your_webhook_url \
  --from-literal=DISCORD_BOT_TOKEN=your_discord_bot_token \
  --dry-run=client -o yaml | kubectl apply -f -
```

### Deployment 배포

```bash
kubectl apply -f k8s/deployment-discord-bot.yaml
```

### 로그 확인

```bash
kubectl logs -f deployment/discord-bot
```

---

## 6️⃣ 명령어 전체 목록

### 📊 조회 명령어
| 명령어 | 설명 | 예시 |
|--------|------|------|
| `/잔고` | 예수금, 총평가액, 수익률 | `/잔고` |
| `/포지션` | 보유 종목 상세 (손익, 수익률) | `/포지션` |
| `/오늘` | 오늘 매매 내역 | `/오늘` |
| `/통계` | 전체 통계 (승률, 누적수익) | `/통계` |

### 🔍 분석 명령어
| 명령어 | 설명 | 예시 |
|--------|------|------|
| `/종목분석` | 실시간 신호 분석 (5점 스코어) | `/종목분석 005930` |
| `/봇상태` | 봇 작동 상태 | `/봇상태` |

### 💰 매매 명령어 (안전장치)
| 명령어 | 설명 | 예시 |
|--------|------|------|
| `/매수` | 매수 주문 (확인만) | `/매수 005930 10` |
| `/매도` | 매도 주문 (확인만) | `/매도 005930 5` |

### ⚙️ 설정 명령어
| 명령어 | 설명 | 예시 |
|--------|------|------|
| `/알림설정` | 알림 켜기/끄기 | `/알림설정 on` |
| `/도움말` | 명령어 도움말 | `/도움말` |

---

## 7️⃣ 트러블슈팅

### ❌ 봇이 응답하지 않음
- Discord Developer Portal에서 `MESSAGE CONTENT INTENT` 활성화 확인
- 봇 로그 확인: `kubectl logs -f deployment/discord-bot`

### ❌ 명령어가 보이지 않음
- 봇 재시작: `kubectl rollout restart deployment/discord-bot`
- 명령어 동기화 최대 1시간 소요 (Discord 서버 캐시)

### ❌ KIS API 에러
- Secret에 API 키가 제대로 설정되었는지 확인
- `kubectl get secret stock-trading-secret -o yaml`

---

## 8️⃣ 보안 주의사항

⚠️ **절대 공유 금지:**
- Discord Bot Token
- KIS API Key / Secret
- 계좌번호

✅ **안전 수칙:**
- `.env` 파일을 GitHub에 커밋하지 마세요
- Secret은 K8s Secret으로 관리하세요
- 봇 토큰이 유출되면 즉시 재발급하세요

---

## 9️⃣ 다음 단계 (고급 기능)

현재 구현된 기능:
- ✅ 실시간 잔고 조회
- ✅ 포지션 관리
- ✅ 매매 내역
- ✅ 종목 분석
- ✅ 통계

**향후 추가 가능한 기능:**
- [ ] `/추천` - AI 추천 매수 종목 Top 5
- [ ] `/섹터` - 섹터별 강도 순위
- [ ] `/긴급청산` - 모든 포지션 즉시 청산
- [ ] `/백테스트` - 전략 백테스트
- [ ] `/리밸런싱` - 포트폴리오 리밸런싱 제안
- [ ] 자동 리포트 (매일 15:30 장 마감 후)
- [ ] 위험 알림 (손실 -3% 이상)

---

## 📞 문의

문제가 발생하면:
1. 로그 확인: `kubectl logs -f deployment/discord-bot`
2. 봇 재시작: `kubectl rollout restart deployment/discord-bot`
3. GitHub Issues에 문의

---

**🎉 설치 완료!**

이제 Discord에서 `/도움말` 명령어로 시작하세요!
