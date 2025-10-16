# Discord Bot 배포 확인 가이드

배포가 잘 안 되는 것 같을 때 확인하는 방법입니다.

## 1️⃣ GitHub Actions 워크플로우 확인

### 방법 1: GitHub 웹사이트
1. https://github.com/HyunWoo9930/AutoTrade/actions 접속
2. 최신 워크플로우 상태 확인
3. 실패한 단계가 있는지 확인

### 방법 2: 터미널 (gh CLI 필요)
```bash
# GitHub CLI로 워크플로우 확인 (설치되어 있다면)
gh run list --limit 5
gh run view <run-id>
```

---

## 2️⃣ Docker 이미지 빌드 확인

### Docker Hub에서 확인
1. https://hub.docker.com/r/hyunwoo12/stock_trading/tags 접속
2. `latest` 태그의 최신 업데이트 시간 확인
3. 최근 커밋 시간과 일치하는지 확인

### 예상 시간
- 커밋 → Docker 이미지 빌드: **3-5분**
- 이미지 빌드 → 서버 배포: **2-3분**
- **총 소요 시간: 약 5-8분**

---

## 3️⃣ 서버(EC2/K3s)에서 확인

### SSH 접속
```bash
ssh ubuntu@your-ec2-ip
```

### Discord Bot Pod 상태 확인
```bash
# Pod 목록 보기
sudo kubectl get pods

# Discord Bot Pod 찾기
sudo kubectl get pods | grep discord-bot

# Pod 상세 정보
sudo kubectl describe pod discord-bot-xxxxx

# Pod 로그 확인 (가장 중요!)
sudo kubectl logs discord-bot-xxxxx

# Pod 재시작 시간 확인
sudo kubectl get pod discord-bot-xxxxx -o wide
```

### Deployment 재시작 (강제)
```bash
# Discord Bot Deployment 재시작
sudo kubectl rollout restart deployment discord-bot

# 재시작 상태 확인
sudo kubectl rollout status deployment discord-bot

# 새 Pod 생성 확인
sudo kubectl get pods -w
```

---

## 4️⃣ 배포가 안 되는 일반적인 이유

### ❌ 원인 1: Docker 이미지 Pull 실패
**증상**: Pod이 `ImagePullBackOff` 상태

**확인**:
```bash
sudo kubectl describe pod discord-bot-xxxxx
# "Failed to pull image" 메시지 확인
```

**해결**:
```bash
# Docker Hub 로그인 확인
sudo docker login

# 수동으로 이미지 Pull
sudo docker pull hyunwoo12/stock_trading:latest

# K3s에 이미지 import
sudo docker save hyunwoo12/stock_trading:latest | sudo k3s ctr images import -

# Deployment 재시작
sudo kubectl rollout restart deployment discord-bot
```

---

### ❌ 원인 2: Pod이 이전 이미지 사용 중
**증상**: 코드가 변경되었는데도 이전 버전 실행

**확인**:
```bash
# Pod의 이미지 확인
sudo kubectl get pod discord-bot-xxxxx -o jsonpath='{.spec.containers[0].image}'

# Pod의 이미지 ID 확인
sudo kubectl get pod discord-bot-xxxxx -o jsonpath='{.status.containerStatuses[0].imageID}'
```

**해결**:
```bash
# Deployment 강제 재생성 (Pod 삭제)
sudo kubectl delete pod discord-bot-xxxxx

# 또는 Deployment 재시작
sudo kubectl rollout restart deployment discord-bot
```

---

### ❌ 원인 3: Secret 설정 누락
**증상**: Pod이 CrashLoopBackOff 상태, 로그에 환경 변수 에러

**확인**:
```bash
# Secret 확인
sudo kubectl get secret stock-trading-secret

# Secret 내용 확인 (base64 디코딩 필요)
sudo kubectl get secret stock-trading-secret -o yaml
```

