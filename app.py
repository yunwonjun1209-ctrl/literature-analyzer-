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

import streamlit as st
import google.generativeai as genai
import json

# =============================================================================
# [1] 시스템 프롬프트 (정답 서식 학습)
# =============================================================================
SYSTEM_INSTRUCTION = """
You are a Literary Analysis AI.
Your ONLY goal is to analyze the input Text/Script and output JSON that fits the user's specific text format EXACTLY.

[CRITICAL: OUTPUT FORMAT RULE]
You must output data so it can be rendered EXACTLY like this example:

<시퀀스1> Summary Sentence...
핵심 : Core Message... (Theme)
-Fact Text = Interpretation Text
-Fact Text = Interpretation Text

[FEW-SHOT LEARNING DATA (Correct Answer Example)]
Input: (Text/Script about 'Graveyard Nearby')
Output JSON:
{
  "metadata": { "title": "윤흥길, 묘지 근처" },
  "structure_break_point": {
    "after_sequence": 4,
    "description": "중략 기준 상황, 인식의 변화",
    "change_state": {
      "before": "할머니의 영향 아래 갇힌 인식 (상이군인 = 저승사자)",
      "after": "할머니의 죽음으로 인한 인식의 확장 (더 넓은 세계의 자각)"
    }
  },
  "sequences": [
    {
      "seq_id": 1,
      "summary": "할머니와 ‘나’는 절름발이 사내를 저승사자로 여기며 적대감을 보이고...",
      "core_message": "전쟁의 폭력성으로 인한 신체적 손상과 그로 인한 정신적 고통.",
      "theme_keyword": "전쟁의 비극성",
      "details": [
        {"fact": "절름발이 사내, 다리를 잃은 청년", "interpretation": "신체적 손상 (공통 범주)"},
        {"fact": "식판을 노려보며 천둥을 내리쳤다", "interpretation": "신체적 손상으로 인한 정신적 고통"}
      ]
    }
  ]
}

Now, analyze the NEW input following this EXACT Logic and JSON Structure.
Output MUST be in Korean.
"""

# =============================================================================
# [2] API 통신 함수
# =============================================================================
def analyze_with_gemini(api_key, original, script):
    try:
        genai.configure(api_key=api_key)
        # 1.5 Pro 모델 (논리 분석 최적화)
        model = genai.GenerativeModel(
            model_name='gemini-2.5-flash',
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
        Analyze and Output strictly valid JSON.
        """

        with st.spinner("🧠 정밀 분석 중..."):
            response = model.generate_content(user_prompt)
            raw_text = response.text
            # JSON 추출 (안전장치)
            match = re.search(r'\{.*\}', raw_text, re.DOTALL)
            if match:
                return json.loads(match.group(0))
            else:
                return {"error": "AI가 JSON을 반환하지 않음", "raw": raw_text}

    except Exception as e:
        return {"error": str(e)}

# =============================================================================
# [3] 메인 화면 UI (줄바꿈이 적용된 텍스트 출력)
# =============================================================================
st.title("문학 강의 논리 분석기")
st.markdown("---")

col1, col2 = st.columns(2)
with col1:
    original_text = st.text_area("1. 작품 원문", height=500)
with col2:
    lecture_script = st.text_area("2. 강의 스크립트", height=500)

with st.sidebar:
    st.header("설정")
    api_key = st.text_input("Google Gemini API Key", type="password")

if st.button("🚀 분석 시작", use_container_width=True):
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
            
            # [최종 출력 로직] 줄바꿈(<br>)을 적극적으로 활용하여 간격 확보
            html = '<div class="result-text">'
            
            # 제목
            title = result.get('metadata', {}).get('title', '분석 결과')
            html += f"<h3>📂 {title}</h3><br>"

            sequences = result.get('sequences', [])
            bp = result.get('structure_break_point', {})

            for seq in sequences:
                # 1. <시퀀스N> 요약
                html += f"""
                <div class="seq-header">&lt;시퀀스{seq['seq_id']}&gt; {seq['summary']}</div>
                """
                
                # 2. 핵심 : 메시지 (테마) - 아래에 빈 줄 추가
                html += f"""
                <div class="core-msg">핵심 : {seq['core_message']} ({seq['theme_keyword']})</div>
                """
                
                # 3. -팩트 = 해석 (각 줄마다 div로 감싸고 margin-bottom 적용)
                for detail in seq.get('details', []):
                    html += f"""
                    <div class="detail-line">-{detail['fact']} = {detail['interpretation']}</div>
                    """
                
                html += "<br>" # 시퀀스 간격 추가

                # 4. 중략/전환점
                if bp and seq['seq_id'] == bp.get('after_sequence'):
                    html += f"""
                    <div class="break-point">
                        {bp.get('description')}<br><br>
                        전 = {bp['change_state']['before']}<br>
                        후 = {bp['change_state']['after']}
                    </div><br>
                    """
            
            html += "</div>"
            st.markdown(html, unsafe_allow_html=True)
