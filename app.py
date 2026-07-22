"""
IRIS 공고 현황 대시보드 (Streamlit)

GitHub의 wlsxotla-cpu/iris-monitor-v2 리포지토리에서 GitHub Actions가
매일 만들어두는 results/latest.json 을 읽어서 카드 형태로 보여준다.
이 앱 자체는 IRIS 사이트에 접속하지 않으므로, 예전처럼 Streamlit Cloud가
IRIS 쪽에서 IP 차단을 당하는 문제가 생기지 않는다.
"""

import time
from datetime import datetime, timezone

import pandas as pd
import requests
import streamlit as st


ORG_COLORS = [
    "#2c5aa0", "#c0392b", "#1e8449", "#8e44ad", "#d35400",
    "#16a085", "#b7950b", "#2874a6", "#943126", "#117864",
    "#6c3483", "#af601a", "#212f3d", "#7d6608", "#0e6251",
]


def color_for_org(org_label: str) -> str:
    idx = sum(ord(c) for c in org_label) % len(ORG_COLORS)
    return ORG_COLORS[idx]


def _html(s: str) -> str:
    """각 줄의 앞뒤 공백을 제거해서, 마크다운이 들여쓰기를 코드블럭으로
    오인하지 않도록 한다 (중첩된 HTML을 삽입해도 안전하게 동작)."""
    return "\n".join(line.strip() for line in s.strip("\n").split("\n"))

RAW_JSON_URL = (
    "https://raw.githubusercontent.com/wlsxotla-cpu/iris-monitor-v2/main/results/latest.json"
)

DETAIL_URL = "https://www.iris.go.kr/contents/retrieveBsnsAncmView.do"

FORM_FIELDS = [
    "bizSearch", "bsnsTl", "ancmPrg", "pageIndex", "ancmId", "ancmNo",
    "ancmTurn", "seq", "hirkSorgnBsnsCd", "bsnsAncmTap", "shSorgnYyBsnsCd",
    "sorgnIdArr", "ancmSttArr", "pbofrTpArr", "qualCndtArr", "blngGovdSeArr",
    "techFildArr", "shBsnsYy",
]

GH_REPO = "wlsxotla-cpu/iris-monitor-v2"
GH_WORKFLOW_FILE = "scrape.yml"


def trigger_scrape():
    token = st.secrets.get("GITHUB_TOKEN")
    if not token:
        return False, "GITHUB_TOKEN이 설정되어 있지 않습니다 (앱 Settings > Secrets에서 추가해주세요)."
    url = f"https://api.github.com/repos/{GH_REPO}/actions/workflows/{GH_WORKFLOW_FILE}/dispatches"
    try:
        resp = requests.post(
            url,
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
            },
            json={"ref": "main"},
            timeout=15,
        )
    except Exception as e:
        return False, str(e)

    if resp.status_code == 204:
        return True, None
    return False, f"{resp.status_code}: {resp.text[:200]}"


def get_latest_run(token, since_iso):
    """방금 트리거한 실행을 찾는다 (since_iso 이후 생성된 것 중 가장 최근)."""
    url = f"https://api.github.com/repos/{GH_REPO}/actions/workflows/{GH_WORKFLOW_FILE}/runs"
    try:
        resp = requests.get(
            url,
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
            },
            params={"event": "workflow_dispatch", "per_page": 5},
            timeout=15,
        )
        resp.raise_for_status()
    except Exception:
        return None

    runs = resp.json().get("workflow_runs", [])
    candidates = [r for r in runs if r["created_at"] >= since_iso]
    if candidates:
        return candidates[-1]  # 가장 오래된(=방금 만든) 것
    return None


st.set_page_config(page_title="IRIS 공고 현황", layout="wide")

st.markdown(
    _html(
        """
        <style>
        .org-header {
            color: white;
            padding: 10px 16px;
            border-radius: 8px 8px 0 0;
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-weight: 600;
            font-size: 1.05rem;
            margin-top: 18px;
        }
        .org-header .count {
            background: rgba(255,255,255,0.25);
            padding: 2px 10px;
            border-radius: 999px;
            font-size: 0.85rem;
        }
        .tab-count {
            color: #666;
            font-size: 0.85rem;
            margin: 4px 0 10px 0;
        }
        .ancm-card {
            border: 1px solid #e5e5e5;
            border-top: none;
            border-radius: 0 0 8px 8px;
            padding: 12px 16px;
            margin-bottom: 2px;
        }
        .ancm-title { font-weight: 600; margin-bottom: 4px; }
        .ancm-meta { color: #777; font-size: 0.85rem; margin-bottom: 8px; }
        </style>
        """
    ),
    unsafe_allow_html=True,
)

st.title("📋 IRIS 공고 현황")


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

items = data.get("items", [])
if not items:
    st.info("현재 조회된 공고가 없습니다.")
    st.stop()

df = pd.DataFrame(items)
df["org_list"] = df["org"].apply(
    lambda o: [x.strip() for x in o.split(",") if x.strip()] if o else ["부처 미표시"]
)
# 콤마로 여러 부처가 같이 적힌 공동(다부처) 공고는, 관련된 부처 그룹 모두에 노출한다.
exploded = df.explode("org_list").rename(columns={"org_list": "org_label"})

