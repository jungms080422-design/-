import streamlit as st
import pandas as pd
import plotly.express as px
import random

# -------------------- App Settings --------------------
st.set_page_config(page_title="청소년 생명존중 시뮬레이터", page_icon="💙", layout="centered")

                
# -------------------------------
# 데이터 로드 (여성가족부 센터 현황)
# -------------------------------

@st.cache_data
def load_center_df():
    try:
        df = pd.read_csv(
            "https://raw.githubusercontent.com/jungms080422-design/-/main/adolscenve.csv"
        )
        df.columns = df.columns.str.strip()
        return df
    except Exception as e:
        st.error(f"센터 현황 CSV를 불러오지 못했습니다: {e}")
        return pd.DataFrame()

def _pick_col(df, candidates):
    """후보 리스트 중 실제 존재하는 첫 컬럼명을 반환(없으면 None)"""
    for c in candidates:
        if c in df.columns:
            return c
    return None

def render_center_map():
    """엔딩 화면 하단에 표시할 상담센터 지도"""
    df = load_center_df()
    st.markdown("## 🧭 여성가족부 청소년상담복지센터 현황 지도")

    if df.empty:
        st.info("센터 현황 데이터를 불러오지 못해 지도를 생략합니다.")
        return

    # 컬럼명 정규화
    df.columns = df.columns.str.strip()

    # 지역/시군구 컬럼 자동 탐색
    region_col = _pick_col(df, ["지역", "광역시도", "시도"])
    sigungu_col = _pick_col(df, ["시군구명", "시군구", "군구"])

    if region_col is None:
        st.warning("CSV에 지역(예: '지역', '광역시도', '시도') 컬럼이 없습니다.")
        return
    if sigungu_col is None:
        st.warning("CSV에 시군구(예: '시군구명', '시군구') 컬럼이 없습니다.")
        return

    # 지역 선택
    region_list = sorted(df[region_col].dropna().unique())
    selected_region = st.selectbox("광역시도 선택", region_list, key="map_region")

    # 시군구 선택
    filtered_df_region = df[df[region_col] == selected_region]
    sigungu_list = sorted(filtered_df_region[sigungu_col].dropna().unique())
    selected_sigungu = st.selectbox("시군구 선택", sigungu_list, key="map_sigungu")

    # 선택된 지역의 센터 필터링 (여기서도 같은 컬럼명을 사용!)
    filtered_df = filtered_df_region[filtered_df_region[sigungu_col] == selected_sigungu]

    # 위도/경도 컬럼 탐색(부분 일치 허용)
    lat_col = next((c for c in filtered_df.columns if "위도" in c), None)
    lon_col = next((c for c in filtered_df.columns if "경도" in c), None)

    if lat_col and lon_col:
        try:
            fig = px.scatter_mapbox(
                filtered_df,
                lat=lat_col,
                lon=lon_col,
                hover_name=("시설명" if "시설명" in filtered_df.columns else filtered_df.columns[0]),
                hover_data={"주소": True, lat_col: False, lon_col: False} if "주소" in filtered_df.columns else None,
                color_discrete_sequence=["#FF6699"],
                zoom=10,
                height=600
            )
            fig.update_layout(
                mapbox_style="open-street-map",
                margin={"r": 0, "t": 0, "l": 0, "b": 0}
            )
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"지도를 그리는 중 오류가 발생했습니다: {e}")
    else:
        st.error("❌ 위도/경도 정보가 없습니다. CSV에 '위도', '경도'(또는 유사명) 컬럼이 있는지 확인해주세요!")



# -------------------- 초기 세션 --------------------
if "game_started" not in st.session_state:
    st.session_state.game_started = False
    st.session_state.gender = None
    st.session_state.stage = 0
    st.session_state.stats = {"mental": 50, "physical": 50, "risk": 0, "happiness": 50}
    st.session_state.history = []
    st.session_state.character_name = "루미"

