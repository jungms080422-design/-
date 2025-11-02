import streamlit as st
import pandas as pd
import random
import plotly.express as px

st.set_page_config(page_title="LifeStats 시뮬레이터", layout="centered")

# ------------------------------
# 데이터 불러오기
# ------------------------------
@st.cache_data
def load_data():
    data = {}
    files = {
        "흡연율": "data/현재_흡연율_일반담배_관련__현재사용률__20251102155742.csv",
        "우울증": "data/청소년_우울증.csv",
        "자살시도율": "data/청소년_자살시도율.csv",
        "사회문제노출": "data/사회문제_위험_노출_정도_20251102160905.csv"
    }
    for name, path in files.items():
        try:
            df = pd.read_csv(path)
            data[name] = df
        except Exception as e:
            st.warning(f"{name} 데이터 불러오기 실패: {e}")
    return data

data = load_data()

# ------------------------------
# 기본 설정
# ------------------------------
st.title("🌱 LifeStats: 청소년기 생명존중 시뮬레이터")
st.write("청소년기의 선택이 삶의 방향에 어떤 영향을 미칠까? 현실 데이터를 기반으로 한 시뮬레이션을 체험해보세요.")

if "started" not in st.session_state:
    st.session_state.started = False
    st.session_state.stats = {"정신건강": 50, "육체건강": 50, "위험행동": 0}

# ------------------------------
# 시작 단계
# ------------------------------
if not st.session_state.started:
    st.subheader("1️⃣ 먼저 성별을 선택하세요")
    gender = st.radio("성별 선택", ["남학생", "여학생", "비공개"])

    if st.button("게임 시작 🚀"):
        st.session_state.gender = gender
        st.session_state.started = True
        st.rerun()

else:
    st.subheader("🎮 청소년기 시뮬레이션 진행 중...")

    # 상황 리스트
    scenarios = [
        {
            "question": "요즘 스트레스가 심할 때, 당신은?",
            "choices": {
                "운동하며 풀기": {"정신건강": +5, "육체건강": +3},
                "혼자 스마트폰 하기": {"정신건강": -5, "위험행동": +3},
                "친구에게 털어놓기": {"정신건강": +7}
            }
        },
        {
            "question": "친구가 술 마시자고 제안했다면?",
            "choices": {
                "단호하게 거절": {"위험행동": -5},
                "조금만 마신다": {"정신건강": -2, "위험행동": +5},
                "같이 놀자고 한다": {"위험행동": +8, "정신건강": -3}
            }
        },
        {
            "question": "밤 12시가 넘었는데 숙제가 안 끝났을 때, 당신은?",
            "choices": {
                "일단 자고 아침에 한다": {"육체건강": +5},
                "밤새 끝낸다": {"육체건강": -7, "정신건강": -3},
                "친구에게 베껴달라 부탁": {"위험행동": +4, "정신건강": -4}
            }
        },
        {
            "question": "SNS에서 악플을 봤을 때 당신의 반응은?",
            "choices": {
                "무시한다": {"정신건강": -1},
                "같이 댓글 단다": {"위험행동": +5, "정신건강": -4},
                "신고하고 차단": {"정신건강": +3}
            }
        },
        {
            "question": "시험 성적이 기대 이하일 때, 당신은?",
            "choices": {
                "부모님과 이야기한다": {"정신건강": +5},
                "자책하며 울기": {"정신건강": -7},
                "다음 시험을 준비한다": {"정신건강": +3, "육체건강": -2}
            }
        }
    ]

    # ------------------------------
    # 진행
    # ------------------------------
    for i, s in enumerate(scenarios):
        st.markdown(f"### {i+1}. {s['question']}")
        choice = st.radio("선택하세요", list(s["choices"].keys()), key=f"q{i}")
        if st.button(f"확정_{i}", key=f"b{i}"):
            for stat, val in s["choices"][choice].items():
                st.session_state.stats[stat] = max(0, min(100, st.session_state.stats.get(stat, 50) + val))
            st.success(f"선택 반영됨! 현재 스탯: {st.session_state.stats}")
            st.rerun()

    # ------------------------------
    # 결과
    # ------------------------------
    st.header("📊 최종 결과")

    df_stats = pd.DataFrame(list(st.session_state.stats.items()), columns=["항목", "수치"])
    fig = px.bar(df_stats, x="항목", y="수치", color="항목", title="당신의 청소년기 스탯 결과")
    st.plotly_chart(fig)

    mental = st.session_state.stats["정신건강"]
    risk = st.session_state.stats["위험행동"]

    if mental < 30 or risk > 70:
        st.error("😔 결과: 우울/위험 상태입니다. 주변의 도움을 받는 게 좋아요.")
    elif mental > 70 and risk < 30:
        st.success("🌈 결과: 건강하고 행복한 청소년기! 생명 존중의 가치가 잘 지켜졌어요.")
    else:
        st.info("🙂 결과: 보통 수준이에요. 작은 습관 하나로 더 건강해질 수 있어요.")

    # ------------------------------
    # 통계 표시
    # ------------------------------
    st.markdown("---")
    st.subheader("📈 현실 데이터 비교 (요약)")

    for key, df in data.items():
        st.markdown(f"#### 🔹 {key} 데이터 일부 미리보기")
        st.dataframe(df.head())

