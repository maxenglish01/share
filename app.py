import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="실시간 프롬프트 실습 보드", layout="wide")

# --- 1. 서버 공유 메모리 (강사가 붙여넣은 자료 + 참가자 기록 저장소) ---
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
        "uploaded_image": None  # 강사가 올린 이미지 데이터 저장
    }

state = get_shared_state()
shared_records = state["records"]

# --- 2. 참가자 화면에 뜨는 플로팅(모달 팝업) 창 ---
@st.dialog("📌 강사 제공 자료 및 프롬프트", width="large")
def show_floating_material():
    st.subheader(state["material_title"])
    
    # 강사가 이미지를 첨부했다면 플로팅 창에 표시
    if state["uploaded_image"] is not None:
        st.image(state["uploaded_image"], use_container_width=True)
        
    # 강사가 붙여넣은 본문 자료 표시 (표, 굵은 글씨 등 자동 변환)
    st.markdown(state["material_content"])
    
    # 강사가 붙여넣은 복사용 프롬프트 표시
    if state["prompt_template"].strip():
        st.divider()
        st.markdown("#### 📋 복사용 기본 프롬프트 (우측 상단 복사 아이콘 클릭)")
        st.code(state["prompt_template"], language="markdown")

# --- 3. 사이드바: 강사 전용 입력창 및 엑셀 다운로드 ---
with st.sidebar:
    st.header("🔒 강사 전용 메뉴")
    admin_pw = st.text_input("강사 비밀번호", type="password", placeholder="기본값: 1234")
    
    if admin_pw == "1234":
        st.subheader("📝 플로팅 창 자료 바로 입력")
        st.caption("여기에 내용을 붙여넣고 반영 버튼을 누르면 참가자들의 플로팅 창이 즉시 바뀝니다.")
        
        new_title = st.text_input("자료 제목", value=state["material_title"])
        new_content = st.text_area(
            "참고 자료 내용 (텍스트, 마크다운 표 등 붙여넣기)", 
            value=state["material_content"], 
            height=180
        )
        new_prompt = st.text_area(
            "복사용 프롬프트 (참가자가 복사해 갈 내용)", 
            value=state["prompt_template"], 
            height=130
        )
        new_img = st.file_uploader("참고 이미지 첨부 (선택)", type=["png", "jpg", "jpeg"])
        
        if st.button("🚀 참가자 화면에 즉시 띄우기", type="primary", use_container_width=True):
            state["material_title"] = new_title
            state["material_content"] = new_content
            state["prompt_template"] = new_prompt
            if new_img is not None:
                state["uploaded_image"] = new_img.getvalue()
            st.success("참가자 플로팅 창에 즉시 반영되었습니다!")
            st.rerun()
            
        if state["uploaded_image"] is not None:
            if st.button("🖼️ 첨부된 이미지 지우기", use_container_width=True):
                state["uploaded_image"] = None
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
        else:
            st.caption("아직 제출된 기록이 없습니다.")

# --- 4. 메인 화면 상단: 플로팅 창 열기 버튼 & 상시 미리보기 ---
st.title("🚀 실시간 프롬프트 실습 보드")

col_info, col_btn = st.columns([2, 1])
with col_info:
    st.info(f"**현재 진행 중인 주제:** {state['material_title']}")
with col_btn:
    if st.button("📖 강사 자료 & 프롬프트 띄우기 (플로팅 창)", type="primary", use_container_width=True):
        show_floating_material()

st.divider()

# --- 5. 참가자 실습 내용 입력 및 저장 폼 ---
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
        height=130,
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

# --- 6. 하단: 실시간 전체 참가자 공유 보드 ---
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