# -------------------- 확장된 시나리오 데이터 --------------------
SCENARIOS = [
    {
        "id": "first_day",
        "text": "고등학교 1학년 첫날이다. 새로운 환경에 적응해야 한다. 점심시간, 아는 사람이 한 명도 없는 교실에서 혼자 있는데 옆 자리 학생이 말을 건넨다. '안녕! 나는 지민이야. 같이 점심 먹을래?'",
        "choices": [
            {
                "text": "😊 '응! 좋아. 나는 [이름]이야. 반가워!'",
                "effects": {"mental": +10, "physical": +5, "risk": 0, "happiness": +12},
                "feedback": "좋은 선택이야! 새로운 친구를 사귀는 것은 학교 생활 적응에 정말 중요해. 사회적 관계는 정신 건강의 핵심 요소야."
            },
            {
                "text": "😐 '어... 미안, 나 혼자 먹고 싶어.'",
                "effects": {"mental": -8, "physical": 0, "risk": +8, "happiness": -7},
                "feedback": "혼자 있고 싶을 수도 있지만, 지속적인 고립은 우울감을 키울 수 있어. 때로는 용기를 내서 다가가는 것도 필요해."
            },
            {
                "text": "😶 아무 말 없이 고개만 끄덕이고 계속 핸드폰을 본다.",
                "effects": {"mental": -5, "physical": 0, "risk": +5, "happiness": -5},
                "feedback": "소극적인 반응은 관계 형성의 기회를 놓치게 해. 작은 대화 한 마디가 큰 변화를 만들 수 있어."
            }
        ]
    },
    {
        "id": "exam_stress",
        "text": "첫 중간고사가 2주 앞으로 다가왔다. 부모님의 기대가 크고, 성적 때문에 스트레스가 심하다. 밤 11시, 아직도 책상 앞에 앉아 있는데 공부가 잘 안 된다.",
        "choices": [
            {
                "text": "📚 '밤을 새워서라도 완벽하게 준비해야 해!'",
                "effects": {"mental": -18, "physical": -22, "risk": +12, "happiness": -15},
                "feedback": "과도한 학습과 수면 부족은 오히려 학습 능력을 떨어뜨려. 뇌는 잠을 자는 동안 기억을 정리해. 적절한 휴식이 더 좋은 성적을 만들어."
            },
            {
                "text": "⏰ '오늘은 자고, 내일부터 계획적으로 공부하자.'",
                "effects": {"mental": +8, "physical": +12, "risk": 0, "happiness": +8},
                "feedback": "현명한 선택이야! 규칙적인 수면과 계획적인 학습이 최고의 시험 준비법이야. 균형 잡힌 생활이 성공의 지름길이야."
            },
            {
                "text": "😰 '어차피 안 될 거 같아. 그냥 포기하고 게임이나 할까...'",
                "effects": {"mental": -25, "physical": -8, "risk": +18, "happiness": -22},
                "feedback": "학업 스트레스는 모두가 겪는 일이야. 포기하기보다는 선생님이나 상담사와 이야기해봐. 작은 목표부터 시작하면 돼."
            },
            {
                "text": "💬 '부모님께 솔직하게 부담을 말씀드려볼까.'",
                "effects": {"mental": +12, "physical": +5, "risk": -5, "happiness": +10},
                "feedback": "정말 용기 있는 선택이야! 솔직한 대화는 오해를 풀고 서로를 이해하는 첫걸음이야. 부모님도 네 건강이 우선이라고 생각하실 거야."
            }
        ]
    },
    {
        "id": "social_media_compare",
        "text": "저녁 9시, SNS를 보다가 같은 반 친구들의 게시물을 발견했다. 다들 예쁘게 꾸미고 친구들과 즐거운 시간을 보내는 사진들뿐이다. '나만 혼자인 것 같고, 나만 뒤처진 것 같아...'",
        "choices": [
            {
                "text": "📱 SNS를 계속 보면서 다른 친구들 게시물도 확인한다.",
                "effects": {"mental": -20, "physical": 0, "risk": +15, "happiness": -18},
                "feedback": "SNS는 현실의 일부만 보여줘. 모두가 좋은 순간만 올리기 때문에 비교하면 우울감이 커질 수 있어. SNS 속 삶은 편집된 버전이라는 걸 기억해."
            },
            {
                "text": "🚶 '이건 도움이 안 돼.' 핸드폰을 끄고 산책을 나간다.",
                "effects": {"mental": +15, "physical": +10, "risk": 0, "happiness": +12},
                "feedback": "훌륭한 선택이야! 디지털 디톡스는 정신 건강에 큰 도움이 돼. 직접 경험하는 현실의 시간이 훨씬 가치 있어."
            },
            {
                "text": "📝 일기를 쓰면서 내 감정을 정리해본다.",
                "effects": {"mental": +12, "physical": +5, "risk": 0, "happiness": +10},
                "feedback": "감정 일기는 자기 이해를 돕는 좋은 방법이야. 자신의 감정을 인식하고 표현하는 건 정신 건강의 기본이야."
            },
            {
                "text": "💬 친한 친구에게 내 기분을 솔직하게 이야기한다.",
                "effects": {"mental": +18, "physical": +5, "risk": 0, "happiness": +15},
                "feedback": "완벽해! 감정을 나누는 것은 외로움을 줄이고 친밀감을 높여. 진짜 친구는 네 약한 모습도 받아줄 거야."
            }
        ]
    },
    {
        "id": "senior_party",
        "text": "금요일 저녁, 3학년 선배가 단체 채팅방에 메시지를 보냈다. '이번 주말에 MT 가는데 같이 갈래? 엄청 재밌을 거야. 술도 좀 마시고 담배도 피우고~' 친구들 대부분이 간다고 한다.",
        "choices": [
            {
                "text": "🎉 '다들 가니까 나도 가야지. 안 가면 왕따당할 것 같아.'",
                "effects": {"mental": -5, "physical": -15, "risk": +28, "happiness": -8},
                "feedback": "또래 압력은 강하지만, 위험한 행동은 장기적으로 해로워. 진짜 친구라면 네 선택을 존중할 거야. 청소년 음주는 뇌 발달에 심각한 영향을 줄 수 있어."
            },
            {
                "text": "🏠 '미안, 주말에 가족 약속이 있어서 못 갈 것 같아.'",
                "effects": {"mental": +10, "physical": +8, "risk": 0, "happiness": +8},
                "feedback": "자신의 안전을 우선하는 건 현명한 판단이야. 거절하는 것도 용기야. 건강한 경계를 설정하는 법을 배우는 중이야."
            },
            {
                "text": "🤔 '술이랑 담배는 빼고 갈 수는 없어?'라고 물어본다.",
                "effects": {"mental": +5, "physical": +5, "risk": +5, "happiness": +5},
                "feedback": "타협점을 찾으려는 시도는 좋지만, 그런 자리에서는 압력이 클 수 있어. 자신의 의지를 지킬 자신이 있다면 괜찮아."
            },
            {
                "text": "😊 '나는 안 갈게. 대신 다음에 영화 보러 가자!'",
                "effects": {"mental": +12, "physical": +10, "risk": 0, "happiness": +12},
                "feedback": "완벽해! 대안을 제시하면서 거절하는 건 사회성과 자기 보호를 모두 지키는 방법이야. 친구들도 네 솔직함을 존중할 거야."
            }
        ]
    },
    {
        "id": "smoking_pressure",
        "text": "쉬는 시간, 화장실에서 같은 반 친구 몇 명이 담배를 피우고 있다. '너도 한 대 피워봐. 스트레스 풀린다니까. 아무도 모르게 할 수 있어.' 친구들이 담배를 권한다.",
        "choices": [
            {
                "text": "🚬 '한 번쯤은 괜찮겠지...' 호기심에 받아든다.",
                "effects": {"mental": -15, "physical": -20, "risk": +30, "happiness": -12},
                "feedback": "청소년 흡연율은 약 6%야. 담배는 중독성이 매우 강하고, 한 번의 시작이 평생의 습관이 될 수 있어. 뇌가 발달 중인 청소년기에는 특히 위험해."
            },
            {
                "text": "🙅 '아니, 난 안 피울래. 건강에 안 좋잖아.'",
                "effects": {"mental": +15, "physical": +12, "risk": 0, "happiness": +15},
                "feedback": "훌륭해! 또래 압력을 이겨낸 거야. 자신의 신념을 지키는 건 정말 강한 사람만이 할 수 있는 거야. 네 건강이 최우선이야."
            },
            {
                "text": "🚪 아무 말 없이 화장실을 나온다.",
                "effects": {"mental": +8, "physical": +8, "risk": 0, "happiness": +5},
                "feedback": "위험한 상황에서 벗어나는 것도 좋은 선택이야. 하지만 명확한 거절이 더 확실한 방법일 수 있어."
            },
            {
                "text": "📢 '선생님께 말씀드려야 할 것 같아. 우리 모두를 위해서.'",
                "effects": {"mental": +10, "physical": +10, "risk": -10, "happiness": +8},
                "feedback": "용기 있는 선택이야! 고자질이 아니라 친구들의 건강을 걱정하는 거야. 때로는 어려운 선택이 옳은 선택이야."
            }
        ]
    },
    {
        "id": "online_bullying",
        "text": "월요일 아침 등교 길, 친구에게서 급한 전화가 왔다. 지난 주말에 찍힌 네 사진이 단체 채팅방에 올라왔고, 여러 명이 외모를 비하하는 댓글을 달았다고 한다. 학교에 도착하니 사람들이 힐끗힐끗 쳐다본다.",
        "choices": [
            {
                "text": "😡 '나도 걔들 사진 찍어서 똑같이 올려버릴 거야!'",
                "effects": {"mental": -18, "physical": 0, "risk": +20, "happiness": -20},
                "feedback": "맞대응은 상황을 더 악화시킬 수 있어. 사이버 폭력은 처벌받을 수 있는 범죄야. 더 현명한 방법이 있어."
            },
            {
                "text": "📸 증거를 캡처하고 학교 상담 선생님을 찾아간다.",
                "effects": {"mental": +15, "physical": 0, "risk": -15, "happiness": +10},
                "feedback": "현명한 선택이야! 증거를 남기고 어른의 도움을 받는 게 가장 효과적인 대응이야. 사이버 폭력은 명백한 범죄야."
            },
            {
                "text": "😢 아무에게도 말하지 않고 혼자 참는다. 학교 가기 싫다.",
                "effects": {"mental": -30, "physical": -15, "risk": +25, "happiness": -35},
                "feedback": "혼자 감당하려고 하지 마. 도움을 요청하는 건 약한 게 아니야. 학교폭력 신고는 117, 청소년상담전화는 1388이야."
            },
            {
                "text": "💪 부모님께 상황을 설명하고 함께 대응 방법을 찾는다.",
                "effects": {"mental": +20, "physical": +5, "risk": -20, "happiness": +15},
                "feedback": "완벽한 선택이야! 가족의 지지는 가장 큰 힘이 돼. 함께 법적 대응도 고려할 수 있어. 넌 혼자가 아니야."
            }
        ]
    },
    {
        "id": "loan_scam",
        "text": "저녁 8시, 모르는 번호로 문자가 왔다. '학생도 가능! 신분증만 있으면 즉시 50만원 대출! 부모님 동의 불필요! 이자 없음!' 요즘 용돈이 부족한데, 갖고 싶은 게 많다.",
        "choices": [
            {
                "text": "💰 '한 번만 빌려볼까? 나중에 갚으면 되잖아.'",
                "effects": {"mental": -20, "physical": 0, "risk": +35, "happiness": -18},
                "feedback": "절대 안 돼! 이건 불법 대출(일명 '대포폰')로 이어질 수 있어. 청소년 대상 대출 광고는 대부분 사기이거나 범죄 조직과 연결되어 있어."
            },
            {
                "text": "🚫 무시하고 번호를 차단한다.",
                "effects": {"mental": +8, "physical": 0, "risk": 0, "happiness": +5},
                "feedback": "잘했어! 의심스러운 문자는 무시하는 게 최선이야. 합법적인 금융 기관은 이런 식으로 연락하지 않아."
            },
            {
                "text": "📱 부모님께 문자를 보여드리고 상담한다.",
                "effects": {"mental": +12, "physical": 0, "risk": -5, "happiness": +10},
                "feedback": "현명한 선택이야! 금융 사기를 예방하는 가장 좋은 방법은 가족과 상의하는 거야. 필요한 게 있으면 솔직하게 이야기하는 게 좋아."
            },
            {
                "text": "📞 경찰청 사이버안전국(182)에 신고한다.",
                "effects": {"mental": +10, "physical": 0, "risk": -10, "happiness": +12},
                "feedback": "책임감 있는 행동이야! 신고는 다른 청소년들을 보호하는 일이기도 해. 넌 범죄를 막는 데 기여한 거야."
            }
        ]
    },
    {
        "id": "depression_sign",
        "text": "최근 2주 동안 아무것도 하기 싫고, 좋아하던 취미도 재미가 없다. 밤에는 잠이 안 오고, 학교에서도 집중이 안 된다. '내가 사라져도 아무도 신경 안 쓸 거야'라는 생각이 자꾸 든다.",
        "choices": [
            {
                "text": "💊 '그냥 시간이 지나면 나아지겠지. 혼자 견뎌봐야지.'",
                "effects": {"mental": -35, "physical": -20, "risk": +40, "happiness": -40},
                "feedback": "이건 우울증의 신호일 수 있어. 청소년 중 약 25%가 우울을 경험해. 혼자 견디지 말고 꼭 도움을 받아야 해. 치료받으면 좋아질 수 있어."
            },
            {
                "text": "📞 청소년상담전화 1388에 전화해본다.",
                "effects": {"mental": +25, "physical": +10, "risk": -20, "happiness": +20},
                "feedback": "정말 용기 있는 선택이야! 도움을 청하는 건 강한 사람만이 할 수 있는 행동이야. 1388은 24시간 운영되고, 비밀이 보장돼."
            },
            {
                "text": "💬 부모님이나 신뢰하는 어른에게 이야기한다.",
                "effects": {"mental": +30, "physical": +15, "risk": -25, "happiness": +25},
                "feedback": "완벽해! 가족과의 솔직한 대화는 치유의 시작이야. 부모님도 네가 힘들어하는 걸 알고 싶어 하실 거야."
            },
            {
                "text": "🏥 학교 상담실을 찾아가거나 정신건강의학과 예약을 요청한다.",
                "effects": {"mental": +35, "physical": +15, "risk": -30, "happiness": +30},
                "feedback": "최고의 선택이야! 전문가의 도움은 가장 효과적인 치료법이야. 정신 건강도 신체 건강만큼 중요해. 치료받는 건 당연한 권리야."
            }
        ]
    },
    {
        "id": "friend_crisis",
        "text": "가장 친한 친구가 최근 이상하다. SNS에 '사라지고 싶다', '아무도 날 이해 못 해'라는 글을 올렸다. 전화해봤는데 '괜찮아, 그냥 힘든 날이야'라고만 한다. 하지만 목소리가 심상치 않다.",
        "choices": [
            {
                "text": "🤷 '괜찮대니까 그냥 두자. 내가 오버하는 건가?'",
                "effects": {"mental": -10, "physical": 0, "risk": +15, "happiness": -15},
                "feedback": "친구의 위기 신호를 놓치면 안 돼. '괜찮다'는 말 뒤에 도움 요청이 숨어있을 수 있어. 한 번 더 관심을 보여줘."
            },
            {
                "text": "💬 '나 지금 갈게. 혼자 있지 마'라고 말하고 직접 찾아간다.",
                "effects": {"mental": +20, "physical": +5, "risk": -15, "happiness": +20},
                "feedback": "훌륭한 친구야! 직접 만나서 이야기하는 게 가장 좋아. 네 존재 자체가 큰 위로가 될 거야. 함께 있어주는 것만으로도 큰 도움이 돼."
            },
            {
                "text": "📞 친구 부모님이나 담임 선생님께 조심스럽게 알린다.",
                "effects": {"mental": +15, "physical": 0, "risk": -20, "happiness": +15},
                "feedback": "책임감 있는 선택이야! 친구의 안전이 최우선이야. 이건 배신이 아니라 진짜 우정이야. 나중에 친구도 고마워할 거야."
            },
            {
                "text": "🆘 1388에 상담해서 어떻게 도와줘야 할지 조언을 구한다.",
                "effects": {"mental": +18, "physical": 0, "risk": -18, "happiness": +18},
                "feedback": "현명해! 전문가의 조언을 받는 건 정말 좋은 방법이야. 청소년상담전화는 이런 상황에 대한 가이드를 제공해줄 거야."
            }
        ]
    },
    {
        "id": "gaming_addiction",
        "text": "게임이 너무 재밌다. 매일 밤 새벽 2-3시까지 게임을 한다. 성적은 떨어지고 친구들도 잘 안 만나게 됐다. 부모님이 걱정하시지만 '이거 하나라도 있어야 스트레스가 풀려'라고 생각한다.",
        "choices": [
            {
                "text": "🎮 '내 인생인데 내가 알아서 할게. 계속 게임할 거야.'",
                "effects": {"mental": -15, "physical": -18, "risk": +20, "happiness": -12},
                "feedback": "게임은 즐거움을 주지만, 과도하면 일상생활에 지장을 줘. 게임 중독은 청소년기 주요 문제 중 하나야. 균형이 필요해."
            },
            {
                "text": "⏰ 하루 1-2시간으로 제한하고, 다른 활동도 시도해본다.",
                "effects": {"mental": +15, "physical": +12, "risk": -5, "happiness": +12},
                "feedback": "훌륭해! 스스로 조절하는 능력은 정말 중요해. 다양한 활동을 하면 더 풍부한 삶을 살 수 있어."
            },
            {
                "text": "💬 '게임이 문제인 것 같아. 도와줄 수 있어?' 부모님께 먼저 이야기한다.",
                "effects": {"mental": +20, "physical": +15, "risk": -10, "happiness": +18},
                "feedback": "정말 성숙한 선택이야! 문제를 인식하고 도움을 청하는 건 쉽지 않은 일이야. 가족의 지원을 받으면 더 쉽게 극복할 수 있어."
            }
        ]
    },
    {
        "id": "final_choice",
        "text": "학년이 끝나간다. 지난 1년을 돌아보니 여러 일이 있었다. 힘든 순간도 있었고 즐거운 순간도 있었다. 이제 방학이다. 앞으로 어떻게 지낼지 생각해본다.",
        "choices": [
            {
                "text": "😊 '힘들 때는 도움을 청하고, 좋은 선택을 계속하자!'",
                "effects": {"mental": +20, "physical": +15, "risk": -10, "happiness": +25},
                "feedback": "완벽한 마음가짐이야! 네가 배운 걸 실천하고 있어. 생명은 소중하고, 너는 가치 있는 사람이야."
            },
            {
                "text": "🤔 '그때그때 달라. 뭐가 좋은지 잘 모르겠어.'",
                "effects": {"mental": +5, "physical": +5, "risk": 0, "happiness": +5},
                "feedback": "괜찮아, 모든 걸 다 알 필요는 없어. 중요한 건 힘들 때 도움을 청할 수 있다는 걸 아는 거야."
            },
            {
                "text": "💪 '나를 더 잘 이해하고, 건강하게 살고 싶어.'",
                "effects": {"mental": +25, "physical": +20, "risk": -15, "happiness": +30},
                "feedback": "멋진 다짐이야! 자기 이해와 건강한 삶은 평생의 과제야. 넌 이미 올바른 길을 걷고 있어."
            }
        ]
    }
]

