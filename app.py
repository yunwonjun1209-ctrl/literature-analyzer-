import streamlit as st
import google.generativeai as genai
import json
import re


# =============================================================================
# [0] 페이지 설정 및 디자인 (블랙 모드 & 텍스트 서식 최적화)
# =============================================================================
st.set_page_config(page_title="문학 강의 논리 분석기", page_icon="📝", layout="wide")

st.markdown("""
    <style>
    /* 1. 전체 배경: 딥 다크 모드 (완전 검정이 아닌 세련된 다크그레이) */
    .stApp {
        background-color: #121212 !important;
        color: #E0E0E0 !important;
        font-family: 'Pretendard', 'Apple SD Gothic Neo', sans-serif;
    }
    
    /* 2. 헤더 및 일반 텍스트 색상 (밝은 회색) */
    h1, h2, h3, h4, h5, h6 {
        color: #FFFFFF !important;
        font-weight: 700;
        letter-spacing: -0.5px;
    }
    p, span, label, li, div {
        color: #E0E0E0 !important;
        line-height: 1.6;
    }
    
    /* 3. 입력창 스타일 (모던한 다크 테마) */
    .stTextArea textarea {
        background-color: #1E1E1E !important;
        color: #FFFFFF !important;
        border: 1px solid #333 !important;
        border-radius: 8px;
        padding: 15px;
        font-size: 15px;
    }
    .stTextArea textarea:focus {
        border-color: #4A90E2 !important; /* 포커스 시 파란색 강조 */
    }
    
    /* 4. 사이드바 스타일 (차분한 톤) */
    [data-testid="stSidebar"] {
        background-color: #0A0A0A !important;
        border-right: 1px solid #222;
    }
    
    /* 5. 버튼 스타일 (그라데이션 효과) */
    .stButton button {
        background: linear-gradient(90deg, #4A90E2, #50C9C3);
        color: white !important;
        border: none;
        border-radius: 8px;
        font-weight: bold;
        padding: 10px 20px;
        transition: all 0.3s ease;
    }
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(74, 144, 226, 0.4);
    }

    /* 6. 결과 텍스트 출력 스타일 (카드형 레이아웃 + 가독성) */
    .result-container {
        max-width: 900px;
        margin: 0 auto;
        padding: 20px;
    }
    
    .sequence-card {
        background-color: #1E1E1E;
        border-radius: 12px;
        padding: 25px;
        margin-bottom: 30px;
        border: 1px solid #333;
        box-shadow: 0 4px 6px rgba(0,0,0,0.2);
    }
    
    .seq-header {
        font-size: 1.3em;
        font-weight: 800;
        color: #FF8A80 !important; /* 살구색 포인트 */
        margin-bottom: 15px;
        padding-bottom: 10px;
        border-bottom: 1px solid #333;
    }
    
    .core-msg {
        font-size: 1.1em;
        font-weight: 700;
        color: #81D4FA !important; /* 하늘색 포인트 */
        background-color: rgba(129, 212, 250, 0.1);
        padding: 12px;
        border-radius: 6px;
        margin-bottom: 20px;
        border-left: 4px solid #81D4FA;
    }
    
    .detail-line {
        font-size: 1em;
        color: #F5F5F5 !important;
        margin-bottom: 12px;
        padding-left: 10px;
        border-left: 2px solid #555;
    }
    
    .break-point {
        background-color: #2C2C2C;
        color: #FFD54F !important; /* 노란색 포인트 */
        padding: 20px;
        border-radius: 8px;
        text-align: center;
        margin: 40px 0;
        font-weight: bold;
        border: 1px dashed #555;
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
           # [결과 출력 로직 - 디자인 적용 버전]
            output_html = f"""<div class="result-container">"""
            
            # 1. 제목
            title = result.get('metadata', {}).get('title', '분석 결과')
            output_html += f"<h2 style='text-align:center; margin-bottom:40px;'>📂 {title}</h2>"

            sequences = result.get('sequences', [])
            bp = result.get('structure_break_point', {})

            for seq in sequences:
                # 카드 시작
                output_html += f"""<div class="sequence-card">"""
                
                # 시퀀스 헤더 & 요약
                output_html += f"""
                <div class="seq-header">&lt;시퀀스{seq['seq_id']}&gt; {seq['summary']}</div>
                """
                
                # 핵심 메시지
                output_html += f"""
                <div class="core-msg">🔑 핵심 : {seq['core_message']} ({seq['theme_keyword']})</div>
                """
                
                # 상세 내용
                for detail in seq.get('details', []):
                    output_html += f"""
                    <div class="detail-line">● {detail['fact']} <br><span style='color:#bbb; font-size:0.9em;'>&nbsp;&nbsp;↳ {detail['interpretation']}</span></div>
                    """
                
                output_html += "</div>" # 카드 끝

                # 중략/전환점
                if bp and seq['seq_id'] == bp.get('after_sequence'):
                    output_html += f"""
                    <div class="break-point">
                        🔄 {bp.get('description')}<br><br>
                        <span style='color:#aaa;'>[전]</span> {bp['change_state']['before']}<br>
                        <span style='color:#fff;'>↓</span><br>
                        <span style='color:#aaa;'>[후]</span> {bp['change_state']['after']}
                    </div>
                    """
            
            output_html += "</div>"
            st.markdown(output_html, unsafe_allow_html=True)
