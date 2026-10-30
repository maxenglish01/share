import streamlit as st
import pandas as pd
from datetime import datetime
import base64

st.set_page_config(page_title="실시간 피드백 실습 보드", layout="wide")

# --- 1. 서버 공유 메모리 ---
@st.cache_resource
def get_shared_state():
    return {
        "records": [],
        "material_title": "1차시: 교육과정 재구성 실습",
        "ppt_url": "",  # 마크다운 내용 대신 PPT 임베드 URL 사용
        "prompt_template": """당신은 교육과정 재구성 전문가입니다.
중학교 2학년 대상의 프로젝트 수업을 설계하려고 합니다.
학생들의 참여를 유도할 수 있는 핵심 질문 3가지와 차시별 활동 계획을 마크다운 표 형식으로 작성해 주세요.""",
        "video_or_slide_url": "",
        "uploaded_file_bytes": None,
        "uploaded_file_name": None,
        "uploaded_file_type": None
    }

state = get_shared_state()
shared_records = state["records"]

# --- 2. 사이드바: 강사 전용 메뉴 ---
with st.sidebar:
    st.header("🔒 강사 전용 메뉴")
    admin_pw = st.text_input("강사 비밀번호", type="password", placeholder="기본값: 1234")
    
    if admin_pw == "1234":
        st.subheader("📝 강의 화면 및 파일 설정")
        new_title = st.text_input("강의 제목", value=state["material_title"])
        new_ppt_url = st.text_input("강의 PPT 임베드 링크 (Google Slides 웹에 게시 등)", value=state["ppt_url"])
        new_prompt = st.text_area("복사용 프롬프트", value=state["prompt_template"], height=120)
        new_url = st.text_input("추가 강의 영상 또는 참고 웹 링크 (선택)", value=state["video_or_slide_url"])
        
        new_file = st.file_uploader(
            "📎 공유할 파일 첨부 (이미지, PDF, 한글, 워드, 엑셀 등)", 
            type=None
        )
        
        if st.button("🚀 참가자 화면에 즉시 반영", type="primary", use_container_width=True):
            state["material_title"] = new_title
            state["ppt_url"] = new_ppt_url.strip()
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

# --- 3. 메인 화면 타이틀 ---
st.title("🚀 실시간 피드백 실습 보드")

# --- 4. 화면 정중앙(상단)에 강조하여 띄우는 강사 제공 자료 카드 ---
with st.container(border=True):
    st.markdown(f"### 📌 [강사 안내 및 자료] {state['material_title']}")
    st.divider()
    
    mat_col1, mat_col2 = st.columns([1.2, 1])
    
    with mat_col1:
        if state["ppt_url"]:
            st.components.v1.iframe(state["ppt_url"], height=400, scrolling=True)
        else:
            st.info("등록된 PPT 화면이 없습니다. 강사 메뉴에서 임베드 링크를 등록해 주세요.")
            
        if state["video_or_slide_url"]:
            st.divider()
            if "youtube.com" in state["video_or_slide_url"] or "youtu.be" in state["video_or_slide_url"]:
                st.video(state["video_or_slide_url"])
            else:
                st.components.v1.iframe(state["video_or_slide_url"], height=300, scrolling=True)
                
    with mat_col2:
        if state["prompt_template"].strip():
            st.markdown("**📋 복사용 프롬프트 (우측 상단 복사 아이콘 클릭)**")
            st.code(state["prompt_template"], language="markdown")
            
        if state["uploaded_file_bytes"] is not None:
            st.divider()
            st.download_button(
                label=f"📥 자료 파일 다운로드 ({state['uploaded_file_name']})",
                data=state["uploaded_file_bytes"],
                file_name=state["uploaded_file_name"],
                mime=state["uploaded_file_type"] or "application/octet-stream",
                type="primary",
                use_container_width=True
            )
            if state["uploaded_file_type"] and state["uploaded_file_type"].startswith("image"):
                st.image(state["uploaded_file_bytes"], use_container_width=True)
            elif state["uploaded_file_name"].lower().endswith(".pdf"):
                b64_pdf = base64.b64encode(state["uploaded_file_bytes"]).decode("utf-8")
                pdf_display = f'<iframe src="data:application/pdf;base64,{b64_pdf}" width="100%" height="300px" type="application/pdf"></iframe>'
                st.markdown(pdf_display, unsafe_allow_html=True)

st.divider()

# --- 5. 참가자 피드백 제출 폼 ---
with st.form("feedback_submission_form", clear_on_submit=True):
    st.subheader("📝 실시간 피드백 제출")
    c1, c2 = st.columns([1, 2])
    with c1:
        user_name = st.text_input("이름", placeholder="예: 홍길동")
    with c2:
        understanding = st.selectbox("오늘의 학습 이해도 자가평가", [
            "⭐⭐⭐⭐⭐ 매우 잘 이해함", 
            "⭐⭐⭐⭐ 대체로 이해함", 
            "⭐⭐⭐ 보통 (절반 정도 이해함)",
            "⭐⭐ 약간 어려움",
            "⭐ 너무 어려움 / 전혀 모르겠음"
        ])
        
    user_feedback = st.text_area(
        "오늘 배운 핵심 내용 요약 및 소감 (어려웠던 점 등)", 
        height=110,
        placeholder="오늘 강의에서 가장 기억에 남는 내용이나, 실습하며 어려웠던 점 등을 자유롭게 남겨주세요."
    )
    
    submitted = st.form_submit_button("✅ 피드백 제출하기", use_container_width=True)
    
    if submitted:
        if user_name.strip() and user_feedback.strip():
            shared_records.append({
                "제출시간": datetime.now().strftime("%H:%M:%S"),
                "이름": user_name.strip(),
                "이해도": understanding.split(' ')[0],  # 별점만 저장하려면 이렇게 처리
                "핵심 요약 및 소감": user_feedback.strip()
            })
            st.toast("피드백이 성공적으로 저장되었습니다!", icon="🎉")
            st.rerun()
        else:
            st.warning("이름과 작성 내용을 모두 입력해 주세요.")

st.divider()

# --- 6. 하단: 실시간 전체 참가자 공유 보드 ---
col_title, col_refresh = st.columns([4, 1])
with col_title:
    st.subheader(f"💬 실시간 피드백 현황 ({len(shared_records)}건)")
with col_refresh:
    if st.button("🔄 최신글 새로고침", use_container_width=True):
        st.rerun()

if shared_records:
    df_display = pd.DataFrame(shared_records).iloc[::-1]
    st.dataframe(df_display, use_container_width=True, hide_index=True)
else:
    st.info("아직 등록된 기록이 없습니다. 첫 번째로 피드백을 제출해 보세요!")
