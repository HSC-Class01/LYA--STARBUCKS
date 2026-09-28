# ZIP 안내

GitHub Actions의 실제 workflow 경로는 `.github/workflows/update.yml`이어야 합니다.

요청하신 대로 배포용 ZIP에는 hidden 경로를 넣지 않았습니다. 따라서 ZIP에는 동일 workflow의 설치본을 `workflow_install/update.yml`에 별도로 넣고, GitHub 저장소에는 실제 `.github/workflows/update.yml`을 생성해야 합니다.
