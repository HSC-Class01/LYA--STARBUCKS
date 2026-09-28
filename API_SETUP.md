# OpenDART API 설정

## 1. 인증키 발급
OpenDART에서 개인 API 인증키를 발급합니다.

## 2. GitHub Secret
Repository → Settings → Secrets and variables → Actions → New repository secret

- Name: `DART_API_KEY`
- Secret: 발급받은 40자리 인증키

## 3. 최초 실행
Actions → DART monthly update → Run workflow

## 4. 자동 실행
`0 0 1 * *`는 UTC 기준 매월 1일 00:00이며, 한국시간으로 매월 1일 오전 9시입니다.

## 5. Workflow 오류 예방
- Python 3.12 고정
- `actions/checkout@v4`, `setup-python@v5`, Pages artifact/deploy action 사용
- `contents: write`, `pages: write`, `id-token: write` 권한 명시
- 동일 workflow 중복 실행 방지를 위한 concurrency 설정
- API key는 secret으로만 전달
- 데이터 변경이 없으면 빈 commit을 만들지 않음
