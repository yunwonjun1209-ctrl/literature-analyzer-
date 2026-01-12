import streamlit as st
import google.generativeai as genai
import json
import re

# =============================================================================
# [0] 페이지 설정 (심플한 다크 모드)
# =============================================================================
st.set_page_config(page_title="문학 강의 논리 분석기", page_icon="📝", layout="wide")

# CSS: 배경은 어둡게, 글씨는 밝게 (복잡한 클래스 제거)
st.markdown("""
    <style>
    .stApp {
        background-color: #1E1E1E; /* 진한 회색 배경 */
    }
    .stTextArea textarea {
        background-color: #2D2D2D !important;
        color: #FFFFFF !important;
    }
    h1, h2, h3, p, div, span, li {
        color: #E0E0E0 !important; /* 밝은 회색 글씨 */
        font-family: sans-serif;
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
    password_input = st.text_input("비밀번호를 입력하세요", type="password")
    
    if password_input:
        if "ACCESS_PASSWORD" in st.secrets and password_input == st.secrets["ACCESS_PASSWORD"]:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("비밀번호가 일치하지 않습니다.")
    st.stop()

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
            match = re.search(r'\{.*\}', raw_text, re.DOTALL)
            if match:
                return json.loads(match.group(0))
            else:
                return {"error": "AI가 JSON을 반환하지 않음", "raw": raw_text}

    except Exception as e:
        return {"error": str(e)}

# =============================================================================
# [3] 메인 화면 UI (가독성 수정됨)
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
            st.divider()
            
            # 제목 출력
            title = result.get('metadata', {}).get('title', '분석 결과')
            st.subheader(f"📂 {title}")
            st.markdown("<br>", unsafe_allow_html=True)

            sequences = result.get('sequences', [])
            bp = result.get('structure_break_point', {})

            for seq in sequences:
                # 1. 시퀀스 헤더 (빨간색 강조)
                st.markdown(f"### <span style='color:#FF8A80'>&lt;시퀀스{seq['seq_id']}&gt;</span> {seq['summary']}", unsafe_allow_html=True)
                
                # 2. 핵심 메시지 (파란색 강조)
                st.markdown(f"**핵심 : <span style='color:#81D4FA'>{seq['core_message']}</span> ({seq['theme_keyword']})**", unsafe_allow_html=True)
                
                # 3. 디테일 (일반 텍스트)
                for detail in seq.get('details', []):
                    st.write(f"- {detail['fact']} = {detail['interpretation']}")
                
                st.markdown("<br>", unsafe_allow_html=True) # 줄바꿈

                # 4. 중략/전환점
                if bp and seq['seq_id'] == bp.get('after_sequence'):
                    st.markdown("---")
                    st.markdown(f"#### 🔄 {bp.get('description')}")
                    st.write(f"전 = {bp['change_state']['before']}")
                    st.write(f"후 = {bp['change_state']['after']}")
                    st.markdown("---")
                    st.markdown("<br>", unsafe_allow_html=True)
