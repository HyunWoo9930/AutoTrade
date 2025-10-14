# AWS EC2 K3s 배포 가이드

## 📋 목차
1. [사전 준비](#사전-준비)
2. [GitHub Repository 설정](#github-repository-설정)
3. [EC2 서버 설정](#ec2-서버-설정)
4. [배포 실행](#배포-실행)
5. [모니터링](#모니터링)
6. [문제 해결](#문제-해결)

---

## 🔧 사전 준비

### 필요한 것들
- AWS EC2 인스턴스 (Ubuntu 20.04+ 권장)
- K3s 설치 완료
- GitHub 계정
- Docker 설치 (EC2)

---

## 🔐 GitHub Repository 설정

### 1. Repository Secrets 설정

GitHub Repository → Settings → Secrets and variables → Actions → New repository secret

다음 시크릿을 추가하세요:

| Secret Name | 설명 | 예시 |
|-------------|------|------|
| `EC2_HOST` | EC2 인스턴스 퍼블릭 IP | `54.123.45.67` |
| `EC2_USER` | EC2 사용자 이름 | `ec2-user` 또는 `ubuntu` |
| `EC2_SSH_PRIVATE_KEY` | EC2 SSH 프라이빗 키 | `-----BEGIN RSA PRIVATE KEY-----...` |
| `DISCORD_WEBHOOK_SYSTEM` | Discord 시스템 알림 웹훅 (배포 알림용) | `https://discord.com/api/webhooks/...` |

### 2. SSH 키 생성 (필요시)

```bash
# 로컬에서 SSH 키 확인
cat ~/.ssh/id_rsa
# 또는 EC2 키페어 파일 내용 복사
cat ~/Downloads/your-key.pem
```

---

## 🖥️ EC2 서버 설정

### 1. 초기 서버 설정

```bash
# EC2에 SSH 접속
ssh -i your-key.pem ec2-user@your-ec2-ip

# Docker 설치 (Amazon Linux 2)
sudo yum update -y
sudo yum install docker -y
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker ec2-user

# K3s 설치 (이미 설치되어 있다면 Skip)
curl -sfL https://get.k3s.io | sh -

# kubectl 권한 설정
sudo chmod 644 /etc/rancher/k3s/k3s.yaml
mkdir -p ~/.kube
sudo cp /etc/rancher/k3s/k3s.yaml ~/.kube/config
sudo chown $(id -u):$(id -g) ~/.kube/config
```

### 2. 프로젝트 디렉토리 생성

```bash
# 프로젝트 디렉토리 생성
mkdir -p ~/stock_trading/k8s
cd ~/stock_trading
```

### 3. Kubernetes Secret 생성

**⚠️ 중요: Secret은 GitHub에 Push하지 말고 서버에서 직접 생성!**

```bash
# secret.yaml 파일 생성 (민감 정보 포함)
cat > ~/stock_trading/k8s/secret.yaml << 'EOF'
apiVersion: v1
kind: Secret
metadata:
  name: stock-trading-secret
  namespace: default
type: Opaque
stringData:
  APP_KEY: "YOUR_KIS_APP_KEY"
  APP_SECRET: "YOUR_KIS_APP_SECRET"
  ACCOUNT_NO: "YOUR_ACCOUNT_NUMBER"
  DISCORD_WEBHOOK_SYSTEM: "YOUR_DISCORD_WEBHOOK_URL"
  DISCORD_WEBHOOK_TRADE: "YOUR_DISCORD_WEBHOOK_URL"
  DISCORD_WEBHOOK_SIGNAL: "YOUR_DISCORD_WEBHOOK_URL"
  DISCORD_WEBHOOK_MARKET: "YOUR_DISCORD_WEBHOOK_URL"
  DISCORD_WEBHOOK_REPORT: "YOUR_DISCORD_WEBHOOK_URL"
EOF

# Secret 적용
sudo kubectl apply -f ~/stock_trading/k8s/secret.yaml

# Secret 확인
sudo kubectl get secrets
```

### 4. GitHub Container Registry 접근 설정

```bash
# GitHub Personal Access Token 생성 필요
# GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
# Scopes: read:packages 선택

# Docker 로그인
echo "YOUR_GITHUB_TOKEN" | sudo docker login ghcr.io -u YOUR_GITHUB_USERNAME --password-stdin
```

---

## 🚀 배포 실행

### 1. 자동 배포 (GitHub Actions)

```bash
# main 브랜치에 push하면 자동 배포
git add .
git commit -m "Deploy to production"
git push origin main
```

GitHub Actions에서 자동으로:
1. Docker 이미지 빌드
2. GitHub Container Registry에 Push
3. EC2 서버에 배포
4. K3s에 CronJob 업데이트

### 2. 수동 배포

GitHub Repository → Actions → Deploy to AWS EC2 K3s → Run workflow

---

## 📊 모니터링

### 1. CronJob 상태 확인

```bash
# CronJob 목록
sudo kubectl get cronjobs

# 실행 이력
sudo kubectl get jobs --sort-by=.metadata.creationTimestamp

# Pod 상태
sudo kubectl get pods
```

### 2. 로그 확인

```bash
# 최근 Job의 로그 확인
POD_NAME=$(sudo kubectl get pods --sort-by=.metadata.creationTimestamp -o name | tail -1)
sudo kubectl logs $POD_NAME

# 특정 Pod 로그
sudo kubectl logs <pod-name>

# 로그 실시간 모니터링
sudo kubectl logs -f <pod-name>
```

### 3. CronJob 수동 실행 (테스트)

```bash
# CronJob 즉시 실행
sudo kubectl create job --from=cronjob/stock-trading-strategy manual-test-$(date +%s)

# 실행 확인
sudo kubectl get jobs
sudo kubectl logs job/manual-test-xxxxx
```

### 4. Grafana 연동

Grafana에서 다음 데이터 소스를 추가하세요:

- **Prometheus**: K3s metrics
- **Loki**: Application logs (설치 필요)

```bash
# Loki & Promtail 설치 (옵션)
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update

helm install loki grafana/loki-stack \
  --namespace monitoring \
  --create-namespace \
  --set grafana.enabled=true \
  --set prometheus.enabled=true
```

---

## 🔧 K8s Manifest 업데이트

### ImagePullPolicy 수정

production 배포를 위해 `cronjob-*.yaml` 파일 수정:

```yaml
# Before
imagePullPolicy: Never

# After
imagePullPolicy: Always
```

```bash
# EC2에서 수정
cd ~/stock_trading/k8s
sudo kubectl apply -f cronjob-strategy.yaml
sudo kubectl apply -f cronjob-morning.yaml
sudo kubectl apply -f cronjob-evening.yaml
```

---

## ❓ 문제 해결

### 이미지 Pull 실패

```bash
# ImagePullBackOff 발생 시
sudo kubectl describe pod <pod-name>

# Docker 로그인 재시도
echo "YOUR_GITHUB_TOKEN" | sudo docker login ghcr.io -u YOUR_GITHUB_USERNAME --password-stdin

# 이미지 수동 Pull
sudo docker pull ghcr.io/your-username/stock_trading:latest
sudo docker save ghcr.io/your-username/stock_trading:latest | sudo k3s ctr images import -
```

### CronJob이 실행되지 않음

```bash
# CronJob 상세 정보
sudo kubectl describe cronjob stock-trading-strategy

# 시간대 확인
sudo kubectl get cronjob stock-trading-strategy -o yaml | grep timeZone

# 수동 실행으로 테스트
sudo kubectl create job --from=cronjob/stock-trading-strategy test-run
```

### Secret 관련 오류

```bash
# Secret 존재 확인
sudo kubectl get secret stock-trading-secret

# Secret 재생성
sudo kubectl delete secret stock-trading-secret
sudo kubectl apply -f ~/stock_trading/k8s/secret.yaml
```

### 로그 확인이 안 됨

```bash
# 완료된 Pod도 표시
sudo kubectl get pods --show-all

# 종료된 Pod의 로그
sudo kubectl logs <pod-name> --previous
```

---

## 📈 배포 스케줄

현재 설정된 CronJob 스케줄:

| CronJob | 스케줄 | 설명 |
|---------|--------|------|
| `stock-trading-strategy` | 평일 10:00, 14:00 | 메인 거래 전략 실행 |
| `cronjob-morning` | 평일 09:00 | 장 시작 전 시장 분석 |
| `cronjob-evening` | 평일 16:00 | 장 마감 후 리포트 |

---

## 🔐 보안 체크리스트

- [ ] GitHub Secret에 모든 민감 정보 등록
- [ ] EC2 Security Group에서 필요한 포트만 오픈
- [ ] SSH 키 기반 인증 사용 (비밀번호 로그인 비활성화)
- [ ] K8s Secret은 서버에서만 관리 (Git에 포함 X)
- [ ] Discord Webhook URL은 환경 변수로 관리
- [ ] 정기적인 패키지 업데이트 실행

---

## 📞 지원

문제가 발생하면 다음을 확인하세요:

1. GitHub Actions 로그
2. EC2 서버 로그 (`sudo kubectl logs`)
3. Discord 알림 채널
4. Grafana 대시보드 (설정된 경우)
