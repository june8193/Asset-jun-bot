# AssetManager 백엔드 API 추가 명세서

KOSPI 및 KOSDAQ 지수 현황 데이터를 조회하기 위한 신규 API 스펙입니다.

## 1. 지수 조회 API
- **Endpoint**: `/api/market/indices`
- **Method**: `GET`
- **Description**: 코스피(KOSPI) 및 코스닥(KOSDAQ)의 현재 지수와 전일비 등락률 정보를 조회합니다.

### Request
- **Headers**: `Accept: application/json`
- **Query Parameters**: 없음

### Response
- **Status**: `200 OK`
- **Content-Type**: `application/json`
- **Body**:
```json
[
  {
    "index_name": "KOSPI",
    "current_price": 2700.50,
    "change_rate": 1.25
  },
  {
    "index_name": "KOSDAQ",
    "current_price": 850.20,
    "change_rate": -0.45
  }
]
```

### Response Schema Fields
- `index_name` (string): 지수 이름 (`KOSPI` 또는 `KOSDAQ`)
- `current_price` (float): 현재 지수 포인트 값
- `change_rate` (float): 전일 대비 등락률 (%)
