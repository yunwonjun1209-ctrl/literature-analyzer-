import streamlit as st
import google.generativeai as genai
import json

# =============================================================================
# [0] 페이지 기본 설정 (가장 먼저 실행)
# =============================================================================
st.set_page_config(page_title="문학 강의 논리 분석기", page_icon="📝", layout="wide")

# =============================================================================
# [SECRET] 비밀번호 보호 로직
# =============================================================================
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #ffffff; }
    h1, p { color: #ffffff !important; }
    </style>
    <h1 style='text-align: center;'>🔒 접근 제한</h1>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        password_input = st.text_input("비밀번호를 입력하세요", type="password")
        if password_input:
            if password_input == st.secrets["ACCESS_PASSWORD"]:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("비밀번호가 일치하지 않습니다.")
    st.stop()

# =============================================================================
# [1] 시스템 프롬프트 (엄격한 서식 지정)
# =============================================================================
SYSTEM_INSTRUCTION = """
You are a Literature Analysis AI Expert specializing in 'Park Seok-jun's Lecture Style'.

[CRITICAL INSTRUCTION]
Your goal is to extract the logic from the lecture script and map it to the original text.
You must output a JSON object that perfectly fits the user's specific text format.

[Target Output Format Example]
<시퀀스1> Sequence Summary
핵심 : Core Message (Theme Keyword)
-Text Fact = Teacher's Interpretation
-Text Fact = Teacher's Interpretation

[JSON Structure Requirement]
The JSON must separate 'fact' and 'interpretation' so the code can render them with an '=' sign.

{
  "metadata": { "title": "Work Title" },
  "structure_break_point": {
    "after_sequence": 3,
    "description": "Situation Description",
    "change_state": { "before": "State Before", "after": "State After" }
  },
  "sequences": [
    {
      "seq_id": 1,
      "summary": "Full summary of the sequence",
      "core_message": "Main message",
      "theme_keyword": "Theme",
      "details": [
        {"fact": "Quote or fact from text", "interpretation": "Logic/Meaning from lecture"}
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
            model_name='gemini-1.5-pro',
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
        Analyze the content. Ensure the output is in Korean.
        """

        with st.spinner("🧠 분석 중..."):
            response = model.generate_content(user_prompt)
            text_response = response.text.replace("```json", "").replace("```", "").strip()
            return json.loads(text_response)

    except Exception as e:
        return {"error": str(e)}

# =============================================================================
# [3] UI 설정 (Pure Text Mode via CSS)
# =============================================================================
st.markdown("""
    <style>
    /* 1. 완벽한 블랙 배경 및 화이트 폰트 */
    .stApp {
        background-color: #000000 !important;
        color: #FFFFFF !important;
    }
    
    /* 2. 입력창 스타일 (진회색 배경, 흰 글씨) */
    .stTextArea textarea {
        background-color: #1a1a1a !important;
        color: #ffffff !important;
        border: 1px solid #444 !important;
    }

    /* 3. 모든 텍스트 강제 화이트 */
    h1, h2, h3, h4, h5, h6, p, label, li, span, div, .stMarkdown {
        color: #FFFFFF !important;
        font-family: 'Apple SD Gothic Neo', 'Malgun Gothic', sans-serif;
    }
    
    /* 4. 사이드바 스타일 */
    [data-testid="stSidebar"] {
        background-color: #111111 !important;
        border-right: 1px solid #333;
    }
    
    /* 5. 결과 텍스트 서식 스타일링 */
    .seq-title {
        font-size: 1.1em;
        margin-top: 30px;
        margin-bottom: 10px;
        line-height: 1.6;
    }
    
    .core-msg {
        font-weight: bold;
        margin-bottom: 10px;
        padding-left: 2px;
    }
    
    .detail-line {
        margin-left: 0px;
        margin-bottom: 5px;
        line-height: 1.6;
        color: #ddd !important; /* 약간 연한 흰색 */
    }
    
    .break-point {
        margin: 40px 0;
        padding: 10px 0;
        border-top: 1px solid #444;
        border-bottom: 1px solid #444;
        line-height: 1.8;
    }
    </style>
    """, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 사이드바
# -----------------------------------------------------------------------------
with st.sidebar:
    st.header("⚙️ 설정")
    api_key = st.text_input("Google Gemini API Key", type="password")

# -----------------------------------------------------------------------------
# 메인 화면
# -----------------------------------------------------------------------------
st.title("📝 문학 강의 논리 분석기")

col1, col2 = st.columns(2)
with col1:
    original_text = st.text_area("1. 작품 원문", height=400)
with col2:
    lecture_script = st.text_area("2. 강의 스크립트", height=400)

analyze_btn = st.button("🚀 분석 시작", type="primary", use_container_width=True)

# -----------------------------------------------------------------------------
# 분석 결과 출력 (요청 서식 완벽 재현)
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
            
            # 메타데이터 출력
            st.markdown(f"### {result.get('metadata', {}).get('title', '분석 결과')}")
            
            sequences = result.get('sequences', [])
            bp = result.get('structure_break_point', {})

            for seq in sequences:
                # 1. <시퀀스N> 요약문 (줄바꿈 없이 한 줄로 보이거나, 자연스럽게 줄바꿈)
                st.markdown(f"""
                <div class="seq-title">
                &lt;시퀀스{seq['seq_id']}&gt; {seq['summary']}
                </div>
                """, unsafe_allow_html=True)
                
                # 2. 핵심 : 메시지 (키워드)
                st.markdown(f"""
                <div class="core-msg">
                핵심 : {seq['core_message']} ({seq['theme_keyword']})
                </div>
                """, unsafe_allow_html=True)
                
                # 3. -팩트 = 해석
                for detail in seq.get('details', []):
                    st.markdown(f"""
                    <div class="detail-line">
                    -{detail['fact']} = {detail['interpretation']}
                    </div>
                    """, unsafe_allow_html=True)

                # 4. 중략/전환점
                if bp and seq['seq_id'] == bp.get('after_sequence'):
                    st.markdown(f"""
                    <div class="break-point">
                    {bp.get('description')}<br>
                    전 = {bp['change_state']['before']}<br>
                    후 = {bp['change_state']['after']}
                    </div>
                    """, unsafe_allow_html=True)