# -------------------- 데이터 로드 함수 (기존 함수 교체) --------------------
@st.cache_data
def load_statistics():
    """CSV 파일들을 로드하고 통계 데이터를 반환"""
    stats = {}
    
    # 우울증 데이터
    try:
        df_dep = pd.read_csv("청소년_우울증.csv", encoding='utf-8-sig')
        if "우울 경험률" in df_dep.columns or "우울경험률" in df_dep.columns:
            col_name = "우울 경험률" if "우울 경험률" in df_dep.columns else "우울경험률"
            stats['depression'] = df_dep[col_name].mean()
            
            # 성별 데이터가 있으면 성별별로 계산
            if "성별" in df_dep.columns:
                stats['depression_male'] = df_dep[df_dep['성별'].str.contains('남', na=False)][col_name].mean()
                stats['depression_female'] = df_dep[df_dep['성별'].str.contains('여', na=False)][col_name].mean()
            else:
                stats['depression_male'] = stats['depression']
                stats['depression_female'] = stats['depression']
        else:
            stats['depression'] = 25.2
            stats['depression_male'] = 20.5
            stats['depression_female'] = 30.1
    except:
        stats['depression'] = 25.2
        stats['depression_male'] = 20.5
        stats['depression_female'] = 30.1
    
    # 자살시도율 데이터
    try:
        df_su = pd.read_csv("청소년_자살시도율.csv", encoding='utf-8-sig')
        if "자살시도율" in df_su.columns:
            stats['suicide'] = df_su["자살시도율"].mean()
            
            if "성별" in df_su.columns:
                stats['suicide_male'] = df_su[df_su['성별'].str.contains('남', na=False)]["자살시도율"].mean()
                stats['suicide_female'] = df_su[df_su['성별'].str.contains('여', na=False)]["자살시도율"].mean()
            else:
                stats['suicide_male'] = stats['suicide']
                stats['suicide_female'] = stats['suicide']
        else:
            stats['suicide'] = 2.7
            stats['suicide_male'] = 2.3
            stats['suicide_female'] = 3.1
    except:
        stats['suicide'] = 2.7
        stats['suicide_male'] = 2.3
        stats['suicide_female'] = 3.1
    
    # 흡연율 데이터
    try:
        df_smoke = pd.read_csv("청소년_흡연율.csv", encoding='utf-8-sig')
        if "흡연율" in df_smoke.columns:
            stats['smoking'] = df_smoke["흡연율"].mean()
            
            if "성별" in df_smoke.columns:
                stats['smoking_male'] = df_smoke[df_smoke['성별'].str.contains('남', na=False)]["흡연율"].mean()
                stats['smoking_female'] = df_smoke[df_smoke['성별'].str.contains('여', na=False)]["흡연율"].mean()
            else:
                stats['smoking_male'] = stats['smoking']
                stats['smoking_female'] = stats['smoking']
        else:
            stats['smoking'] = 5.9
            stats['smoking_male'] = 7.8
            stats['smoking_female'] = 3.8
    except:
        stats['smoking'] = 5.9
        stats['smoking_male'] = 7.8
        stats['smoking_female'] = 3.8
    
    # 사회문제 노출 데이터
    try:
        df_soc = pd.read_csv("사회문제_위험_노출_정도_20251102160905.csv", encoding='utf-8-sig')
        if "위험노출정도" in df_soc.columns:
            stats['risk_exposure'] = df_soc["위험노출정도"].mean()
        else:
            stats['risk_exposure'] = 15.8
    except:
        stats['risk_exposure'] = 15.8
    
    return stats

