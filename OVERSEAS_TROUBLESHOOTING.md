# 해외주식 트러블슈팅 가이드

## 🔍 KeyError 해결 방법

### 문제: `KeyError: 0` in overseas_strategy.py

```python
KeyError: 0
  File "overseas_strategy.py", line 307
  cash_usd = float(balance['output2'][0].get('frcr_dncl_amt_2', 0))
```

### 원인

KIS API의 해외주식 잔고 조회 응답 구조가 예상과 다를 수 있음:
- `output2`가 리스트가 아닌 딕셔너리일 수 있음
- `output2`가 빈 리스트일 수 있음
- 키 이름이 다를 수 있음

### 해결 방법

#### 1단계: API 응답 구조 확인

```bash
python3 code/test_overseas_api.py
```

이 스크립트는:
- 해외주식 잔고 조회 API 호출
- 응답 구조 출력 (타입, 키 목록)
- 전체 응답을 `data/overseas_balance_response.json`에 저장

#### 2단계: 응답 JSON 확인

```bash
cat data/overseas_balance_response.json | jq .
```

예상 구조:

```json
{
  "rt_cd": "0",
  "msg1": "정상처리 되었습니다.",
  "output1": [
    {
      "ovrs_pdno": "AAPL",
      "ovrs_cblc_qty": "10",
      "now_pric2": "175.50",
      "evlu_pfls_rt": "5.23"
    }
  ],
  "output2": {
    "frcr_dncl_amt_2": "5000.00"
  }
}
```

또는:

```json
{
  "output2": [
    {
      "frcr_dncl_amt_2": "5000.00"
    }
  ]
}
```

#### 3단계: 코드 수정 (이미 적용됨)

`overseas_strategy.py`는 이미 다음과 같이 수정되어 양쪽 케이스를 처리합니다:

```python
if balance and 'output2' in balance:
    try:
        # 리스트인 경우
        if isinstance(balance['output2'], list) and len(balance['output2']) > 0:
            cash_usd = float(balance['output2'][0].get('frcr_dncl_amt_2', 0))
        # 딕셔너리인 경우
        elif isinstance(balance['output2'], dict):
            cash_usd = float(balance['output2'].get('frcr_dncl_amt_2', 0))
    except (KeyError, IndexError, TypeError, ValueError) as e:
        print(f"⚠️ 잔고 조회 실패, 기본값 사용: {e}")
        cash_usd = 0
```

---

## 🧪 디버깅 모드

### 디버깅 출력 활성화

`overseas_strategy.py`의 `execute_strategy()` 메서드에 이미 추가됨:

```python
# 🔍 디버깅: API 응답 구조 확인
if balance:
    print(f"\n🔍 API 응답 키: {balance.keys()}")
    if 'output2' in balance:
        print(f"🔍 output2 타입: {type(balance['output2'])}")
        print(f"🔍 output2 내용: {balance['output2']}")
    if 'output1' in balance:
        print(f"🔍 output1 타입: {type(balance['output1'])}")
```

실행 시 자동으로 API 응답 구조가 출력됩니다.

### 디버깅 출력 제거

수정이 완료되면 위 코드 블록을 주석 처리하거나 삭제:

```python
# # 🔍 디버깅: API 응답 구조 확인
# if balance:
#     print(f"\n🔍 API 응답 키: {balance.keys()}")
#     ...
```

---

## 🚨 자주 발생하는 에러

### 1. 토큰 발급 실패

**증상:**
```
❌ 토큰 발급 실패: {"error":"invalid_client"}
```

**해결:**
- `config.py`에서 APP_KEY, APP_SECRET 확인
- 모의투자 계정 활성화 확인
- 1분에 1회만 토큰 발급 가능 (재시도 필요)

### 2. API 호출 제한

**증상:**
```
❌ 해외주식 조회 실패: {"msg1":"API 호출 횟수 초과"}
```

**해결:**
- KIS API는 초당 2회 제한
- `kis_api.py`의 `min_interval = 0.5` (이미 설정됨)
- 대량 종목 조회 시 시간 간격 필요

### 3. 거래소 코드 불일치

**증상:**
```
❌ 해외주식 조회 실패: {"msg1":"거래소 코드 오류"}
```

**해결:**
- 현재가 조회: `"NAS"`, `"NYSE"`, `"AMS"`
- 매매 주문: `"NASD"`, `"NYSE"`, `"AMEX"`
- `watchlist_us.py`에서 거래소 코드 확인

### 4. output2 빈 리스트

**증상:**
```python
IndexError: list index out of range
```

**해결:**
이미 수정됨:
```python
if isinstance(balance['output2'], list) and len(balance['output2']) > 0:
    cash_usd = float(balance['output2'][0].get('frcr_dncl_amt_2', 0))
```

### 5. 키 이름 오류

**증상:**
```python
KeyError: 'frcr_dncl_amt_2'
```

**해결:**
1. `test_overseas_api.py` 실행하여 실제 키 이름 확인
2. `overseas_strategy.py`에서 키 이름 수정

예시:
```python
# 잘못된 키 이름
cash_usd = float(balance['output2']['frcr_dncl_amt_2'])

# 올바른 키 이름 (예시)
cash_usd = float(balance['output2']['ovrs_frcr_dncl_amt'])
```

---

## 📋 체크리스트

### 실행 전 체크

- [ ] KIS API 토큰 발급 성공
- [ ] `test_overseas_api.py` 실행하여 API 응답 확인
- [ ] `data/overseas_balance_response.json` 파일 생성 확인
- [ ] 응답 구조가 코드와 일치하는지 확인

### 에러 발생 시 체크

- [ ] 에러 메시지와 라인 번호 확인
- [ ] 디버깅 출력으로 실제 API 응답 확인
- [ ] `output1`, `output2` 타입 확인 (list vs dict)
- [ ] 키 이름 확인 (오타, 버전 차이)

### 수정 후 체크

- [ ] `test_overseas.py` 실행하여 단일 종목 테스트
- [ ] 에러 없이 실행 완료
- [ ] 디버깅 출력 제거 (선택사항)

---

## 🛠️ 수동 API 테스트

### curl로 직접 API 호출

```bash
# 1. 토큰 발급
TOKEN=$(curl -X POST "https://openapi.koreainvestment.com:9443/oauth2/tokenP" \
  -H "content-type: application/json" \
  -d '{
    "grant_type": "client_credentials",
    "appkey": "YOUR_APP_KEY",
    "appsecret": "YOUR_APP_SECRET"
  }' | jq -r '.access_token')

# 2. 해외주식 잔고 조회
curl -X GET "https://openapi.koreainvestment.com:9443/uapi/overseas-stock/v1/trading/inquire-balance" \
  -H "authorization: Bearer $TOKEN" \
  -H "appkey: YOUR_APP_KEY" \
  -H "appsecret: YOUR_APP_SECRET" \
  -H "tr_id: VTTS3012R" \
  -G \
  --data-urlencode "CANO=YOUR_ACCOUNT" \
  --data-urlencode "ACNT_PRDT_CD=01" \
  --data-urlencode "OVRS_EXCG_CD=NASD" \
  --data-urlencode "TR_CRCY_CD=USD" \
  | jq .
```

---

## 📞 지원

### KIS API 문서

- 공식 문서: https://apiportal.koreainvestment.com
- API 명세: 해외주식 > 잔고조회 (VTTS3012R)

### 문의

- GitHub Issues: 프로젝트 저장소
- Discord: `#에러-로그` 채널

---

**작성일**: 2025-10-14
**버전**: 1.0.0
