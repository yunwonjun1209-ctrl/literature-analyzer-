import streamlit as st
import google.generativeai as genai
import json

# =============================================================================
# [0] 페이지 기본 설정 (가장 먼저 실행되어야 함)
# =============================================================================
st.set_page_config(page_title="문학 강의 논리 분석기", page_icon="📝", layout="wide")

# =============================================================================
# [SECRET] 비밀번호 보호 로직
# =============================================================================
# 세션 상태 초기화
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# 로그인 화면 (인증되지 않았으면 여기서 멈춤)
if not st.session_state.authenticated:
    st.markdown("<h1 style='text-align: center; color: white;'>🔒 접근 제한</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #ccc;'>관계자 외 접근이 제한된 페이지입니다.</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        password_input = st.text_input("비밀번호를 입력하세요", type="password")
        
        if password_input:
            # st.secrets에서 'ACCESS_PASSWORD'를 가져와 비교
            if password_input == st.secrets["ACCESS_PASSWORD"]:
                st.session_state.authenticated = True
                st.rerun()  # 화면 새로고침하여 메인 화면 진입
            else:
                st.error("경고! 비밀번호가 일치하지 않습니다. 귀하의 접근 기록이 서버에 남습니다.")
    
    st.stop() # 인증 안 되면 아래 코드는 실행하지 않음

# =============================================================================
# [1] 시스템 프롬프트 (분석 논리 및 출력 포맷 지정)
# =============================================================================
SYSTEM_INSTRUCTION = """
You are a Literature Analysis AI Expert specializing in 'Park Seok-jun's Lecture Style'.
Analyze the provided 'Original Text' and 'Lecture Script' based on the following protocol.

[Analysis Protocol v3.0 - Text Format Focus]
1. Goal: Analyze the logic connecting [Text Fact] to [Teacher's Interpretation].
2. Output Format: STRICTLY JSON format only.
3. Language: Korean (한국어) ONLY.

[JSON Structure Requirement]
The JSON must support the following output format:
<Sequence N> Summary
Key : Core Message (Theme Keyword)
-Fact = Interpretation

{
  "metadata": {
    "title": "Work Title",
    "teacher_logic": "Main Logic"
  },
  "structure_break_point": {
    "after_sequence": 3,
    "description": "Situation Description",
    "change_state": {
      "before": "State Before",
      "after": "State After"
    }
  },
  "sequences": [
    {
      "seq_id": 1,
      "summary": "Sequence Summary",
      "core_message": "Core Message",
      "theme_keyword": "Theme",
      "details": [
        {"fact": "Text Fact", "interpretation": "Teacher's Interpretation"}
      ]
    }
  ]
}
"""

# =============================================================================
# [2] API 통신 함수
# =============================================================================
def analyze_with_gemini(api_key, original, script):
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(
            model_name='gemini-2.5-flash', # 긴 텍스트 분석에 최적화
            system_instruction=SYSTEM_INSTRUCTION
        )

        user_prompt = f"""
        ---
        [Original Text]
        {original}
        
        ---
        [Lecture Script]
        {script}
        
        ---
        Analyze the above content.
        """

        with st.spinner("🧠 AI가 분석 중입니다..."):
            response = model.generate_content(user_prompt)
            text_response = response.text.replace("```json", "").replace("```", "").strip()
            return json.loads(text_response)

    except Exception as e:
        return {"error": str(e)}

# =============================================================================
# [3] Streamlit UI 설정 (Pure Dark Mode)
# =============================================================================
# CSS 스타일링 (검은 배경, 흰 글씨, 박스 제거)
st.markdown("""
    <style>
    /* 1. 전체 앱 배경 및 폰트 색상 강제 지정 */
    .stApp {
        background-color: #121212 !important;
        color: #FFFFFF !important;
    }
    
    /* 2. 입력창 스타일 (어두운 회색 배경, 흰색 글씨) */
    .stTextArea textarea {
        background-color: #1E1E1E !important;
        color: #E0E0E0 !important;
        border: 1px solid #333 !important;
        font-family: 'Apple SD Gothic Neo', sans-serif;
    }

    /* 3. 헤더 및 일반 텍스트 색상 */
    h1, h2, h3, h4, h5, h6, p, label, li, span, div {
        color: #FFFFFF !important;
    }
    
    /* 4. 사이드바 스타일 */
    [data-testid="stSidebar"] {
        background-color: #1E1E1E !important;
        border-right: 1px solid #333;
    }
    
    /* 5. 분석 결과 텍스트 스타일링 (요청하신 포맷용) */
    .seq-header {
        font-size: 1.15em;
        font-weight: bold;
        color: #FF8A80 !important; /* 시퀀스 번호 강조색 (살구색) */
        margin-top: 25px;
        margin-bottom: 5px;
    }
    
    .seq-summary {
        font-size: 1.1em;
        margin-bottom: 10px;
        line-height: 1.5;
    }

    .core-msg {
        font-weight: bold;
        color: #81D4FA !important; /* 핵심 메시지 강조색 (하늘색) */
        margin-bottom: 10px;
    }

    .detail-line {
        margin-left: 0px;
        margin-bottom: 5px;
        line-height: 1.6;
        color: #E0E0E0 !important;
    }
    
    .break-point {
        margin: 30px 0;
        padding: 15px;
        border-top: 1px dashed #555;
        border-bottom: 1px dashed #555;
        color: #FFD54F !important; /* 중략 부분 강조색 (노란색) */
    }
    </style>
    """, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 사이드바
# -----------------------------------------------------------------------------
with st.sidebar:
    st.header("⚙️ 설정")
    api_key = st.text_input("Google Gemini API Key", type="password")
    st.info("입력된 원문과 강의를 '텍스트 포맷'으로 분석합니다.")

# -----------------------------------------------------------------------------
# 메인 화면
# -----------------------------------------------------------------------------
st.title("📝 문학 강의 논리 분석기")
st.markdown("요청하신 **텍스트 서식(<시퀀스> ... -팩트 = 해석)** 그대로 출력합니다.")

col1, col2 = st.columns(2)
with col1:
    original_text = st.text_area("1. 작품 원문", height=400)
with col2:
    lecture_script = st.text_area("2. 강의 스크립트", height=400)

analyze_btn = st.button("🚀 분석 시작", type="primary", use_container_width=True)

# -----------------------------------------------------------------------------
# 분석 결과 출력 (요청하신 포맷 준수)
# -----------------------------------------------------------------------------
if analyze_btn:
    if not api_key:
        st.error("API Key를 입력해주세요.")
    elif not original_text or not lecture_script:
        st.warning("내용을 모두 입력해주세요.")
    else:
        result = analyze_with_gemini(api_key, original_text, lecture_script)
        
        if "error" in result:
            st.error(f"오류: {result['error']}")
        else:
            st.divider()
            
            # 메타데이터
            st.subheader(f"{result.get('metadata', {}).get('title', '분석 결과')}")
            
            sequences = result.get('sequences', [])
            bp = result.get('structure_break_point', {})

            for seq in sequences:
                # 1. 시퀀스 헤더 & 요약
                st.markdown(f"""
                <div class="seq-header">&lt;시퀀스{seq['seq_id']}&gt;</div>
                <div class="seq-summary">{seq['summary']}</div>
                """, unsafe_allow_html=True)
                
                # 2. 핵심 메시지
                st.markdown(f"""
                <div class="core-msg">
                핵심 : {seq['core_message']} ({seq['theme_keyword']})
                </div>
                """, unsafe_allow_html=True)
                
                # 3. 디테일 (Fact = Interpretation)
                for detail in seq.get('details', []):
                    st.markdown(f"""
                    <div class="detail-line">
                    -{detail['fact']} = {detail['interpretation']}
                    </div>
                    """, unsafe_allow_html=True)

                # 4. 중략/전환점 (Break Point)
                if bp and seq['seq_id'] == bp.get('after_sequence'):
                    st.markdown(f"""
                    <div class="break-point">
                        {bp.get('description')}<br>
                        전 = {bp['change_state']['before']}<br>
                        후 = {bp['change_state']['after']}
                    </div>
                    """, unsafe_allow_html=True)
