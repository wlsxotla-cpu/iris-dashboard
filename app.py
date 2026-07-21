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

st.caption(f"마지막 갱신: {data.get('updated_at', '알 수 없음')}")

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

DETAIL_URL = "https://www.iris.go.kr/contents/retrieveBsnsAncmView.do"

# IRIS 목록 페이지가 실제로 쓰는 폼 필드 (ancmId/ancmPrg만 채우고 나머지는 비워둔다)
FORM_FIELDS = [
    "bizSearch", "bsnsTl", "ancmPrg", "pageIndex", "ancmId", "ancmNo",
    "ancmTurn", "seq", "hirkSorgnBsnsCd", "bsnsAncmTap", "shSorgnYyBsnsCd",
    "sorgnIdArr", "ancmSttArr", "pbofrTpArr", "qualCndtArr", "blngGovdSeArr",
    "techFildArr", "shBsnsYy",
]


def detail_button_html(ancm_id, ancm_prg, key):
    if not ancm_id or not ancm_prg:
        return ""
    hidden_inputs = "".join(
        f'<input type="hidden" name="{f}" value="{ancm_prg if f == "ancmPrg" else (ancm_id if f == "ancmId" else "")}">'
        for f in FORM_FIELDS
    )
    return f"""
    <form action="{DETAIL_URL}" method="post" target="_blank" style="display:inline;margin:0;">
        {hidden_inputs}
        <button type="submit" style="
            padding:4px 10px;border-radius:6px;border:1px solid #d0d0d0;
            background:#f5f5f5;cursor:pointer;font-size:0.85rem;">
            상세보기 ↗
        </button>
    </form>
    """


for idx, row in filtered.iterrows():
    title = row["title"]

    with st.container(border=True):
        st.markdown(f"**{title}**")
        st.caption(
            f"{row['tab']} · {row['org']} > {row['agency']} · "
            f"공고번호 {row['ancm_no']} · {row['ancm_date']} · "
            f"{row['status']} / {row['type']}"
        )
        html = detail_button_html(row.get("ancm_id"), row.get("ancm_prg"), idx)
        if html:
            st.markdown(html, unsafe_allow_html=True)

if st.button("새로고침"):
    st.cache_data.clear()
    st.rerun()
