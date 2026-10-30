import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from datetime import datetime
import base64

st.set_page_config(page_title="실시간 프롬프트 실습 보드", layout="wide")

# --- 1. 서버 공유 메모리 (강의 화면 데이터 + 첨부파일 + 참가자 기록) ---
@st.cache_resource
def get_shared_state():
    return {
        "records": [],
        "material_title": "1차시: 교육과정 재구성 프롬프트 작성법",
        "material_content": """### 💡 프롬프트 작성 핵심 공식
* **역할(Role)**: AI에게 구체적인 전문가 페르소나를 부여하세요.
* **맥락(Context)**: 대상 학년, 성취기준, 수업 상황을 명시하세요.
* **출력 형식(Format)**: 마크다운 표, 개조식 등 원하는 결과 형태를 지정하세요.""",
        "prompt_template": """당신은 교육과정 재구성 전문가입니다.
중학교 2학년 대상의 프로젝트 수업을 설계하려고 합니다.
학생들의 참여를 유도할 수 있는 핵심 질문 3가지와 차시별 활동 계획을 마크다운 표 형식으로 작성해 주세요.""",
        "video_or_slide_url": "",  # 유튜브 강의 영상이나 웹 슬라이드 주소
        "uploaded_file_bytes": None,
        "uploaded_file_name": None,
        "uploaded_file_type": None
    }

state = get_shared_state()
shared_records = state["records"]

# --- 2. 플로팅 모달 창 (원할 때 크게 확대해서 보기) ---
@st.dialog("📌 강의 자료 확대 보기", width="large")
def show_floating_material():
    st.subheader(state["material_title"])
    st.markdown(state["material_content"])
    if state["prompt_template"].strip():
        st.markdown("#### 📋 복사용 프롬프트")
        st.code(state["prompt_template"], language="markdown")

# --- 3. 사이드바: 강사 전용 메뉴 (자료 입력 및 파일 업로드) ---
with st.sidebar:
    st.header("🔒 강사 전용 메뉴")
    admin_pw = st.text_input("강사 비밀번호", type="password", placeholder="기본값: 1234")
    
    if admin_pw == "rlaxornr":
        st.subheader("📝 강의 화면 및 파일 설정")
        new_title = st.text_input("강의 제목", value=state["material_title"])
        new_content = st.text_area("강의 설명 내용 (마크다운/표 지원)", value=state["material_content"], height=150)
        new_prompt = st.text_area("복사용 프롬프트", value=state["prompt_template"], height=120)
        new_url = st.text_input("강의 영상(유튜브) 또는 슬라이드 웹 링크 (선택)", value=state["video_or_slide_url"])
        
        # 그림뿐만 아니라 모든 종류의 파일 업로드 가능
        new_file = st.file_uploader(
            "📎 공유할 파일 첨부 (이미지, PDF, 한글, 워드, 엑셀 등 모두 가능)", 
            type=None
        )
        
        if st.button("🚀 참가자 화면에 즉시 반영", type="primary", use_container_width=True):
            state["material_title"] = new_title
            state["material_content"] = new_content
            state["prompt_template"] = new_prompt
            state["video_or_slide_url"] = new_url.strip()
            if new_file is not None:
                state["uploaded_file_bytes"] = new_file.getvalue()
                state["uploaded_file_name"] = new_file.name
                state["uploaded_file_type"] = new_file.type
            st.success("참가자 화면에 반영되었습니다!")
            st.rerun()
            
        if state["uploaded_file_name"] is not None:
            st.caption(f"현재 첨부된 파일: {state['uploaded_file_name']}")
            if st.button("🗑️ 첨부 파일 지우기", use_container_width=True):
                state["uploaded_file_bytes"] = None
                state["uploaded_file_name"] = None
                state["uploaded_file_type"] = None
                st.rerun()

        st.divider()
        st.subheader(f"📊 참가자 기록 관리 ({len(shared_records)}건)")
        if shared_records:
            df_export = pd.DataFrame(shared_records)
            csv_data = df_export.to_csv(index=False).encode("utf-8-sig")
            st.download_button(
                label="📥 전체 기록 엑셀(CSV) 다운로드",
                data=csv_data,
                file_name=f"특강_참가자기록_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
                use_container_width=True
            )
            if st.button("🗑️ 전체 기록 초기화", use_container_width=True):
                shared_records.clear()
                st.rerun()

# --- 4. 최상단: Streamlit 앱 자체를 미니 플로팅 창으로 띄우는 버튼 ---
col_top1, col_top2, col_top3 = st.columns([2.5, 1, 1])
with col_top1:
    st.title("🚀 실시간 프롬프트 실습 보드")
