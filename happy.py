import streamlit as st
import pandas as pd
import random

# -------------------- App Settings --------------------
st.set_page_config(page_title="청소년 생명존중 시뮬레이터", page_icon="💙", layout="centered")

# -------------------- 초기 세션 --------------------
if "game_started" not in st.session_state:
    st.session_state.game_started = False
    st.session_state.gender = None
    st.session_state.stage = 0
    st.session_state.stats = {"mental": 50, "physical": 50, "risk": 0, "happiness": 50}
    st.session_state.history = []
    st.session_state.character_name = "루미"

# -------------------- 시나리오 데이터 (가중치 반영) --------------------
SCENARIOS = [
    {
        "id": "start",
        "text": "새 학기가 시작되었어. 반에 적응이 잘 안 돼서 힘들어. 그때 반 친구가 다가와서 말을 걸었어. '같이 점심 먹을래?'",
        "choices": [
            {
                "text": "😊 응, 고마워! 같이 먹자.",
                "effects": {"mental": +10, "physical": +5, "risk": 0, "happiness": +10},
                "feedback": "좋은 선택이야! 친구와의 관계는 정신 건강에 정말 중요해."
            },
            {
                "text": "😔 아니, 괜찮아. 혼자 먹을래.",
                "effects": {"mental": -5, "physical": 0, "risk": +5, "happiness": -5},
                "feedback": "혼자 있고 싶을 수도 있지만, 때로는 누군가와 함께하는 게 도움이 돼."
            }
        ]
    },
    {
        "id": "study_pressure",
        "text": "시험이 일주일 앞으로 다가왔어. 성적에 대한 부담이 너무 커. 어떻게 할까?",
        "choices": [
            {
                "text": "📚 밤을 새워서라도 완벽하게 준비할 거야.",
                "effects": {"mental": -15, "physical": -20, "risk": +10, "happiness": -10},
                "feedback": "과도한 학습은 오히려 건강을 해칠 수 있어. 휴식도 공부의 일부야."
            },
            {
                "text": "⏰ 규칙적으로 공부하고 충분히 쉴 거야.",
                "effects": {"mental": +5, "physical": +10, "risk": 0, "happiness": +5},
                "feedback": "현명한 선택이야! 균형 잡힌 생활이 최고의 성과를 만들어."
            },
            {
                "text": "😰 너무 부담돼서 아예 포기하고 싶어.",
                "effects": {"mental": -20, "physical": -5, "risk": +15, "happiness": -20},
                "feedback": "힘들 때는 선생님이나 상담사와 이야기해봐. 혼자 감당하지 않아도 돼."
            }
        ]
    },
    {
        "id": "social_media",
        "text": "SNS에서 친구들이 올린 게시물을 보니 다들 행복해 보여. 나만 뒤처진 것 같아.",
        "choices": [
            {
                "text": "📱 SNS를 더 자주 확인하면서 비교해.",
                "effects": {"mental": -15, "physical": 0, "risk": +10, "happiness": -15},
                "feedback": "SNS는 현실의 일부만 보여줘. 비교는 우울감을 키울 수 있어."
            },
            {
                "text": "🚶 SNS를 잠시 끄고 내 취미 활동을 해.",
                "effects": {"mental": +10, "physical": +5, "risk": 0, "happiness": +10},
                "feedback": "좋아! 나만의 시간을 갖는 건 정신 건강에 큰 도움이 돼."
            }
        ]
    },
    {
        "id": "party_offer",
        "text": "선배가 주말 파티에 초대했어. 거기서 담배나 술을 권유받을 수도 있대.",
        "choices": [
            {
                "text": "🎉 가볼래. 친구들이랑 있으면 괜찮겠지.",
                "effects": {"mental": 0, "physical": -10, "risk": +20, "happiness": -5},
                "feedback": "또래 압력은 강하지만, 위험한 행동은 장기적으로 해로워."
            },
            {
                "text": "🏠 정중히 거절하고 집에서 쉴래.",
                "effects": {"mental": +5, "physical": +5, "risk": 0, "happiness": +5},
                "feedback": "자신의 건강을 우선시하는 건 용기 있는 선택이야!"
            }
        ]
    },
    {
        "id": "smoking_offer",
        "text": "친구가 담배를 권했어. '한 번만 피워봐, 스트레스 풀린다니까.'",
        "choices": [
            {
                "text": "🚬 한 번쯤은 괜찮겠지. 피워볼래.",
                "effects": {"mental": -10, "physical": -15, "risk": +25, "happiness": -10},
                "feedback": "청소년 흡연율이 증가하고 있어. 담배는 중독성이 강하고 건강을 해쳐."
            },
            {
                "text": "🙅 아니, 나는 안 피울래.",
                "effects": {"mental": +10, "physical": +10, "risk": 0, "happiness": +10},
                "feedback": "훌륭해! 또래 압력을 이겨낸 거야. 네 건강이 최우선이야."
            }
        ]
    },
    {
        "id": "cyberbullying",
        "text": "같은 반 친구가 너에 대한 악플을 SNS에 올렸어. 많은 친구들이 봤어.",
        "choices": [
            {
                "text": "😡 똑같이 악플로 맞대응할 거야.",
                "effects": {"mental": -15, "physical": 0, "risk": +15, "happiness": -15},
                "feedback": "맞대응은 상황을 악화시킬 수 있어. 더 나은 방법이 있어."
            },
            {
                "text": "📸 증거를 모아서 선생님께 말씀드릴 거야.",
                "effects": {"mental": +10, "physical": 0, "risk": -10, "happiness": +5},
                "feedback": "현명한 선택이야! 어른의 도움을 받는 건 약한 게 아니야."
            },
            {
                "text": "😢 아무에게도 말 안 하고 혼자 참을 거야.",
                "effects": {"mental": -25, "physical": -10, "risk": +20, "happiness": -25},
                "feedback": "혼자 감당하지 마. 도움을 요청하는 건 용기 있는 행동이야."
            }
        ]
    },
    {
        "id": "loan_message",
        "text": "모르는 번호에서 '쉽고 빠른 소액 대출, 학생도 가능!' 이런 문자가 왔어.",
        "choices": [
            {
                "text": "💰 연락해볼까? 용돈이 필요하긴 해.",
                "effects": {"mental": -15, "physical": 0, "risk": +30, "happiness": -15},
                "feedback": "불법 대출은 심각한 범죄에 연루될 수 있어. 절대 연락하지 마."
            },
            {
                "text": "🚫 무시하고 차단할 거야.",
                "effects": {"mental": +5, "physical": 0, "risk": 0, "happiness": +5},
                "feedback": "잘했어! 의심스러운 연락은 무시하는 게 최선이야."
            }
        ]
    },
    {
        "id": "mental_crisis",
        "text": "요즘 너무 힘들어. 아무것도 하기 싫고, 모든 게 무의미하게 느껴져.",
        "choices": [
            {
                "text": "💊 혼자서 해결해야지. 아무에게도 말 안 할 거야.",
                "effects": {"mental": -30, "physical": -15, "risk": +35, "happiness": -30},
                "feedback": "힘들 때는 도움을 요청해야 해. 청소년상담전화 1388에 전화해봐."
            },
            {
                "text": "📞 부모님이나 상담 선생님께 이야기해볼 거야.",
                "effects": {"mental": +20, "physical": +10, "risk": -15, "happiness": +20},
                "feedback": "정말 용기 있는 선택이야! 도움을 청하는 건 강한 사람만이 할 수 있어."
            },
            {
                "text": "🏃 운동이나 취미 활동으로 기분 전환을 해볼 거야.",
                "effects": {"mental": +10, "physical": +15, "risk": 0, "happiness": +15},
                "feedback": "좋은 방법이야! 그래도 증상이 계속되면 전문가와 상담하는 게 좋아."
            }
        ]
    }
]

