# AssetManager 백엔드 API 추가 명세서 - 시장 휴장일 판정

KOSPI 및 KOSDAQ 주식 시장의 휴장일 여부를 판정하기 위한 신규 API 스펙입니다.

## 1. 시장 휴장일 조회 API
- **Endpoint**: `/api/market/holiday`
- **Method**: `GET`
- **Description**: 특정 날짜의 한국 거래소(KRX) 또는 미국 거래소의 개장 여부와 휴장 사유를 조회합니다.

### Request
- **Headers**: `Accept: application/json`
- **Query Parameters**:
  - `date` (string, optional): 조회할 날짜 (형식: `YYYY-MM-DD`). 지정하지 않으면 API 서버 기준 오늘 날짜를 기본값으로 사용합니다.
  - `country` (string, optional): 국가 코드 (예: `KR`, `US`). 기본값은 `KR` 입니다 (대소문자 구분 없음).

### Response
- **Status**: `200 OK`
- **Content-Type**: `application/json`
- **Body**:
```json
{
  "date": "2026-06-14",
  "country": "KR",
  "is_holiday": true,
  "description": "주말"
}
```

### Response Schema Fields
- `date` (string): 검증 대상 날짜 (`YYYY-MM-DD`)
- `country` (string): 조회 대상 국가 코드 (`KR` 또는 `US`)
- `is_holiday` (boolean): 해당 날짜가 휴장일(주말 또는 공휴일)인 경우 `true`, 정상 영업일인 경우 `false`
- `description` (string): 휴장 사유 (예: `주말`, `추석 연휴`, `신정`, `영업일` 등)