with col_top2:
    # 클릭 시 현재 Streamlit 앱 자체를 가로 480px, 세로 800px의 미니 플로팅 윈도우로 분리해 띄움
    float_app_html = """
    <button onclick="window.open(window.location.href, 'streamlit_float', 'width=480,height=800,left=1000,top=50,scrollbars=yes,resizable=yes')" 
            style="width:100%; height:42px; margin-top:15px; background-color:#262730; color:white; border:1px solid #4B4B4B; border-radius:8px; font-size:14px; font-weight:bold; cursor:pointer;">
        🗗 이 화면을 미니 플로팅 창으로 띄우기
    </button>
    """
    components.html(float_app_html, height=65)
with col_top3:
    st.write("")
    if st.button("🔍 강의 자료 팝업 확대", use_container_width=True):
        show_floating_material()

# --- 5. 상시 노출되는 강의 화면 영역 (참가자 입력창 바로 위!) ---
with st.container(border=True):
    st.subheader(f"📺 {state['material_title']}")
    
    # 강의 내용과 프롬프트를 좌우 2단으로 깔끔하게 배치
    lec_col1, lec_col2 = st.columns([1.2, 1])
    
    with lec_col1:
        st.markdown(state["material_content"])
        
        # 유튜브 영상이나 슬라이드 링크가 있을 경우 바로 화면에 재생
        if state["video_or_slide_url"]:
            if "youtube.com" in state["video_or_slide_url"] or "youtu.be" in state["video_or_slide_url"]:
                st.video(state["video_or_slide_url"])
            else:
                st.components.v1.iframe(state["video_or_slide_url"], height=300, scrolling=True)
                
    with lec_col2:
        if state["prompt_template"].strip():
            st.markdown("**📋 복사용 프롬프트 (우측 상단 복사 아이콘 클릭)**")
            st.code(state["prompt_template"], language="markdown")
            
        # 첨부 파일이 있을 경우: 다운로드 버튼 제공 + 이미지/PDF는 바로 화면에 표시
        if state["uploaded_file_bytes"] is not None:
            st.divider()
            st.download_button(
                label=f"📥 강의 자료 다운로드 ({state['uploaded_file_name']})",
                data=state["uploaded_file_bytes"],
                file_name=state["uploaded_file_name"],
                mime=state["uploaded_file_type"] or "application/octet-stream",
                type="primary",
                use_container_width=True
            )
            # 이미지 파일이면 바로 화면에 보여주기
            if state["uploaded_file_type"] and state["uploaded_file_type"].startswith("image"):
                st.image(state["uploaded_file_bytes"], use_container_width=True)
            # PDF 파일이면 바로 화면에 PDF 뷰어 띄우기
            elif state["uploaded_file_name"].lower().endswith(".pdf"):
                b64_pdf = base64.b64encode(state["uploaded_file_bytes"]).decode("utf-8")
                pdf_display = f'<iframe src="data:application/pdf;base64,{b64_pdf}" width="100%" height="300px" type="application/pdf"></iframe>'
                st.markdown(pdf_display, unsafe_allow_html=True)

# --- 6. 참가자 실습 내용 입력 및 저장 폼 ---
with st.form("prompt_submission_form", clear_on_submit=True):
    c1, c2 = st.columns([1, 2])
    with c1:
        user_name = st.text_input("이름 (또는 닉네임)", placeholder="예: 김교사")
    with c2:
        step = st.selectbox("실습 단계 선택", [
            "1단계: 기본 프롬프트 변형하기", 
            "2단계: 페르소나 및 맥락 추가하기", 
            "3단계: 최종 결과물 도출하기"
        ])
        
    user_prompt = st.text_area(
        "작성한 프롬프트 또는 AI 생성 결과를 붙여넣어 주세요.", 
        height=110,
        placeholder="여기에 내용을 입력하세요..."
    )
    
    submitted = st.form_submit_button("✅ 기록 저장 및 공유하기", use_container_width=True)
    
    if submitted:
        if user_name.strip() and user_prompt.strip():
            shared_records.append({
                "제출시간": datetime.now().strftime("%H:%M:%S"),
                "이름": user_name.strip(),
                "실습단계": step,
                "작성내용": user_prompt.strip()
            })
            st.toast("기록이 성공적으로 저장되었습니다!", icon="🎉")
            st.rerun()
        else:
            st.warning("이름과 작성 내용을 모두 입력해 주세요.")

st.divider()

# --- 7. 하단: 실시간 전체 참가자 공유 보드 ---
col_title, col_refresh = st.columns([4, 1])
with col_title:
    st.subheader(f"💬 실시간 참여 현황 ({len(shared_records)}건)")
with col_refresh:
    if st.button("🔄 최신글 새로고침", use_container_width=True):
        st.rerun()

if shared_records:
    df_display = pd.DataFrame(shared_records).iloc[::-1]
    st.dataframe(df_display, use_container_width=True, hide_index=True)
else:
    st.info("아직 등록된 기록이 없습니다. 첫 번째로 프롬프트를 제출해 보세요!")