# -------------------- 데이터 로드 함수 --------------------
@st.cache_data
def load_statistics():
    """CSV 파일들을 로드하고 통계 데이터를 반환"""
    try:
        stats = {}
        
        # 우울증 데이터
        try:
            df_dep = pd.read_csv("청소년_우울증.csv", encoding='utf-8-sig')
            stats['depression'] = df_dep["우울 경험률"].mean() if "우울 경험률" in df_dep.columns else 25.0
        except:
            stats['depression'] = 25.0  # 기본값
        
        # 자살시도율 데이터
        try:
            df_su = pd.read_csv("청소년_자살시도율.csv", encoding='utf-8-sig')
            stats['suicide'] = df_su["자살시도율"].mean() if "자살시도율" in df_su.columns else 2.5
        except:
            stats['suicide'] = 2.5  # 기본값
        
        # 사회문제 노출 데이터
        try:
            df_soc = pd.read_csv("사회문제_위험_노출_정도_20251102160905.csv", encoding='utf-8-sig')
            stats['risk_exposure'] = df_soc["위험노출정도"].mean() if "위험노출정도" in df_soc.columns else 15.0
        except:
            stats['risk_exposure'] = 15.0  # 기본값
        
        # 흡연율 데이터 (예시)
        stats['smoking'] = 6.0  # 청소년 흡연율 약 6%
        
        return stats
    except Exception as e:
        return {
            'depression': 25.0,
            'suicide': 2.5,
            'risk_exposure': 15.0,
            'smoking': 6.0
        }