# -------------------- 게임 결과 분석 --------------------
def analyze_result(stats, real_stats):
    """최종 결과를 분석하여 엔딩 결정"""
    mental = stats['mental']
    risk = stats['risk']
    happiness = stats['happiness']
    
    if mental >= 60 and happiness >= 60 and risk <= 20:
        return "happy", "🌟 행복한 청소년", "#28A745"
    elif mental <= 30 or happiness <= 30:
        if risk >= 40:
            return "crisis", "⚠️ 위기 상황", "#DC3545"
        else:
            return "depressed", "😔 우울 위험", "#FD7E14"
    elif risk >= 50:
        return "high_risk", "🚨 고위험 행동", "#C82333"
    else:
        return "normal", "😐 평범한 일상", "#007BFF"

def get_ending_message(ending_type, stats, real_stats):
    """엔딩 타입에 따른 메시지 반환"""
    messages = {
        "happy": f"""
        <div style='background-color:#D4EDDA; padding:20px; border-radius:10px; border-left:5px solid #28A745; color:#155724;'>
        <h3>🎉 축하해요!</h3>
        <p>당신은 건강한 선택들을 통해 행복한 청소년기를 보내고 있어요.</p>
        <p>당신의 정신 건강 지수는 <b>{stats['mental']}점</b>으로, 평균 이상이에요.</p>
        <p>이런 긍정적인 태도를 계속 유지해주세요! ✨</p>
        </div>
        """,
        "depressed": f"""
        <div style='background-color:#FFF3CD; padding:20px; border-radius:10px; border-left:5px solid #FD7E14; color:#856404;'>
        <h3>💙 괜찮아요, 도움을 받을 수 있어요</h3>
        <p>당신의 정신 건강 지수는 <b>{stats['mental']}점</b>입니다.</p>
        <p>실제로 청소년의 약 <b>{real_stats['depression']:.1f}%</b>가 우울을 경험하고 있어요.</p>
        <br>
        <p><b>🆘 도움받을 수 있는 곳:</b></p>
        <ul>
        <li>📞 청소년상담전화: <b>1388</b> (24시간, 무료)</li>
        <li>📞 자살예방상담전화: <b>1393</b> (24시간, 무료)</li>
        <li>🏫 학교 상담실</li>
        <li>🏥 정신건강복지센터</li>
        </ul>
        <p><b>혼자가 아니에요. 언제든 도움을 요청하세요.</b></p>
        </div>
        """,
        "crisis": f"""
        <div style='background-color:#F8D7DA; padding:20px; border-radius:10px; border-left:5px solid #DC3545; color:#721C24;'>
        <h3>🚨 지금 당장 도움이 필요해요!</h3>
        <p>당신의 상태는 매우 위험한 수준입니다.</p>
        <p>청소년 자살시도율은 <b>{real_stats['suicide']:.1f}%</b>이지만, 대부분은 도움을 받아 회복했어요.</p>
        <br>
        <p><b>🆘 즉시 연락하세요:</b></p>
        <ul>
        <li>🚨 <b>응급상황: 119</b></li>
        <li>📞 <b>자살예방상담전화: 1393</b> (24시간)</li>
        <li>📱 <b>청소년상담전화: 1388</b> (24시간)</li>
        <li>💬 <b>카카오톡 플러스친구: "자살예방상담"</b></li>
        </ul>
        <p><b style='font-size:18px;'>당신의 생명은 소중합니다. 지금 전화하세요.</b></p>
        </div>
        """,
        "high_risk": f"""
        <div style='background-color:#F8D7DA; padding:20px; border-radius:10px; border-left:5px solid #C82333; color:#721C24;'>
        <h3>⚠️ 위험한 행동을 멈춰야 해요</h3>
        <p>당신의 위험 행동 지수는 <b>{stats['risk']}점</b>입니다.</p>
        <p>청소년의 <b>{real_stats['risk_exposure']:.1f}%</b>가 위험한 환경에 노출되어 있어요.</p>
        <br>
        <p>흡연, 음주, 불법 대출 등은 당장은 문제가 없어 보여도<br>
        장기적으로 큰 피해를 줄 수 있어요.</p>
        <br>
        <p><b>📞 상담받기:</b></p>
        <ul>
        <li>청소년상담전화: <b>1388</b></li>
        <li>학교폭력신고: <b>117</b></li>
        <li>사이버범죄 신고: <b>182</b></li>
        </ul>
        </div>
        """,
        "normal": f"""
        <div style='background-color:#D1ECF1; padding:20px; border-radius:10px; border-left:5px solid #007BFF; color:#0C5460;'>
        <h3>😊 나쁘지 않아요!</h3>
        <p>당신은 평범한 청소년기를 보내고 있어요.</p>
        <p>때로는 힘들 수도 있지만, 좋은 선택을 계속하면<br>
        더 행복한 미래를 만들 수 있어요.</p>
        <br>
        <p>📊 <b>당신의 현재 상태:</b></p>
        <ul>
        <li>정신 건강: <b>{stats['mental']}점</b></li>
        <li>행복 지수: <b>{stats['happiness']}점</b></li>
        </ul>
        </div>
        """
    }
    return messages.get(ending_type, messages["normal"])