**해결**:
```bash
# Secret 재생성 (9개 웹훅 모두 포함)
sudo kubectl delete secret stock-trading-secret

sudo kubectl create secret generic stock-trading-secret \
  --from-literal=DISCORD_WEBHOOK_TRADE_DOMESTIC=your_url \
  --from-literal=DISCORD_WEBHOOK_TRADE_OVERSEAS=your_url \
  --from-literal=DISCORD_WEBHOOK_SIGNAL_DOMESTIC=your_url \
  --from-literal=DISCORD_WEBHOOK_SIGNAL_OVERSEAS=your_url \
  --from-literal=DISCORD_WEBHOOK_MARKET_DOMESTIC=your_url \
  --from-literal=DISCORD_WEBHOOK_MARKET_OVERSEAS=your_url \
  --from-literal=DISCORD_WEBHOOK_REPORT=your_url \
  --from-literal=DISCORD_WEBHOOK_SYSTEM_TRADING=your_url \
  --from-literal=DISCORD_WEBHOOK_SYSTEM_DEPLOY=your_url \
  --from-literal=KIS_APP_KEY=your_key \
  --from-literal=KIS_APP_SECRET=your_secret \
  --from-literal=KIS_ACCOUNT_NO=your_account \
  --from-literal=DISCORD_BOT_TOKEN=your_token

# Deployment 재시작
sudo kubectl rollout restart deployment discord-bot
```

---

### ❌ 원인 4: 봇 코드 에러
**증상**: Pod이 CrashLoopBackOff 상태

**확인**:
```bash
# 로그에서 Python 에러 확인
sudo kubectl logs discord-bot-xxxxx
```

**해결**:
- 로그를 보고 에러 원인 파악
- 코드 수정 후 다시 커밋/푸시

---

## 5️⃣ 빠른 배포 확인 스크립트

### 한 번에 확인
```bash
echo "=== 1. GitHub Actions 최신 워크플로우 ==="
gh run list --limit 1

echo -e "\n=== 2. Discord Bot Pod 상태 ==="
sudo kubectl get pods | grep discord-bot

echo -e "\n=== 3. Deployment 상태 ==="
sudo kubectl get deployment discord-bot

echo -e "\n=== 4. Pod 로그 (최근 20줄) ==="
POD_NAME=$(sudo kubectl get pods | grep discord-bot | grep Running | awk '{print $1}')
sudo kubectl logs $POD_NAME --tail=20

echo -e "\n=== 5. Pod 이미지 ==="
sudo kubectl get pod $POD_NAME -o jsonpath='{.spec.containers[0].image}'
```

---

## 6️⃣ 강제 배포 (긴급)

### 모든 것을 다시 시작
```bash
# 1. 최신 이미지 Pull
sudo docker pull hyunwoo12/stock_trading:latest

# 2. K3s에 import
sudo docker save hyunwoo12/stock_trading:latest | sudo k3s ctr images import -

# 3. Discord Bot Pod 삭제 (자동 재생성)
sudo kubectl delete pod -l app=discord-bot

# 4. 새 Pod 생성 대기
sudo kubectl get pods -w

# 5. 로그 확인
POD_NAME=$(sudo kubectl get pods | grep discord-bot | grep Running | awk '{print $1}')
sudo kubectl logs $POD_NAME -f
```

---

## 7️⃣ 배포 완료 확인

### Discord Bot이 정상 작동하는지 확인
1. Discord에서 `/도움말` 입력
2. 새로운 `/매매내역` 명령어가 보이는지 확인
3. `/잔고` 명령어로 수익률이 정상 표시되는지 확인
4. `/포지션` 명령어가 에러 없이 작동하는지 확인

---

## 🆘 문제 해결이 안 될 때

### 로그 전체 확인
```bash
# 전체 로그 파일로 저장
sudo kubectl logs discord-bot-xxxxx > bot.log

# 로그 확인
cat bot.log
```

### 디버깅 모드로 실행
```bash
# Pod 내부로 진입
sudo kubectl exec -it discord-bot-xxxxx -- /bin/bash

# 수동으로 봇 실행
cd /app
python discord_bot.py
```

---

## 📞 문의

위 방법으로도 해결이 안 되면 다음 정보를 함께 알려주세요:
1. GitHub Actions 워크플로우 링크
2. `sudo kubectl get pods` 결과
3. `sudo kubectl logs discord-bot-xxxxx` 전체 로그
4. Docker Hub의 latest 태그 업데이트 시간