# -------------------- 게임 결과 분석 --------------------
def analyze_result(stats, real_stats):
    """최종 결과를 분석하여 엔딩 결정"""
    mental = stats['mental']
    risk = stats['risk']
    happiness = stats['happiness']
    
    if mental >= 60 and happiness >= 60 and risk <= 20:
        return "happy", "🌟 행복한 청소년", "#4CAF50"
    elif mental <= 30 or happiness <= 30:
        if risk >= 40:
            return "crisis", "⚠️ 위기 상황", "#F44336"
        else:
            return "depressed", "😔 우울 위험", "#FF9800"
    elif risk >= 50:
        return "high_risk", "🚨 고위험 행동", "#D32F2F"
    else:
        return "normal", "😐 평범한 일상", "#2196F3"

def get_ending_message(ending_type, stats, real_stats):
    """엔딩 타입에 따른 메시지 반환"""
    messages = {
        "happy": f"""
        🎉 **축하해요!** 당신은 건강한 선택들을 통해 행복한 청소년기를 보내고 있어요.
        
        당신의 정신 건강 지수는 {stats['mental']}점으로, 평균 이상이에요.
        이런 긍정적인 태도를 계속 유지해주세요!
        """,
        "depressed": f"""
        💙 **괜찮아요, 도움을 받을 수 있어요.**
        
        당신의 정신 건강 지수는 {stats['mental']}점입니다.
        실제로 청소년의 약 {real_stats['depression']:.1f}%가 우울을 경험하고 있어요.
        
        🆘 **도움받을 수 있는 곳:**
        - 청소년상담전화: **1388** (24시간)
        - 자살예방상담전화: **1393** (24시간)
        - 학교 상담실
        - 정신건강복지센터
        
        혼자가 아니에요. 언제든 도움을 요청하세요.
        """,
        "crisis": f"""
        🚨 **지금 당장 도움이 필요해요!**
        
        당신의 상태는 매우 위험한 수준입니다.
        청소년 자살시도율은 {real_stats['suicide']:.1f}%이지만, 대부분은 도움을 받아 회복했어요.
        
        🆘 **즉시 연락하세요:**
        - 🚨 **응급상황: 119**
        - 📞 **자살예방상담전화: 1393** (24시간)
        - 📱 **청소년상담전화: 1388** (24시간)
        
        당신의 생명은 소중합니다. 지금 전화하세요.
        """,
        "high_risk": f"""
        ⚠️ **위험한 행동을 멈춰야 해요.**
        
        당신의 위험 행동 지수는 {stats['risk']}점입니다.
        청소년의 {real_stats['risk_exposure']:.1f}%가 위험한 환경에 노출되어 있어요.
        
        흡연, 음주, 불법 대출 등은 당장은 문제가 없어 보여도
        장기적으로 큰 피해를 줄 수 있어요.
        
        📞 **상담받기:**
        - 청소년상담전화: **1388**
        - 학교폭력신고: **117**
        """,
        "normal": f"""
        😊 **나쁘지 않아요!**
        
        당신은 평범한 청소년기를 보내고 있어요.
        때로는 힘들 수도 있지만, 좋은 선택을 계속하면
        더 행복한 미래를 만들 수 있어요.
        
        정신 건강: {stats['mental']}점
        행복 지수: {stats['happiness']}점
        """
    }
    return messages.get(ending_type, messages["normal"])

