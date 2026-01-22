import streamlit as st
import google.generativeai as genai
import json
import re

# =============================================================================
# [0] 페이지 설정 (심플한 다크 모드)
# =============================================================================
st.set_page_config(page_title="문학 강의 논리 분석기", page_icon="📝", layout="wide")

st.markdown("""
    <style>
    /* 1. 전체 앱 배경 (검정) */
    .stApp {
        background-color: #000000 !important;
        color: #FFFFFF !important;
    }
    
    /* 2. 사이드바 배경 (완전 검정으로 통일) */
    [data-testid="stSidebar"] {
        background-color: #000000 !important; /* 여기를 검정으로 변경 */
        border-right: 1px solid #333;
    }
    
    /* 3. 입력창 스타일 (어두운 회색) */
    .stTextArea textarea {
        background-color: #1E1E1E !important;
        color: #FFFFFF !important;
        border: 1px solid #444 !important;
    }
    .stTextInput input {
        background-color: #1E1E1E !important;
        color: #FFFFFF !important;
        border: 1px solid #444 !important;
    }
    
    /* 4. 헤더, 텍스트 색상 강제 화이트 */
    h1, h2, h3, h4, h5, h6, p, div, span, label, li {
        color: #FFFFFF !important;
    }
    
    /* 5. 버튼 스타일 (다크 모드에 맞게) */
    .stButton button {
        background-color: #222 !important;
        color: #fff !important;
        border: 1px solid #555 !important;
    }
    
    /* 6. 결과 출력 텍스트 스타일 */
    .result-text {
        font-size: 16px;
        line-height: 1.8;
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

# [UI] 우측 상단에 인터넷 이미지 고정하기
st.markdown("""
    <style>
    .top-right-image {
        position: fixed; /* 스크롤해도 고정됨 (원치 않으면 absolute로 변경) */
        top: 70px;       /* 위에서 얼마나 띄울지 */
        right: 50px;     /* 오른쪽에서 얼마나 띄울지 */
        width: 200px;    /* 사진 크기 (원하는 대로 조절) */
        z-index: 1000;   /* 다른 요소보다 위에 오도록 */
        border-radius: 10px; /* 모서리 둥글게 (싫으면 삭제) */
        opacity: 0.9;    /* 투명도 (1.0이 불투명) */
    }
    </style>
    <img src="https://i.namu.wiki/i/Iie8i1o1dVcRnzTjU2nHmgjjaFbImjnr0sjSeuI9g5PtSF4JyXZn1U2aLBZdNIh4tVzy8B6IyB_AMA6KkcKXqw7lnLTVPHTZQk9x2_PhNDFZeKJKXuFqyH-evDi4AYM2ev-Ye_IJfpFnNZy8WQVYFQ.webp" class="top-right-image">
    """, unsafe_allow_html=True)


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
# =============================================================================
# [2] API Function (Modified for Sequence Control)
# =============================================================================
def analyze_with_gemini(api_key, original, script, target_count): # <--- target_count 인자 추가됨
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(
            model_name='gemini-2.5-flash', # 혹은 gemini-1.5-pro
            system_instruction=SYSTEM_INSTRUCTION
        )

        # 사용자 프롬프트에 '목표 개수'를 강제로 주입
        user_prompt = f"""
        ---
        [Original Text]
        {original}
        
        ---
        [Lecture Script]
        {script}
        
        ---
        [CRITICAL INSTRUCTION]
        Divide the content into EXACTLY {target_count} sequences (or close to {target_count}).
        Do not summarize too briefly; ensure enough detail to meet the target count of {target_count}.
        
        Analyze and Output strictly valid JSON.
        """

        with st.spinner(f"🧠 {target_count}개의 시퀀스로 정밀 분석 중..."):
            response = model.generate_content(user_prompt)
            raw_text = response.text
            match = re.search(r'\{.*\}', raw_text, re.DOTALL)
            if match:
                return json.loads(match.group(0))
            else:
                return {"error": "AI가 JSON을 반환하지 않음", "raw": raw_text}

    except Exception as e:
        return {"error": str(e)}
# [추가] 시퀀스 개수 설정 슬라이더
    target_seq_count = st.slider("🎯 희망 시퀀스 개수", min_value=3, max_value=10, value=6, step=1, help="AI에게 몇 개의 장면으로 나누라고 할지 지시합니다.")
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
        # target_seq_count 변수를 함수에 전달
        result = analyze_with_gemini(api_key, original_text, lecture_script, target_seq_count)
        
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
