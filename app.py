"""
IRIS 공고 현황 대시보드 (Streamlit)

GitHub의 wlsxotla-cpu/iris-monitor-v2 리포지토리에서 GitHub Actions가
매일 만들어두는 results/latest.json 을 읽어서 표로 보여준다.
이 앱 자체는 IRIS 사이트에 접속하지 않으므로, 예전처럼 Streamlit Cloud가
IRIS 쪽에서 IP 차단을 당하는 문제가 생기지 않는다.
"""

import pandas as pd
import requests
import streamlit as st

# 실제 리포지토리 경로에 맞게 필요하면 수정
RAW_JSON_URL = (
    "https://raw.githubusercontent.com/wlsxotla-cpu/iris-monitor-v2/main/results/latest.json"
)

st.set_page_config(page_title="IRIS 공고 현황", layout="wide")

st.title("IRIS 공고 현황")


@st.cache_data(ttl=300)
def load_data():
    resp = requests.get(RAW_JSON_URL, timeout=15)
    resp.raise_for_status()
    return resp.json()


try:
    data = load_data()
except Exception as e:
    st.error(f"데이터를 불러오지 못했습니다: {e}")
    st.stop()

st.caption(
    f"마지막 갱신: {data.get('updated_at', '알 수 없음')}  ·  "
    f"필터 부처: {', '.join(data.get('departments', []))}"
)

items = data.get("items", [])
if not items:
    st.info("현재 조회된 공고가 없습니다.")
    st.stop()

df = pd.DataFrame(items)

col1, col2, col3 = st.columns(3)
with col1:
    tab_options = sorted(df["tab"].unique())
    selected_tabs = st.multiselect("탭", tab_options, default=tab_options)
with col2:
    org_options = sorted(df["org"].unique())
    selected_orgs = st.multiselect("소관부처", org_options, default=org_options)
with col3:
    keyword = st.text_input("제목 검색")

filtered = df[df["tab"].isin(selected_tabs) & df["org"].isin(selected_orgs)]
if keyword:
    filtered = filtered[filtered["title"].str.contains(keyword, case=False, na=False)]

st.write(f"총 {len(filtered)}건")

for _, row in filtered.iterrows():
    title = row["title"]
    detail_url = row.get("detail_url")
    header = f"[{title}]({detail_url})" if detail_url else title

    with st.container(border=True):
        st.markdown(f"**{header}**")
        st.caption(
            f"{row['tab']} · {row['org']} > {row['agency']} · "
            f"공고번호 {row['ancm_no']} · {row['ancm_date']} · "
            f"{row['status']} / {row['type']}"
        )
        attachments = row.get("attachments") or []
        if attachments:
            att_lines = " · ".join(
                f"[{a.get('name') or '첨부파일'}]({a.get('url')})" for a in attachments
            )
            st.markdown(f"첨부파일: {att_lines}")

if st.button("새로고침"):
    st.cache_data.clear()
    st.rerun()