with st.sidebar:
    st.header("⚙️ 설정")
    tab_options = sorted(exploded["tab"].unique())
    org_options = sorted(exploded["org_label"].unique())

    qp = st.query_params
    saved_tabs = [t for t in qp.get("tabs", "").split(",") if t in tab_options]
    saved_orgs = [o for o in qp.get("orgs", "").split(",") if o in org_options]

    selected_tabs = st.multiselect(
        "탭", tab_options, default=saved_tabs or tab_options
    )
    selected_orgs = st.multiselect(
        "소관부처", org_options, default=saved_orgs or org_options
    )
    keyword = st.text_input("제목 검색", value=qp.get("kw", ""))

    # 선택값을 URL에 반영 (다음에 이 URL로 들어오면 그대로 복원됨)
    st.query_params["tabs"] = ",".join(selected_tabs)
    st.query_params["orgs"] = ",".join(selected_orgs)
    if keyword:
        st.query_params["kw"] = keyword
    elif "kw" in st.query_params:
        del st.query_params["kw"]

    st.caption("💡 지금 이 필터 상태로 주소창 URL을 즐겨찾기 해두면 다음에도 그대로 열립니다.")
    st.caption(f"마지막 갱신: {data.get('updated_at', '알 수 없음')}")

    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("🔄 새로고침"):
            st.cache_data.clear()
            st.rerun()
    with col_b:
        if st.button("🚀 지금 수집"):
            since = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            ok, err = trigger_scrape()
            if not ok:
                st.error(err)
            else:
                token = st.secrets.get("GITHUB_TOKEN")
                with st.status("수집 요청을 보냈습니다...", expanded=True) as status:
                    time.sleep(5)  # Actions 목록에 새 실행이 잡힐 때까지 잠깐 대기
                    run = None
                    for attempt in range(30):  # 최대 약 2~3분 대기
                        run = get_latest_run(token, since)
                        if run and run["status"] == "completed":
                            break
                        status.write(
                            f"진행 중... ({run['status'] if run else '실행 확인 중'})"
                        )
                        time.sleep(5)

                    if run and run["status"] == "completed":
                        if run["conclusion"] == "success":
                            status.update(label="✅ 수집 완료! 목록을 새로고침합니다.", state="complete")
                            st.cache_data.clear()
                        else:
                            status.update(
                                label=f"❌ 수집 실패 ({run['conclusion']}) - Actions 로그를 확인해주세요",
                                state="error",
                            )
                    else:
                        status.update(
                            label="⏱️ 시간이 오래 걸리고 있습니다 - Actions 탭에서 직접 확인해주세요",
                            state="error",
                        )
                st.rerun()

filtered = exploded[exploded["tab"].isin(selected_tabs) & exploded["org_label"].isin(selected_orgs)]
if keyword:
    filtered = filtered[filtered["title"].str.contains(keyword, case=False, na=False)]

st.write(f"총 **{filtered['title'].nunique()}**건 (공동부처 공고는 관련 부처 모두에 표시됩니다)")


def detail_button_html(ancm_id, ancm_prg):
    if not ancm_id or not ancm_prg:
        return ""
    hidden_inputs = "".join(
        f'<input type="hidden" name="{f}" value="{ancm_prg if f == "ancmPrg" else (ancm_id if f == "ancmId" else "")}">'
        for f in FORM_FIELDS
    )
    return _html(
        f"""
        <form action="{DETAIL_URL}" method="post" target="_blank" style="display:inline;margin:0;">
        {hidden_inputs}
        <button type="submit" style="padding:4px 10px;border-radius:6px;border:1px solid #2c5aa0;background:white;color:#2c5aa0;cursor:pointer;font-size:0.85rem;">
        🔗 IRIS에서 보기
        </button>
        </form>
        """
    )


for org_label in sorted(filtered["org_label"].unique(), key=lambda x: (x == "부처 미표시", x)):
    org_items = filtered[filtered["org_label"] == org_label]

    tab_counts = org_items["tab"].value_counts()
    tab_summary = "  ·  ".join(f"{t} {c}건" for t, c in tab_counts.items())

    color = color_for_org(org_label)
    st.markdown(
        _html(
            f"""
            <div class="org-header" style="background:{color};">
            <span>{org_label}</span>
            <span class="count">{len(org_items)}건</span>
            </div>
            <div class="tab-count">{tab_summary}</div>
            """
        ),
        unsafe_allow_html=True,
    )

    cols = st.columns(3)
    for i, (_, row) in enumerate(org_items.iterrows()):
        with cols[i % 3]:
            html_button = detail_button_html(row.get("ancm_id"), row.get("ancm_prg"))
            st.markdown(
                _html(
                    f"""
                    <div class="ancm-card">
                    <div class="ancm-title">{row['title']}</div>
                    <div class="ancm-meta">
                    {row['tab']} · {row['agency']}<br>
                    공고번호 {row['ancm_no']}<br>
                    {row['ancm_date']} · {row['status']} / {row['type']}
                    </div>
                    {html_button}
                    </div>
                    """
                ),
                unsafe_allow_html=True,
            )
