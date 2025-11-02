import streamlit as st
import pandas as pd
import random

# -------------------- App Settings --------------------
st.set_page_config(page_title="청소년 사회문제 시뮬레이터", page_icon="🧠", layout="centered")
st.markdown("<h1 style='text-align:center;'>🧠 청소년 사회문제 시뮬레이터</h1>", unsafe_allow_html=True)
st.write("하루하루의 선택이 너의 정신 건강과 사회적 안전에 어떤 영향을 주는지 체험해보자.")

# -------------------- 캐릭터 설정 --------------------
CHARACTER = {
    "name": "루미",
    "emoji": "🤖",
    "color": "#6C63FF",
}

# -------------------- 초기 세션 --------------------
if "stage" not in st.session_state:
    st.session_state.stage = 0
    st.session_state.stats = {"mental": 5, "physical": 5, "risk": 0}
    st.session_state.history = []

# -------------------- 시나리오 데이터 --------------------
SCENARIOS = [
    {
        "id": "start",
        "text": "새 학기가 시작되었어. 반에 적응해야 해. 친구가 먼저 말을 걸어왔어. '같이 점심 먹을래?'",
        "choices": [
            {"text": "응 고마워!", "effects": {"mental": +2, "physical": +1, "risk": 0}, "tags": []},
            {"text": "아니, 혼자 먹을래.", "effects": {"mental": -1, "physical": 0, "risk": 0}, "tags": []}
        ]
    },
    {
        "id": "study_pressure",
        "text": "시험 기간이 다가와. 공부를 더 해야 할까?",
        "choices": [
            {"text":"열심히 공부할래. 밤샘도 해볼까.", "effects": {"mental": -2, "physical": -2, "risk": 0}, "tags": []},
            {"text":"조금만 하고 쉴래.", "effects": {"mental": +1, "physical": +1, "risk": 0}, "tags": []}
        ]
    },
    {
        "id": "party_offer",
        "text": "친구에게서 파티 초대 메시지가 왔어. 여기서 뭔가를 권유받을 수 있어.",
        "choices":[
            {"text":"갈래, 재밌겠다.", "effects": {"mental": +1, "physical": -1, "risk": +1}, "tags": ["drugs"]},
            {"text":"가지 않을래.", "effects": {"mental": 0, "physical": 0, "risk": 0}, "tags": []}
        ]
    },
    {
        "id": "loan_message",
        "text": "모르는 번호로 '빠른 돈 벌이, 소액 대출 필요?' 라는 메시지가 왔어.",
        "choices":[
            {"text":"연결해볼래 (Yes)", "effects": {"mental": -2, "physical": 0, "risk": +2}, "tags":["gamble"]},
            {"text":"무시할래 (No)", "effects": {"mental": +0, "physical": 0, "risk": 0}, "tags": []}
        ]
    },
    {
        "id": "bully_event",
        "text": "같은 반 친구가 온라인에서 너를 놀리는 글을 올렸어.",
        "choices":[
            {"text":"맞대응 한다.", "effects": {"mental": -2, "physical": 0, "risk": +1}, "tags":["bully"]},
            {"text":"증거를 모아 상담선생님에게 말한다.", "effects": {"mental": +1, "physical": 0, "risk": -1}, "tags": []}
        ]
    }
]

# -------------------- 데이터 기반 리포트 --------------------
def generate_report(stats):
    try:
        df_dep = pd.read_csv("청소년_우울증.csv")
        df_su = pd.read_csv("청소년_자살시도율.csv")
        df_soc = pd.read_csv("사회문제_위험_노출_정도_20251102160905.csv")

        dep_avg = df_dep["우울 경험률"].mean()
        su_avg = df_su["자살시도율"].mean()
        risk_avg = df_soc["위험노출정도"].mean()

        # 사용자 점수 기반 분석
        user_risk = stats["risk"] * 10
        diff = user_risk - risk_avg
        msg = f"당신의 위험 지수는 평균보다 {abs(diff):.1f}% {'높습니다 🔺' if diff>0 else '낮습니다 🔻'}."
        return msg
    except Exception as e:
        return "⚠️ 데이터 분석 중 오류가 발생했어요. (파일 확인 필요)"

# -------------------- 대화 시뮬레이션 --------------------
def render_chat(scenario):
    st.markdown(
        f"""
        <div style="background-color:{CHARACTER['color']}; padding:10px; border-radius:12px; color:white; margin-bottom:10px;">
        {CHARACTER['emoji']} <b>{CHARACTER['name']}</b>: {scenario['text']}
        </div>
        """, unsafe_allow_html=True)

    for choice in scenario["choices"]:
        if st.button(choice["text"], use_container_width=True):
            for stat, delta in choice["effects"].items():
                st.session_state.stats[stat] += delta
            st.session_state.history.append((scenario["id"], choice["text"]))
            st.session_state.stage += 1
            st.rerun()

# -------------------- 메인 진행 --------------------
if st.session_state.stage < len(SCENARIOS):
    scenario = SCENARIOS[st.session_state.stage]
    render_chat(scenario)
else:
    st.success("🎉 시뮬레이션 완료!")
    st.write("당신의 상태 요약:")
    st.write(st.session_state.stats)

    st.markdown("### 📊 현실 데이터 기반 리포트")
    report = generate_report(st.session_state.stats)
    st.info(report)

    st.markdown("---")
    if st.button("다시 시작하기 🔁"):
        st.session_state.stage = 0
        st.session_state.stats = {"mental": 5, "physical": 5, "risk": 0}
        st.session_state.history = []
        st.rerun()