# -------------------- 메인 화면 --------------------
st.markdown("<h1 style='text-align:center;'>💙 청소년 생명존중 시뮬레이터</h1>", unsafe_allow_html=True)

# 게임 시작 전 화면
if not st.session_state.game_started:
    st.markdown("---")
    st.markdown("""
    ### 🎮 게임 소개
    이 시뮬레이터는 청소년기에 마주할 수 있는 다양한 상황과 선택을 체험하는 게임입니다.
    
    - 여러 가지 상황에서 **선택**을 하게 됩니다
    - 선택에 따라 **정신건강, 육체건강, 위험도, 행복도**가 변합니다
    - 마지막에 **실제 통계 데이터**와 비교한 결과를 보여드립니다
    
    💡 **목적**: 생명의 소중함을 깨닫고, 위기 상황에서 도움을 청하는 것의 중요성을 배웁니다.
    """)
    
    st.markdown("---")
    st.markdown("### 👤 캐릭터 설정")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🙋‍♂️ 남성", use_container_width=True, type="primary"):
            st.session_state.gender = "male"
            st.session_state.game_started = True
            st.session_state.character_name = "민준"
            st.rerun()
    
    with col2:
        if st.button("🙋‍♀️ 여성", use_container_width=True, type="primary"):
            st.session_state.gender = "female"
            st.session_state.game_started = True
            st.session_state.character_name = "서연"
            st.rerun()
    
    st.markdown("---")
    st.markdown("""
    <div style='background-color: #FFF3CD; padding: 15px; border-radius: 10px; border-left: 5px solid #FFC107;'>
    <b>⚠️ 중요한 안내</b><br>
    게임 중 힘든 감정이 들거나 도움이 필요하면:<br>
    📞 청소년상담전화 <b>1388</b> (24시간)<br>
    📞 자살예방상담전화 <b>1393</b> (24시간)
    </div>
    """, unsafe_allow_html=True)

