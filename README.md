# ☕ LYA — STARBUCKS Financial Agent

[![🔗 대시보드 바로가기](https://img.shields.io/badge/%F0%9F%94%97%20%EB%8C%80%EC%8B%9C%EB%B3%B4%EB%93%9C%20%EB%B0%94%EB%A1%9C가기-B8A1E6?style=for-the-badge)](./site/index.html)

> DART(OpenDART) 정기보고서를 수집하고 주요 재무수치·재무비율을 계산한 뒤 GitHub Pages 대시보드로 보여주는 자동화 agent입니다.

## What it does
- 2010년부터 사업보고서·반기보고서·분기보고서 메타데이터 수집
- OpenDART 재무제표 API가 제공하는 기간의 구조화 재무수치 자동 수집
- 매출액, 매출총이익, 영업이익, 당기순이익, 자산, 부채, 자본, 유동자산, 유동부채, 현금, 재고자산 등 추출
- 영업이익률·순이익률·유동비율·부채비율·ROE·ROA·자산회전율 계산
- 매월 1일 KST 09:00(UTC 00:00) GitHub Actions 자동 실행
- GitHub Pages dashboard 자동 배포
- Annual / Half-year / Quarterly 3개 표 제공
- 국내 peer firms 참고표 제공

## API key setup
1. OpenDART에서 인증키를 발급합니다: https://opendart.fss.or.kr/
2. GitHub 저장소의 **Settings → Secrets and variables → Actions → New repository secret**으로 이동합니다.
3. 이름을 정확히 `DART_API_KEY`로 입력하고 발급받은 40자리 키를 값으로 저장합니다.
4. **Actions → DART monthly update → Run workflow**로 최초 수집을 수동 실행합니다.

API key는 코드나 README에 절대 직접 입력하지 않습니다.

## GitHub Pages
Repository Settings → Pages에서 **Source = GitHub Actions**를 선택합니다. 이후 workflow가 `site/`를 Pages artifact로 배포합니다.

대시보드 주소는 일반적으로 `https://HSC-Class01.github.io/LYA--STARBUCKS/` 형태입니다.

## Data notes
OpenDART의 구조화 재무제표 API와 공시검색 API의 제공 범위가 서로 다를 수 있으므로, 2010–2014 구간은 `filings.csv`의 공시 메타데이터를 먼저 보존하고 구조화 재무수치는 API 제공 여부에 따라 채워집니다. 원문 보고서 보존은 `config/company.json`의 `store_raw_reports`로 제어합니다.

## Peer firms
| Peer firm | 국내 사업 | 비고 |
|---|---|---|
| 커피빈코리아 | 커피전문점 | 국내 직영 중심 커피 브랜드 |
| 투썸플레이스 | 카페·디저트 | 국내 커피·디저트 전문점 |
| 이디야 | 커피전문점 | 국내 커피 프랜차이즈 |
| 할리스 | 커피전문점 | 국내 커피·베이커리 |
| 엠즈씨드(폴 바셋) | 커피전문점 | 매일유업 계열 커피 브랜드 |

Peer firms are a reference set, not a ranking or recommendation.
