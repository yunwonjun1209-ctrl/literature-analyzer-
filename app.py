import streamlit as st
import google.generativeai as genai
import json

# =============================================================================
# [0] 페이지 설정 및 디자인 초기화 (꾸밈 요소 제거)
# =============================================================================
st.set_page_config(page_title="문학 강의 논리 분석기", page_icon="📝", layout="wide")

# CSS: 완벽한 검은 배경 + 흰 글씨 + 여백 조정 (카드/박스 디자인 제거)
st.markdown("""
    <style>
    /* 1. 전체 배경 및 폰트: 검정 배경, 흰색 텍스트 */
    .stApp {
        background-color: #000000 !important;
        color: #FFFFFF !important;
        font-family: 'Apple SD Gothic Neo', 'Malgun Gothic', sans-serif;
    }
    
    /* 2. 모든 텍스트 강제 화이트 (헤더, 본문, 라벨 등) */
    h1, h2, h3, h4, h5, h6, p, div, span, label, li {
        color: #FFFFFF !important;
    }
    
    /* 3. 입력창 스타일: 어두운 회색 배경, 흰 글씨, 테두리 최소화 */
    .stTextArea textarea {
        background-color: #1a1a1a !important;
        color: #ffffff !important;
        border: 1px solid #444 !important;
    }
    
    /* 4. 사이드바: 약간 더 어두운 톤 */
    [data-testid="stSidebar"] {
        background-color: #0a0a0a !important;
        border-right: 1px solid #333;
    }
    
    /* 5. 버튼 스타일: 심플한 회색/파란색 톤 */
    .stButton button {
        background-color: #333 !important;
        color: white !important;
        border: 1px solid #555 !important;
    }
    .stButton button:hover {
        border-color: #888 !important;
    }

    /* 6. 결과 출력용 서식 (줄간격 및 폰트 사이즈) */
    .result-text {
        font-size: 16px;
        line-height: 1.8;
        white-space: pre-wrap; /* 줄바꿈 보존 */
    }
    
    /* 구분선 스타일 */
    hr {
        border-color: #333 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# =============================================================================
# [SECRET] 비밀번호 보호 로직
# =============================================================================
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔒 접근 제한")
    st.markdown("관계자 외 접근이 불가능합니다.")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        password_input = st.text_input("비밀번호를 입력하세요", type="password")
        if password_input:
            # st.secrets에 저장된 'ACCESS_PASSWORD'와 비교
            if "ACCESS_PASSWORD" in st.secrets and password_input == st.secrets["ACCESS_PASSWORD"]:
                st.session_state.authenticated = True
                st.rerun()
            elif "ACCESS_PASSWORD" not in st.secrets:
                st.error("서버에 비밀번호가 설정되지 않았습니다. (Secrets 설정 필요)")
            else:
                st.error("비밀번호가 일치하지 않습니다.")
    st.stop()

# =============================================================================
# [1] 시스템 프롬프트 (엄격한 줄글 포맷팅 지시)
# =============================================================================
SYSTEM_INSTRUCTION = """
You are a Literature Analysis AI.
Your task is to analyze the 'Original Text' and 'Lecture Script' and output the logic in a specific JSON structure.

[CRITICAL INSTRUCTION]
The user requires the output to strictly follow a specific TEXT format when rendered.
You must extract:
1. Sequence Number & Summary
2. Core Message & Theme Keyword
3. Specific Facts from text AND the Teacher's Interpretation of that fact.

[JSON Structure Requirement]
{
  "metadata": { "title": "Title" },
  "structure_break_point": {
    "after_sequence": 3,
    "description": "Situation Description",
    "change_state": { "before": "State Before", "after": "State After" }
  },
  "sequences": [
    {
      "seq_id": 1,
      "summary": "Full summary of sequence",
      "core_message": "Core message",
      "theme_keyword": "Theme",
      "details": [
        {"fact": "Quote/Fact from text", "interpretation": "Interpretation"}
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
        Analyze the content. All output must be in Korean.
        Ensure 'Fact' and 'Interpretation' are clearly separated in the logic.
        """

        with st.spinner("Analyzing..."):
            response = model.generate_content(user_prompt)
            text_response = response.text.replace("```json", "").replace("```", "").strip()
            return json.loads(text_response)

    except Exception as e:
        return {"error": str(e)}

# =============================================================================
# [3] 메인 화면 UI
# =============================================================================
st.title("문학 강의 논리 분석기")
st.markdown("---")

# 입력 폼
col1, col2 = st.columns(2)
with col1:
    original_text = st.text_area("1. 작품 원문", height=400)
with col2:
    lecture_script = st.text_area("2. 강의 스크립트", height=400)

# 사이드바 (API 키 입력)
with st.sidebar:
    st.header("설정")
    api_key = st.text_input("Google Gemini API Key", type="password")

# 분석 버튼
if st.button("분석 시작", use_container_width=True):
    if not api_key:
        st.error("API Key를 입력해주세요.")
    elif not original_text or not lecture_script:
        st.warning("내용을 모두 입력해주세요.")
    else:
        result = analyze_with_gemini(api_key, original_text, lecture_script)
        
        if "error" in result:
            st.error(f"오류: {result['error']}")
        else:
            st.markdown("---")
            
            # [핵심] 결과 출력 로직 (HTML/CSS로 줄글 서식 강제 구현)
            # 사용자가 요청한 서식을 그대로 재현합니다.
            
            output_html = f"""<div class="result-text">"""
            
            # 1. 제목 (선택사항)
            title = result.get('metadata', {}).get('title', '')
            if title:
                output_html += f"<h3>{title}</h3><br>"

            sequences = result.get('sequences', [])
            bp = result.get('structure_break_point', {})

            for seq in sequences:
                # <시퀀스N> 요약
                output_html += f"<b>&lt;시퀀스{seq['seq_id']}&gt; {seq['summary']}</b><br><br>"
                
                # 핵심 : 메시지 (키워드)
                output_html += f"핵심 : {seq['core_message']} ({seq['theme_keyword']})<br>"
                
                # -팩트 = 해석
                for detail in seq.get('details', []):
                    output_html += f"-{detail['fact']} = {detail['interpretation']}<br>"
                
                output_html += "<br>" # 시퀀스 간 간격

                # 중략/전환점 (Break Point)
                if bp and seq['seq_id'] == bp.get('after_sequence'):
                    output_html += f"{bp.get('description')}<br>"
                    output_html += f"전 = {bp['change_state']['before']}<br>"
                    output_html += f"후 = {bp['change_state']['after']}<br><br>"
            
            output_html += "</div>"
            
            # Streamlit에 HTML 렌더링 (디자인 요소 없이 텍스트만 출력)
            st.markdown(output_html, unsafe_allow_html=True)
