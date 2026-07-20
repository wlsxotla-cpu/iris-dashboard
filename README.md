# iris-dashboard

iris-monitor-v2 리포지토리가 매일 만들어두는 공고 목록(results/latest.json)을
Streamlit으로 보여주는 대시보드입니다.

이 앱은 IRIS 사이트에 직접 접속하지 않고 GitHub에 저장된 결과 파일만
읽어오기 때문에, Streamlit Cloud에 배포해도 IRIS 쪽 IP 차단 문제가 생기지
않습니다.

## 배포 방법 (Streamlit Cloud)

1. https://share.streamlit.io 접속 후 GitHub 계정으로 로그인
2. "Create app" 클릭
3. Repository: 이 리포지토리 선택
4. Branch: main
5. Main file path: app.py
6. Deploy 클릭

배포되면 발급되는 URL로 어디서든 접속해서 확인할 수 있습니다.

## 부처 필터를 바꾼 경우

iris-monitor-v2 쪽 scraper.py의 DEPARTMENTS 목록을 바꾸면, 이 대시보드는
따로 수정할 필요 없이 다음 갱신 때부터 자동으로 새 부처 기준 데이터를
보여줍니다.