# 게임 진행 화면
elif st.session_state.stage < len(SCENARIOS):
    # 상태 표시
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        mental_color = "#4CAF50" if st.session_state.stats['mental'] >= 50 else "#FF5252"
        st.markdown(f"<div style='text-align:center; padding:10px; background-color:{mental_color}20; border-radius:8px;'>"
                   f"<b>🧠 정신건강</b><br>{st.session_state.stats['mental']}</div>", unsafe_allow_html=True)
    
    with col2:
        physical_color = "#4CAF50" if st.session_state.stats['physical'] >= 50 else "#FF5252"
        st.markdown(f"<div style='text-align:center; padding:10px; background-color:{physical_color}20; border-radius:8px;'>"
                   f"<b>💪 신체건강</b><br>{st.session_state.stats['physical']}</div>", unsafe_allow_html=True)
    
    with col3:
        risk_color = "#4CAF50" if st.session_state.stats['risk'] <= 20 else "#FF5252"
        st.markdown(f"<div style='text-align:center; padding:10px; background-color:{risk_color}20; border-radius:8px;'>"
                   f"<b>⚠️ 위험도</b><br>{st.session_state.stats['risk']}</div>", unsafe_allow_html=True)
    
    with col4:
        happiness_color = "#4CAF50" if st.session_state.stats['happiness'] >= 50 else "#FF5252"
        st.markdown(f"<div style='text-align:center; padding:10px; background-color:{happiness_color}20; border-radius:8px;'>"
                   f"<b>😊 행복도</b><br>{st.session_state.stats['happiness']}</div>", unsafe_allow_html=True)
    
    st.markdown("---")
    
    # 진행도 표시
    progress = (st.session_state.stage + 1) / len(SCENARIOS)
    st.progress(progress)
    st.markdown(f"<p style='text-align:center; color:#666;'>상황 {st.session_state.stage + 1} / {len(SCENARIOS)}</p>", unsafe_allow_html=True)
    
    # 현재 시나리오
    scenario = SCENARIOS[st.session_state.stage]
    
    # 대화 형식으로 표시
    gender_emoji = "🙋‍♂️" if st.session_state.gender == "male" else "🙋‍♀️"
    st.markdown(
        f"""
        <div style="background-color:#E3F2FD; padding:15px; border-radius:12px; margin-bottom:15px; border-left:4px solid #2196F3;">
        {gender_emoji} <b>{st.session_state.character_name}</b><br>
        <span style="font-size:16px;">{scenario['text']}</span>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("#### 💭 어떻게 할까?")
    
    # 선택지 버튼
    for idx, choice in enumerate(scenario["choices"]):
        if st.button(choice["text"], key=f"choice_{idx}", use_container_width=True):
            # 스탯 업데이트
            for stat, delta in choice["effects"].items():
                st.session_state.stats[stat] = max(0, min(100, st.session_state.stats[stat] + delta))
            
            # 히스토리 저장
            st.session_state.history.append({
                "scenario": scenario["id"],
                "choice": choice["text"],
                "feedback": choice["feedback"]
            })
            
            # 피드백 표시
            st.session_state.last_feedback = choice["feedback"]
            st.session_state.stage += 1
            st.rerun()
    
    # 이전 선택 피드백 표시
    if "last_feedback" in st.session_state and st.session_state.last_feedback:
        st.markdown("---")
        st.info(f"💬 {st.session_state.last_feedback}")

# 게임 종료 화면
else:
    st.balloons()
    st.markdown("---")
    st.markdown("<h2 style='text-align:center;'>🎉 시뮬레이션 완료!</h2>", unsafe_allow_html=True)
    
    # 통계 로드
    real_stats = load_statistics()
    
    # 결과 분석
    ending_type, ending_title, ending_color = analyze_result(st.session_state.stats, real_stats)
    
    # 엔딩 타이틀
    st.markdown(
        f"""
        <div style="background-color:{ending_color}; padding:20px; border-radius:15px; text-align:center; color:white; margin:20px 0;">
        <h2>{ending_title}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    # 최종 스탯
    st.markdown("### 📊 당신의 최종 상태")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("🧠 정신건강", f"{st.session_state.stats['mental']}/100")
    with col2:
        st.metric("💪 신체건강", f"{st.session_state.stats['physical']}/100")
    with col3:
        st.metric("⚠️ 위험도", f"{st.session_state.stats['risk']}/100")
    with col4:
        st.metric("😊 행복도", f"{st.session_state.stats['happiness']}/100")
    
    st.markdown("---")
    
    # 엔딩 메시지
    st.markdown(get_ending_message(ending_type, st.session_state.stats, real_stats))
    
    st.markdown("---")
    
    # 실제 통계 데이터 비교
    st.markdown("### 📈 실제 청소년 통계와 비교")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"""
        <div style='background-color:#F5F5F5; padding:15px; border-radius:10px;'>
        <b>📊 우울 경험률</b><br>
        청소년 중 약 <span style='color:#FF5252; font-size:20px;'>{real_stats['depression']:.1f}%</span>가<br>
        우울감을 경험하고 있습니다.
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div style='background-color:#F5F5F5; padding:15px; border-radius:10px; margin-top:10px;'>
        <b>🚬 흡연율</b><br>
        청소년 흡연율: <span style='color:#FF5252; font-size:20px;'>{real_stats['smoking']:.1f}%</span>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div style='background-color:#F5F5F5; padding:15px; border-radius:10px;'>
        <b>⚠️ 자살시도율</b><br>
        청소년 중 약 <span style='color:#FF5252; font-size:20px;'>{real_stats['suicide']:.1f}%</span>가<br>
        자살을 시도한 경험이 있습니다.
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div style='background-color:#F5F5F5; padding:15px; border-radius:10px; margin-top:10px;'>
        <b>🔴 사회문제 노출</b><br>
        위험 노출도: <span style='color:#FF5252; font-size:20px;'>{real_stats['risk_exposure']:.1f}%</span>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # 생명존중 메시지
    st.markdown("""
    <div style='background-color:#E8F5E9; padding:20px; border-radius:10px; border-left:5px solid #4CAF50;'>
    <h3>💚 당신은 소중한 사람입니다</h3>
    <p>
    힘든 순간이 있더라도, 당신의 생명은 무엇보다 소중합니다.<br>
    도움을 청하는 것은 약한 것이 아니라 <b>용기있는 행동</b>입니다.<br>
    혼자 감당하지 말고, 언제든 주변에 도움을 요청하세요.
    </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # 도움 받을 수 있는 곳
    st.markdown("### 📞 도움받을 수 있는 곳")
    
    help_info
