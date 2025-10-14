# 🚀 빠른 배포 가이드

## 1️⃣ GitHub Secrets 설정 (3분)

GitHub Repository → Settings → Secrets and variables → Actions → New repository secret

```
EC2_HOST = 여기에_EC2_퍼블릭_IP
EC2_USER = ec2-user
EC2_SSH_PRIVATE_KEY = 여기에_SSH_키_전체_내용
DISCORD_WEBHOOK_SYSTEM = https://discord.com/api/webhooks/1427482970457116692/O1ZIxe7L0ZFsH47ySlA8Q6Z8SnCgChnKLY0sj80jaCrl6MNcDwvZQww3Z8hlgizYItAH
```

**SSH 키 확인:**
```bash
cat ~/Downloads/your-ec2-key.pem
```

---

## 2️⃣ EC2 초기 설정 (5분)

```bash
# EC2 접속
ssh -i your-key.pem ec2-user@your-ec2-ip

# 복사해서 한 번에 실행
sudo yum update -y && \
sudo yum install docker -y && \
sudo systemctl start docker && \
sudo systemctl enable docker && \
sudo usermod -aG docker ec2-user && \
curl -sfL https://get.k3s.io | sh - && \
sudo chmod 644 /etc/rancher/k3s/k3s.yaml && \
mkdir -p ~/.kube && \
sudo cp /etc/rancher/k3s/k3s.yaml ~/.kube/config && \
sudo chown $(id -u):$(id -g) ~/.kube/config && \
mkdir -p ~/stock_trading/k8s

# 재접속 (docker 그룹 권한 적용)
exit
ssh -i your-key.pem ec2-user@your-ec2-ip
```

---

## 3️⃣ Secret 파일 생성 (2분)

```bash
# EC2에서 실행
cat > ~/stock_trading/k8s/secret.yaml << 'EOF'
apiVersion: v1
kind: Secret
metadata:
  name: stock-trading-secret
  namespace: default
type: Opaque
stringData:
  APP_KEY: "PSzqRqmM6FqnhsKXXcz396qrApRE91stOuqs"
  APP_SECRET: "x3kn1Nb9ud7lXhg1N9TPo58TVtjabsgODlhvmaq/3AmYbpTfrUeri+iP3NRS2xcl3Z+q6u/1I4H6Kzhaws0Ectie0FZRFSvgJ5+j4liZEB/YR3eg7afCaRV6r4I8kpYC0Ovm3Gw9f7bcGy5NWvrQma+LFlD1pMmSsboqyBtqvKGXqCLMl8M="
  ACCOUNT_NO: "50155286"
  DISCORD_WEBHOOK_SYSTEM: "https://discord.com/api/webhooks/1427482970457116692/O1ZIxe7L0ZFsH47ySlA8Q6Z8SnCgChnKLY0sj80jaCrl6MNcDwvZQww3Z8hlgizYItAH"
  DISCORD_WEBHOOK_TRADE: "https://discord.com/api/webhooks/1427483211323281428/_fQpVJneh54QJASCvcLzjTu11veFgQEkbt3C_oS00flOOyANOglTcp-ie361bYeivjif"
  DISCORD_WEBHOOK_SIGNAL: "https://discord.com/api/webhooks/1427483273915011072/MWzRbq5b8IC2eMEOjy6_432NsG67reXWuY_5LxXpkQNo3kvqw_JPelQ-8YKYpAW0P02P"
  DISCORD_WEBHOOK_MARKET: "https://discord.com/api/webhooks/1427483312624242778/1th0wIBqI-_r33qGqE12dMvyc-DXlrvY8DbTImXMEHSFiB39ZBzQQ5J09oUXTm1b0hEU"
  DISCORD_WEBHOOK_REPORT: "https://discord.com/api/webhooks/1427483383046606880/ztluKN-5DVovzq5Be-y_Qc6HBUnXdl6xHZbIjpkX8Tw6rGq3POTz2nrStzZ-lI-lVEBk"
EOF

# Secret 적용
sudo kubectl apply -f ~/stock_trading/k8s/secret.yaml

# 확인
sudo kubectl get secret stock-trading-secret
```

---

## 4️⃣ GitHub Container Registry 로그인 (2분)

```bash
# EC2에서 실행

# GitHub Personal Access Token 생성
# GitHub.com → Settings → Developer settings → Personal access tokens
# → Tokens (classic) → Generate new token
# 권한: read:packages, write:packages

# 로그인 (YOUR_TOKEN을 실제 토큰으로 변경)
echo "YOUR_GITHUB_TOKEN" | sudo docker login ghcr.io -u HyunWoo9930 --password-stdin
```

---

## 5️⃣ 배포 시작 (1분)

```bash
# 로컬 터미널에서 실행
cd /Users/hyunwoo/Desktop/Project/stock_trading

git add .
git commit -m "Deploy to AWS EC2 K3s"
git push origin main
```

GitHub Actions가 자동으로 배포를 시작합니다!

---

## 6️⃣ 배포 확인

### GitHub Actions
- Repository → Actions 탭 → 워크플로우 확인

### Discord
- 배포 완료 알림 확인

### EC2
```bash
ssh -i your-key.pem ec2-user@your-ec2-ip

# CronJob 확인
sudo kubectl get cronjobs

# Pod 확인
sudo kubectl get pods
```

---

## 7️⃣ 수동 테스트 (선택)

```bash
# EC2에서 실행
sudo kubectl create job --from=cronjob/stock-trading-strategy test-run

# 로그 확인
sudo kubectl get pods
sudo kubectl logs <pod-name>
```

---

## 🎯 자동 실행 스케줄

- **08:50** (평일): 장 시작 전 분석
- **10:00** (평일): 메인 전략 실행
- **14:00** (평일): 메인 전략 실행
- **15:40** (평일): 장 마감 후 리포트

---

## ⚠️ 문제 해결

### 이미지 Pull 실패
```bash
# EC2에서
echo "YOUR_TOKEN" | sudo docker login ghcr.io -u HyunWoo9930 --password-stdin
sudo docker pull ghcr.io/HyunWoo9930/stock_trading:latest
sudo docker save ghcr.io/HyunWoo9930/stock_trading:latest | sudo k3s ctr images import -
```

### CronJob 실행 안됨
```bash
sudo kubectl describe cronjob stock-trading-strategy
sudo kubectl create job --from=cronjob/stock-trading-strategy manual-test
sudo kubectl logs job/manual-test
```

### Secret 오류
```bash
sudo kubectl delete secret stock-trading-secret
sudo kubectl apply -f ~/stock_trading/k8s/secret.yaml
```

---

## 📞 완료!

이제 자동매매 봇이 AWS EC2에서 실행됩니다.
- 코드 수정 후 `git push`하면 자동 배포
- Discord로 모든 알림 수신
- Grafana로 모니터링 가능
