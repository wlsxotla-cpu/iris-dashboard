"""
KEIT SROME 수요조사·인터넷공시 대시보드 (Streamlit)

GitHub의 wlsxotla-cpu/iris-monitor-v2 리포지토리에서 GitHub Actions가
만들어두는 results/srome.json 을 읽어서 카드 형태로 보여준다.
IRIS 대시보드와는 완전히 별도의 앱이다 (가끔만 확인하는 용도라 분리함).
"""

import requests
import streamlit as st

SROME_JSON_URL = (
    "https://raw.githubusercontent.com/wlsxotla-cpu/iris-monitor-v2/main/results/srome.json"
)

SROME_LIST_URLS = {
    "수요조사": "https://srome.keit.re.kr/srome/biz/perform/opnnPrpsl/retrieveDmndSrvyLstView.do?prgmId=XPG201010000",
    "인터넷공시": "https://srome.keit.re.kr/srome/biz/perform/opnnPrpsl/retrieveIntrnDsclsLstView.do?prgmId=XPG201020000",
}


def _html(s: str) -> str:
    """각 줄의 앞뒤 공백을 제거해서, 마크다운이 들여쓰기를 코드블럭으로
    오인하지 않도록 한다."""
    return "\n".join(line.strip() for line in s.strip("\n").split("\n"))


st.set_page_config(page_title="SROME 수요조사·인터넷공시", layout="wide")

st.markdown(
    _html(
        """
        <style>
        .ancm-card {
            border: 1px solid #e5e5e5;
            border-radius: 8px;
            padding: 12px 16px;
            margin-bottom: 10px;
        }
        .ancm-title { font-weight: 600; margin-bottom: 4px; }
        .ancm-meta { color: #777; font-size: 0.85rem; margin-bottom: 8px; }
        .badge {
            display: inline-block;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 0.78rem;
            font-weight: 700;
            margin-right: 4px;
        }
        .badge-status { background: #e6f6ec; color: #14803c; }
        .badge-period { background: #fff4e0; color: #a15c00; }
        .badge-dday { background: #fdecea; color: #c0392b; }
        </style>
        """
    ),
    unsafe_allow_html=True,
)

st.title("🔎 SROME 수요조사·인터넷공시")
st.caption("⏰ IRIS 스크래퍼와 같은 GitHub Actions에서 매일 평일 오전 9시(KST)에 같이 갱신됩니다.")


@st.cache_data(ttl=300)
def load_data():
    resp = requests.get(SROME_JSON_URL, timeout=15)
    resp.raise_for_status()
    return resp.json()


try:
    data = load_data()
except Exception as e:
    st.error(f"데이터를 불러오지 못했습니다: {e}")
    st.stop()

with st.sidebar:
    st.header("⚙️ 설정")
    st.caption(f"마지막 갱신: {data.get('updated_at', '알 수 없음')}")
    if st.button("🔄 새로고침"):
        st.cache_data.clear()
        st.rerun()

items = data.get("items", [])

for category, list_url in SROME_LIST_URLS.items():
    cat_items = [i for i in items if i.get("category") == category]
    st.subheader(f"{category} ({len(cat_items)}건)")

    if not cat_items:
        st.caption("아직 준비 중이거나 현재 조회된 항목이 없습니다.")
        st.link_button(f"{category} 사이트에서 직접 보기 ↗", list_url)
        continue

    cols = st.columns(3)
    for i, item in enumerate(cat_items):
        with cols[i % 3]:
            st.markdown(
                _html(
                    f"""
                    <div class="ancm-card">
                    <div class="ancm-title">{item['title']}</div>
                    <div class="ancm-meta">
                    <span class="badge badge-status">{item.get('status', '')}</span>
                    <span class="badge badge-dday">{item.get('dday', '')}</span><br><br>
                    기획년도 {item.get('plan_year', '')}<br>
                    <span class="badge badge-period">접수기간 {item.get('period', '')}</span><br><br>
                    공고일 {item.get('notice_date', '')}
                    </div>
                    </div>
                    """
                ),
                unsafe_allow_html=True,
            )
    st.link_button(f"{category} 전체 목록 사이트에서 보기 ↗", list_url)

st.divider()
st.caption("KOTERI SJT")
