import streamlit as st
import pandas as pd
import random

st.set_page_config(page_title="LifeStats: 청소년 생명존중 시뮬레이터", page_icon="🎮", layout="centered")

# ---- 앱 제목 ----
st.title("🎮 LifeStats: 청소년 생명존중 시뮬레이터")
st.caption("현실 데이터를 기반으로 한 선택 시뮬레이션 게임")

# ---- CSV 데이터 로드 ----
@st.cache_data
def load_data():
    files = {
        "흡연": "현재_흡연율_일반담배_궐련__현재사용률__20251102155742.csv",
        "우울증": "청소년_우울증.csv",
        "자살시도": "청소년_자살시도율.csv",
        "사회문제노출": "사회문제_위험_노출_정도_20251102160905.csv"
    }
    data = {}
    for key, file in files.items():
        try:
            data[key] = pd.read_csv(file, encoding="utf-8")
        except:
            try:
                data[key] = pd.read_csv(file, encoding="cp949")
            except:
                data[key] = None
    return data

data = load_data()

# ---- 초기 설정 ----
if "stage" not in st.session_state:
    st.session_state.stage = 0
    st.session_state.mental = 50
    st.session_state.physical = 50
    st.session_state.risk = 50

# ---- 성별 선택 ----
if st.session_state.stage == 0:
    st.subheader("시작하기 전에...")
    gender = st.radio("성별을 선택해주세요", ["남학생", "여학생", "선택하지 않음"])
    if st.button("게임 시작"):
        st.session_state.stage = 1
        st.session_state.gender = gender
        st.experimental_rerun()

# ---- 시뮬레이션 단계 ----
elif st.session_state.stage == 1:
    st.subheader("📘 청소년기의 선택")
    st.write("학교에서 친구들이 담배를 권합니다. 당신의 선택은?")
    choice = st.radio(
        "선택하세요:",
        ["그냥 해본다", "정중히 거절한다", "모른 척 회피한다"]
    )

    if st.button("결정!"):
        if choice == "그냥 해본다":
            st.session_state.risk += 20
            st.session_state.physical -= 10
        elif choice == "정중히 거절한다":
            st.session_state.mental += 10
        else:
            st.session_state.mental -= 5

        st.session_state.stage = 2
        st.experimental_rerun()

elif st.session_state.stage == 2:
    st.write("📱 SNS에서 누군가 나를 험담합니다. 당신은?")
    choice = st.radio(
        "선택하세요:",
        ["같이 싸운다", "무시한다", "선생님께 알린다"]
    )

    if st.button("다음"):
        if choice == "같이 싸운다":
            st.session_state.risk += 15
            st.session_state.mental -= 10
        elif choice == "무시한다":
            st.session_state.mental -= 5
        else:
            st.session_state.mental += 10
        st.session_state.stage = 3
        st.experimental_rerun()

elif st.session_state.stage == 3:
    st.write("💊 친구가 ‘기분 좋아지는 약’을 건넸습니다. 당신은?")
    choice = st.radio(
        "선택하세요:",
        ["거절한다", "호기심에 시도한다", "모른 척 회피한다"]
    )

    if st.button("결과 보기"):
        if choice == "호기심에 시도한다":
            st.session_state.physical -= 15
            st.session_state.risk += 30
        elif choice == "거절한다":
            st.session_state.mental += 10
        else:
            st.session_state.mental -= 5
        st.session_state.stage = 4
        st.experimental_rerun()

# ---- 결과 ----
elif st.session_state.stage == 4:
    st.subheader("🎯 당신의 결과")

    m, p, r = st.session_state.mental, st.session_state.physical, st.session_state.risk

    if r > 70:
        result = "⚠️ 위험한 행동이 많아 삶의 균형이 무너졌어요."
    elif m < 40:
        result = "😔 정신적으로 힘든 시기를 보내고 있어요. 주변에 도움을 요청해요."
    elif m > 70 and p > 70:
        result = "🌈 건강하고 행복한 삶을 만들어가고 있어요!"
    else:
        result = "🙂 평범하지만 꾸준히 노력 중이에요."

    st.success(result)

    st.write(f"정신건강: {m}")
    st.write(f"육체건강: {p}")
    st.write(f"위험행동: {r}")

    # 현실 데이터 일부 시각화
    st.divider()
    st.subheader("📊 현실 통계 보기")
    for key, df in data.items():
        if df is not None:
            st.write(f"**{key} 데이터 미리보기**")
            st.dataframe(df.head())

    if st.button("다시 하기"):
        for key in ["stage", "mental", "physical", "risk"]:
            if key in st.session_state:
                del st.session_state[key]
        st.experimental_rerun()