# -------------------- 메인 화면 --------------------
st.markdown("<h1 style='text-align:center; color:#007BFF;'>💙 청소년 생명존중 시뮬레이터</h1>", unsafe_allow_html=True)

# 게임 시작 전 화면
if not st.session_state.game_started:
    st.markdown("---")
    st.markdown("""
    <div style='background-color:#E7F3FF; padding:20px; border-radius:10px; border-left:5px solid #007BFF; color:#004085;'>
    <h3>🎮 게임 소개</h3>
    <p>이 시뮬레이터는 청소년기에 마주할 수 있는 다양한 상황과 선택을 체험하는 게임입니다.</p>
    <ul>
    <li>여러 가지 상황에서 <b>선택</b>을 하게 됩니다</li>
    <li>선택에 따라 <b>정신건강, 육체건강, 위험도, 행복도</b>가 변합니다</li>
    <li>마지막에 <b>실제 통계 데이터</b>와 비교한 결과를 보여드립니다</li>
    </ul>
    <p>💡 <b>목적:</b> 생명의 소중함을 깨닫고, 위기 상황에서 도움을 청하는 것의 중요성을 배웁니다.</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("### 👤 캐릭터 설정")
    st.write("당신의 성별을 선택해주세요:")
    
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
    <div style='background-color:#FFF9E6; padding:20px; border-radius:10px; border-left:5px solid #FFC107; color:#856404;'>
    <h4>⚠️ 중요한 안내</h4>
    <p>게임 중 힘든 감정이 들거나 도움이 필요하면:</p>
    <ul>
    <li>📞 청소년상담전화 <b style='font-size:18px; color:#DC3545;'>1388</b> (24시간)</li>
    <li>📞 자살예방상담전화 <b style='font-size:18px; color:#DC3545;'>1393</b> (24시간)</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)

# 게임 진행 화면
elif st.session_state.stage < len(SCENARIOS):
    # 상태 표시 - 가독성 개선
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        mental_color = "#28A745" if st.session_state.stats['mental'] >= 50 else "#DC3545"
        st.markdown(f"""
        <div style='text-align:center; padding:15px; background-color:white; border:2px solid {mental_color}; border-radius:10px;'>
        <div style='font-size:24px;'>🧠</div>
        <div style='font-weight:bold; color:{mental_color}; font-size:20px;'>{st.session_state.stats['mental']}</div>
        <div style='font-size:12px; color:#666;'>정신건강</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        physical_color = "#28A745" if st.session_state.stats['physical'] >= 50 else "#DC3545"
        st.markdown(f"""
        <div style='text-align:center; padding:15px; background-color:white; border:2px solid {physical_color}; border-radius:10px;'>
        <div style='font-size:24px;'>💪</div>
        <div style='font-weight:bold; color:{physical_color}; font-size:20px;'>{st.session_state.stats['physical']}</div>
        <div style='font-size:12px; color:#666;'>신체건강</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        risk_color = "#28A745" if st.session_state.stats['risk'] <= 20 else "#DC3545"
        st.markdown(f"""
        <div style='text-align:center; padding:15px; background-color:white; border:2px solid {risk_color}; border-radius:10px;'>
        <div style='font-size:24px;'>⚠️</div>
        <div style='font-weight:bold; color:{risk_color}; font-size:20px;'>{st.session_state.stats['risk']}</div>
        <div style='font-size:12px; color:#666;'>위험도</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        happiness_color = "#28A745" if st.session_state.stats['happiness'] >= 50 else "#DC3545"
        st.markdown(f"""
        <div style='text-align:center; padding:15px; background-color:white; border:2px solid {happiness_color}; border-radius:10px;'>
        <div style='font-size:24px;'>😊</div>
        <div style='font-weight:bold; color:{happiness_color}; font-size:20px;'>{st.session_state.stats['happiness']}</div>
        <div style='font-size:12px; color:#666;'>행복도</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # 진행도 표시
    progress = (st.session_state.stage + 1) / len(SCENARIOS)
    st.progress(progress)
    st.markdown(f"<p style='text-align:center; color:#666; font-size:14px;'>상황 {st.session_state.stage + 1} / {len(SCENARIOS)}</p>", unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # 현재 시나리오
    scenario = SCENARIOS[st.session_state.stage]
    
    # 대화 형식으로 표시 - 가독성 개선
    gender_emoji = "🙋‍♂️" if st.session_state.gender == "male" else "🙋‍♀️"
    st.markdown(
        f"""
        <div style="background-color:#F8F9FA; padding:20px; border-radius:15px; margin-bottom:20px; border:2px solid #007BFF; color:#212529;">
        <div style="margin-bottom:10px;">
        {gender_emoji} <b style="font-size:18px; color:#007BFF;">{st.session_state.character_name}</b>
        </div>
        <div style="font-size:16px; line-height:1.6;">
        {scenario['text']}
        </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<h4 style='color:#007BFF;'>💭 어떻게 할까요?</h4>", unsafe_allow_html=True)
    
    # 선택지 버튼 - 가독성 개선
    for idx, choice in enumerate(scenario["choices"]):
        button_color = "#007BFF" if idx == 0 else "#6C757D"
        if st.button(
            choice["text"], 
            key=f"choice_{idx}", 
            use_container_width=True,
            type="primary" if idx == 0 else "secondary"
        ):
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
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(
            f"""
            <div style='background-color:#D1ECF1; padding:15px; border-radius:10px; border-left:4px solid #17A2B8; color:#0C5460;'>
            <b>💬 피드백:</b><br>{st.session_state.last_feedback}
            </div>
            """, unsafe_allow_html=True)

# 게임 종료 화면
else:
    st.balloons()
    st.markdown("---")
    st.markdown("<h2 style='text-align:center; color:#007BFF;'>🎉 시뮬레이션 완료!</h2>", unsafe_allow_html=True)
    
    # 통계 로드
    real_stats = load_statistics()
    
    # 결과 분석
    ending_type, ending_title, ending_color = analyze_result(st.session_state.stats, real_stats)
    
    # 엔딩 타이틀
    st.markdown(
        f"""
        <div style="background-color:{ending_color}; padding:25px; border-radius:15px; text-align:center; color:white; margin:20px 0; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
        <h2 style='margin:0; color:white;'>{ending_title}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    # 최종 스탯
    st.markdown("### 📊 당신의 최종 상태")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("🧠 정신건강", f"{st.session_state.stats['mental']}/100", 
                 delta=st.session_state.stats['mental']-50)
    with col2:
        st.metric("💪 신체건강", f"{st.session_state.stats['physical']}/100",
                 delta=st.session_state.stats['physical']-50)
    with col3:
        st.metric("⚠️ 위험도", f"{st.session_state.stats['risk']}/100",
                 delta=st.session_state.stats['risk'], delta_color="inverse")
    with col4:
        st.metric("😊 행복도", f"{st.session_state.stats['happiness']}/100",
                 delta=st.session_state.stats['happiness']-50)
    
    st.markdown("---")
    
    # 엔딩 메시지
    st.markdown(get_ending_message(ending_type, st.session_state.stats, real_stats), unsafe_allow_html=True)
    
    st.markdown("---")
    render_center_map()
# -------------------- 성별별 통계 표시 --------------------
def show_gender_statistics(stats, user_gender):
    """사용자 성별에 맞는 통계 표시"""
    st.markdown("### 📊 나와 같은 성별 청소년 통계")
    
    gender_text = "남학생" if user_gender == "male" else "여학생"
    
    # 성별별 데이터 가져오기 (없으면 전체 평균 사용)
    if user_gender == "male":
        depression_rate = stats.get('depression_male', stats.get('depression', 25.2))
        suicide_rate = stats.get('suicide_male', stats.get('suicide', 2.7))
        smoking_rate = stats.get('smoking_male', stats.get('smoking', 5.9))
    else:
        depression_rate = stats.get('depression_female', stats.get('depression', 25.2))
        suicide_rate = stats.get('suicide_female', stats.get('suicide', 2.7))
        smoking_rate = stats.get('smoking_female', stats.get('smoking', 5.9))
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"""
        <div style='background-color:white; padding:20px; border-radius:10px; border:2px solid #DC3545; color:#212529;'>
        <h4 style='color:#DC3545; margin-top:0;'>😔 {gender_text} 우울 경험률</h4>
        <p style='font-size:32px; font-weight:bold; color:#DC3545; margin:10px 0;'>{depression_rate:.1f}%</p>
        <p>같은 성별 청소년 중 이만큼이<br>우울감을 경험하고 있어요.</p>
        </div>
        """, unsafe_allow_html=True)
        
    with col2:
        st.markdown(f"""
        <div style='background-color:white; padding:20px; border-radius:10px; border:2px solid #C82333; color:#212529;'>
        <h4 style='color:#C82333; margin-top:0;'>⚠️ {gender_text} 자살시도율</h4>
        <p style='font-size:32px; font-weight:bold; color:#C82333; margin:10px 0;'>{suicide_rate:.1f}%</p>
        <p>하지만 대부분은<br>도움으로 회복했어요.</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    st.markdown(f"""
    <div style='background-color:white; padding:20px; border-radius:10px; border:2px solid #FD7E14; color:#212529;'>
    <h4 style='color:#FD7E14; margin-top:0;'>🚬 {gender_text} 흡연율</h4>
    <p style='font-size:32px; font-weight:bold; color:#FD7E14; margin:10px 0;'>{smoking_rate:.1f}%</p>
    <p>흡연은 중독성이 강하고 건강을 크게 해쳐요.</p>
    </div>
    """, unsafe_allow_html=True)


import streamlit as st
import pandas as pd

# -------------------------------
# 데이터 불러오기
# -------------------------------
df = pd.read_csv("https://raw.githubusercontent.com/jungms080422-design/-/main/adolscenve.csv", encoding="cp949")
df.columns = df.columns.str.strip()

# -------------------------------
# UI 구성
# -------------------------------
st.title("🌱 여성가족부 청소년상담복지센터 현황")

st.write("지역과 시군구를 선택하면 해당 지역의 센터 주소와 전화번호를 확인할 수 있습니다.")

# 지역(광역시도) 선택
region_list = sorted(df["지역"].dropna().unique())
selected_region = st.selectbox("📍 광역시도 선택", region_list)

# 시군구 선택
filtered_region_df = df[df["지역"] == selected_region]
sigungu_list = sorted(filtered_region_df["시군구"].dropna().unique())
selected_sigungu = st.selectbox("🏙️ 시군구 선택", sigungu_list)

# 선택된 지역 필터링
filtered_df = filtered_region_df[filtered_region_df["시군구"] == selected_sigungu]

# -------------------------------
# 결과 표시
# -------------------------------
st.subheader(f"📋 {selected_region} {selected_sigungu} 청소년상담복지센터 목록")

if not filtered_df.empty:
    # 보여줄 컬럼만 선택
    display_cols = [col for col in ["시설명", "주소", "전화번호"] if col in filtered_df.columns]
    st.dataframe(filtered_df[display_cols].reset_index(drop=True))
else:
    st.warning("해당 지역의 센터 정보가 없습니다.")

# -------------------------------
# 추가 정보
# -------------------------------
with st.expander("ℹ️ 데이터 출처"):
    st.markdown("""
    - 본 데이터는 **여성가족부 청소년상담복지센터 현황** 자료를 기반으로 합니다.  
    - 출처: 여성가족부 청소년상담복지개발원  
    """)


# 인코딩 자동 탐지 + fallback
try:
    df = pd.read_csv(
        "https://raw.githubusercontent.com/jungms080422-design/-/main/adolscenve.csv",
        encoding="utf-8-sig"
    )
except UnicodeDecodeError:
    df = pd.read_csv(
        "https://raw.githubusercontent.com/jungms080422-design/-/main/adolscenve.csv",
        encoding="cp949",
        errors="ignore"
    )

st.write(df.head())
