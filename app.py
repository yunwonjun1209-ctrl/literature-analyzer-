import streamlit as st
import google.generativeai as genai
import json

# =============================================================================
# [0] 페이지 설정 및 디자인 (블랙 모드 & 텍스트 서식 최적화)
# =============================================================================
st.set_page_config(page_title="문학 강의 논리 분석기", page_icon="📝", layout="wide")

st.markdown("""
    <style>
    /* 1. 전체 배경 및 폰트: 검정 배경, 흰색 텍스트 */
    .stApp {
        background-color: #000000 !important;
        color: #FFFFFF !important;
        font-family: 'Apple SD Gothic Neo', 'Malgun Gothic', sans-serif;
    }
    
    /* 2. 모든 텍스트 강제 화이트 */
    h1, h2, h3, h4, h5, h6, p, div, span, label, li, textarea {
        color: #FFFFFF !important;
    }
    
    /* 3. 입력창 스타일 */
    .stTextArea textarea {
        background-color: #1a1a1a !important;
        color: #ffffff !important;
        border: 1px solid #444 !important;
    }
    
    /* 4. 사이드바 */
    [data-testid="stSidebar"] {
        background-color: #0a0a0a !important;
        border-right: 1px solid #333;
    }
    
    /* 5. 결과 출력용 서식 (줄간격 및 스타일) */
    .result-container {
        font-size: 16px;
        line-height: 1.8;
    }
    .seq-header {
        font-weight: bold;
        color: #FFFFFF;
        margin-top: 25px;
    }
    .core-msg {
        color: #81D4FA !important; /* 핵심은 살짝 푸른빛으로 구분 */
        font-weight: bold;
    }
    .break-point {
        margin: 30px 0;
        padding: 15px 0;
        border-top: 1px dashed #555;
        border-bottom: 1px dashed #555;
        color: #FFD54F !important; /* 중략은 노란빛 */
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
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        password_input = st.text_input("비밀번호를 입력하세요", type="password")
        if password_input:
            if "ACCESS_PASSWORD" in st.secrets and password_input == st.secrets["ACCESS_PASSWORD"]:
                st.session_state.authenticated = True
                st.rerun()
            elif "ACCESS_PASSWORD" not in st.secrets:
                st.error("Secrets에 비밀번호가 설정되지 않았습니다.")
            else:
                st.error("비밀번호가 일치하지 않습니다.")
    st.stop()

# =============================================================================
# [1] 시스템 프롬프트 (Few-Shot Prompting: 예시를 학습시킴)
# =============================================================================
SYSTEM_INSTRUCTION = """
You are a Literature Analysis AI Expert specializing in 'Park Seok-jun's Lecture Style'.

[CRITICAL INSTRUCTION]
Do not just summarize. You must map the [Original Text] directly to the [Lecture Script]'s logic.
The output MUST follow the specific JSON format that separates 'Fact' and 'Interpretation'.
Use the [Example Analysis] below as your absolute guide for logic and depth.

---
[Example Analysis Logic]
Input Text: "The lame man howled like a beast."
Input Lecture: "The teacher explains that physical injury leads to mental pain and hostility."
Output Logic: Fact="howled like a beast" -> Interpretation="Mental pain caused by physical injury (Expression of dissatisfaction)"

[Reference Format Example - You must output JSON like this]
{
  "metadata": { "title": "Title" },
  "structure_break_point": {
    "after_sequence": 3,
    "description": "Situation Change",
    "change_state": { "before": "Before state", "after": "After state" }
  },
  "sequences": [
    {
      "seq_id": 1,
      "summary": "Summary of this scene",
      "core_message": "Main Lecture Point",
      "theme_keyword": "Keyword",
      "details": [
        {"fact": "Specific quote or word from Original Text", "interpretation": "Specific explanation from Lecture Script linked to this fact"}
      ]
    }
  ]
}
---

Your task:
1. Divide the text into logical Sequences based on the Lecture flow.
2. For each sequence, identify the 'Core Message' emphasized by the lecturer.
3. Find the specific 'Fact' in the text that the lecturer uses as evidence.
4. Provide the 'Interpretation' exactly as the lecturer explains it.
5. All output must be in Korean (한국어).
"""

# =============================================================================
# [2] API 통신 함수
# =============================================================================
def analyze_with_gemini(api_key, original, script):
    try:
        genai.configure(api_key=api_key)
        # 1.5 Pro 모델 사용 (복잡한 논리 추론에 필수)
        model = genai.GenerativeModel(
            model_name='gemini-2.5-flash',
            system_instruction=SYSTEM_INSTRUCTION
        )

        user_prompt = f"""
        Analyze the following inputs deeply.
        
        ---
        [Original Text]
        {original}
        
        ---
        [Lecture Script]
        {script}
        
        ---
        Output valid JSON only.
        """

        with st.spinner("🧠 선생님의 강의 논리를 정밀 분석 중입니다..."):
            response = model.generate_content(user_prompt)
            # JSON 클리닝
            text_response = response.text.replace("```json", "").replace("```", "").strip()
            return json.loads(text_response)

    except Exception as e:
        return {"error": str(e)}

# =============================================================================
# [3] 메인 화면 UI
# =============================================================================
st.title("문학 강의 논리 분석기")
st.markdown("선생님의 강의 스크립트와 원문을 비교하여 **<시퀀스> 논리 구조**를 추출합니다.")

col1, col2 = st.columns(2)
with col1:
    original_text = st.text_area("1. 작품 원문", height=500, placeholder="분석할 소설 원문을 넣어주세요.")
with col2:
    lecture_script = st.text_area("2. 강의 스크립트", height=500, placeholder="선생님의 강의 녹취록을 넣어주세요.")

with st.sidebar:
    st.header("설정")
    api_key = st.text_input("Google Gemini API Key", type="password")

if st.button("🚀 정밀 분석 시작", use_container_width=True):
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
            
            # HTML 문자열 생성 (줄글 서식 구현)
            html = '<div class="result-container">'
            
            # 제목
            title = result.get('metadata', {}).get('title', '분석 결과')
            html += f"<h3>📂 {title}</h3><br>"

            sequences = result.get('sequences', [])
            bp = result.get('structure_break_point', {})

            for seq in sequences:
                # 시퀀스 헤더
                html += f"""
                <div class="seq-header">&lt;시퀀스{seq['seq_id']}&gt; {seq['summary']}</div><br>
                """
                
                # 핵심 메시지
                html += f"""
                <span class="core-msg">핵심 : {seq['core_message']} ({seq['theme_keyword']})</span><br>
                """
                
                # 상세 내용 (-팩트 = 해석)
                for detail in seq.get('details', []):
                    html += f"-{detail['fact']} = {detail['interpretation']}<br>"
                
                html += "<br>" # 시퀀스 간격

                # 중략/전환점
                if bp and seq['seq_id'] == bp.get('after_sequence'):
                    html += f"""
                    <div class="break-point">
                        {bp.get('description')}<br>
                        전 = {bp['change_state']['before']}<br>
                        후 = {bp['change_state']['after']}
                    </div>
                    """
            
            html += '</div>'
            st.markdown(html, unsafe_allow_html=True)
