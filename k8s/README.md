# Kubernetes Manifests

이 디렉토리는 주식 자동매매 봇의 Kubernetes 배포 파일들을 포함합니다.

## 📁 파일 구조

```
k8s/
├── configmap.yaml          # 워치리스트 설정
├── secret.yaml             # API 키, Discord 웹훅 (템플릿)
├── pvc.yaml                # 거래 일지 저장소
├── cronjob-strategy.yaml   # 메인 전략 실행 (10:00, 14:00)
├── cronjob-morning.yaml    # 장 시작 전 루틴 (08:50)
└── cronjob-evening.yaml    # 장 마감 후 루틴 (15:40)
```

## ⚠️ 중요 사항

### Secret 관리
`secret.yaml` 파일은 **템플릿**입니다. 실제 배포 시:

1. EC2 서버에서 실제 값으로 secret.yaml 생성
2. `kubectl apply -f secret.yaml` 실행
3. **절대 실제 Secret을 Git에 커밋하지 마세요!**

### 이미지 설정
CronJob YAML 파일의 이미지 경로를 자신의 GitHub 계정으로 변경하세요:

```yaml
image: ghcr.io/YOUR_GITHUB_USERNAME/stock_trading:latest
```

## 🚀 배포 방법

### 1. ConfigMap 적용
```bash
kubectl apply -f configmap.yaml
```

### 2. Secret 생성 (EC2에서)
```bash
# secret.yaml을 실제 값으로 수정 후
kubectl apply -f secret.yaml
```

### 3. PVC 생성
```bash
kubectl apply -f pvc.yaml
```

### 4. CronJob 배포
```bash
kubectl apply -f cronjob-strategy.yaml
kubectl apply -f cronjob-morning.yaml
kubectl apply -f cronjob-evening.yaml
```

### 5. 확인
```bash
kubectl get cronjobs
kubectl get pvc
kubectl get configmap
kubectl get secret
```

## 📊 CronJob 스케줄

| CronJob | 시간 (한국) | 설명 |
|---------|-------------|------|
| stock-trading-morning | 평일 08:50 | 장 시작 전 시장 분석 |
| stock-trading-strategy | 평일 10:00, 14:00 | 메인 거래 전략 실행 |
| stock-trading-evening | 평일 15:40 | 장 마감 후 일일 리포트 |

## 🔧 수동 실행 (테스트)

```bash
# CronJob을 즉시 실행
kubectl create job --from=cronjob/stock-trading-strategy manual-test

# 로그 확인
kubectl logs job/manual-test
```

## 📝 로그 확인

```bash
# 최근 Pod 찾기
kubectl get pods --sort-by=.metadata.creationTimestamp

# 로그 보기
kubectl logs <pod-name>

# 실시간 로그
kubectl logs -f <pod-name>
```

## 🔄 업데이트

GitHub Actions가 자동으로 업데이트하지만, 수동으로 하려면:

```bash
# 이미지 Pull
docker pull ghcr.io/YOUR_USERNAME/stock_trading:latest

# K3s에 이미지 Import
docker save ghcr.io/YOUR_USERNAME/stock_trading:latest | sudo k3s ctr images import -

# CronJob 재시작 (필요시)
kubectl delete cronjob stock-trading-strategy
kubectl apply -f cronjob-strategy.yaml
```

## 🗑️ 삭제

```bash
kubectl delete cronjob stock-trading-morning
kubectl delete cronjob stock-trading-strategy
kubectl delete cronjob stock-trading-evening
kubectl delete pvc trading-journal-pvc
kubectl delete configmap stock-trading-config
kubectl delete secret stock-trading-secret
```
