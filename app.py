import streamlit as st
import pandas as pd
from datetime import datetime
import random

st.set_page_config(page_title="실시간 강의 대시보드", layout="wide")

# --- 0. 참가자용 랜덤 닉네임 자동 생성 (오류 수정 부분) ---
# 단어 목록을 if문 밖으로 꺼내서 제출 버튼을 눌러도 항상 기억하도록 수정했습니다.
adjectives = ["행복한", "즐거운", "용감한", "똑똑한", "호기심많은", "신나는", "귀여운", "멋진", "열정적인", "지혜로운"]
nouns = ["토끼", "강아지", "고양이", "다람쥐", "펭귄", "병아리", "호랑이", "사자", "쿼카", "돌고래", "부엉이"]

if "my_random_name" not in st.session_state:
    st.session_state["my_random_name"] = f"{random.choice(adjectives)} {random.choice(nouns)}"

# --- 1. 서버 공유 메모리 ---
@st.cache_resource
def get_shared_state():
    return {
        "records": [],
        "material_title": "1차시: 교육과정 재구성의 이해",
        "video_or_slide_url": "",
        "prompt_template": "", 
        "uploaded_file_bytes": None,
        "uploaded_file_name": None,
        "uploaded_file_type": None,
        "winner": None  
    }

state = get_shared_state()
shared_records = state["records"]

# 구글 슬라이드 주소 변환 함수
def get_embed_url(url):
    if not url: return ""
    url = url.strip()
    
    if "docs.google.com/presentation" in url:
        if "/pub" in url:
            return url.replace("/pub", "/embed")
        elif "/edit" in url: 
            return url.split("/edit")[0] + "/preview"
        elif "/preview" not in url and "/embed" not in url:
            return url.rstrip('/') + "/preview"
        return url
        
    elif "youtube.com/watch?v=" in url:
        video_id = url.split("v=")[1].split("&")[0]
        return f"https://www.youtube.com/embed/{video_id}"
    elif "youtu.be/" in url:
        video_id = url.split("youtu.be/")[1].split("?")[0]
        return f"https://www.youtube.com/embed/{video_id}"
        
    return url

# --- 2. 사이드바: 강사 전용 메뉴 ---
with st.sidebar:
    st.header("🔒 강사 전용 메뉴")
    admin_pw = st.text_input("강사 비밀번호", type="password", placeholder="기본값: 1234")
    
    if admin_pw == "1234":
        st.subheader("📝 강의 PPT 및 자료 설정")
        new_title = st.text_input("강의 제목", value=state["material_title"])
        st.info("※ 구글 프레젠테이션 주소창의 링크를 그대로 넣으시면 자동 변환됩니다.")
        new_url = st.text_input("PPT 웹 게시 주소 또는 유튜브 링크", value=state["video_or_slide_url"])
        
        # 프롬프트 입력칸
        new_prompt = st.text_area("복사용 프롬프트 (비워두면 화면에서 숨김)", value=state["prompt_template"], height=120)
        
        new_file = st.file_uploader("📎 공유할 파일 첨부 (선택)", type=None)
        
        if st.button("🚀 참가자 화면에 즉시 반영", type="primary", use_container_width=True):
            state["material_title"] = new_title
            state["video_or_slide_url"] = new_url
            state["prompt_template"] = new_prompt.strip()
            if new_file is not None:
                state["uploaded_file_bytes"] = new_file.getvalue()
                state["uploaded_file_name"] = new_file.name
                state["uploaded_file_type"] = new_file.type
            st.success("참가자 화면에 반영되었습니다!")
            st.rerun()

        st.divider()
        st.subheader("🎲 참가자 랜덤 뽑기")
        if st.button("🎁 발표자 무작위 추첨", use_container_width=True):
            if shared_records:
                names = list(set([r["이름"] for r in shared_records]))
                state["winner"] = random.choice(names)
                st.rerun()
            else:
                st.warning("아직 제출한 참가자가 없습니다.")
                
        if state["winner"]:
            if st.button("당첨자 초기화", use_container_width=True):
                state["winner"] = None
                st.rerun()

        st.divider()
        st.subheader("📊 실시간 피드백 요약")
        if shared_records:
            df_export = pd.DataFrame(shared_records)
            
            avg_rating = df_export["점수"].astype(int).mean()
            st.metric("전체 평균 이해도", f"{avg_rating:.1f} / 5.0 점")
            
            summary_text = "\n".join([f"[{r['이름']}] {r['핵심 요약 및 Q&A']}" for r in shared_records])
            st.text_area("제출된 내용 한눈에 보기", value=summary_text, height=150)

            csv_data = df_export.to_csv(index=False).encode("utf-8-sig")
            st.download_button(
                label="📥 전체 기록 CSV 다운로드",
                data=csv_data,
                file_name=f"강의피드백_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
                use_container_width=True
            )
            if st.button("🗑️ 전체 기록 초기화", use_container_width=True):
                shared_records.clear()
                state["winner"] = None
                st.rerun()

# --- 3. 메인 화면 타이틀 및 랜덤 뽑기 결과 ---
st.title("🚀 실시간 강의 대시보드")

if state["winner"]:
    st.success(f"🎉 **축하합니다! 오늘의 발표자(이벤트 당첨자)는 [{state['winner']}] 님입니다!** 🎉")
    st.balloons()

# --- 4. 강사 제공 자료(PPT) 카드 ---
with st.container(border=True):
    st.markdown(f"### 📌 [진행 중인 강의] {state['material_title']}")
    
    if state["video_or_slide_url"]:
        embed_link = get_embed_url(state["video_or_slide_url"])
        st.components.v1.iframe(embed_link, height=550, scrolling=True)
    
    if state["prompt_template"]:
        st.markdown("---")
        st.markdown("**📋 실습용 프롬프트 (우측 상단 복사 아이콘 클릭)**")
        st.code(state["prompt_template"], language="markdown")
        
    if state["uploaded_file_bytes"] is not None:
        st.markdown("---")
        st.download_button(
            label=f"📥 강의 보조 자료 다운로드 ({state['uploaded_file_name']})",
            data=state["uploaded_file_bytes"],
            file_name=state["uploaded_file_name"],
            mime=state["uploaded_file_type"] or "application/octet-stream",
            type="primary"
        )

st.divider()

# --- 5. 참가자 실시간 피드백 입력 폼 ---
rating_options = {
    "😭 너무 어려워요": 1,
    "🤔 아리송해요": 2,
    "🙂 보통이에요": 3,
    "😊 이해했어요": 4,
    "🤩 완벽히 이해했어요!": 5
}

with st.form("feedback_form", clear_on_submit=True):
    st.subheader("✍️ 실시간 피드백 제출")
    c1, c2 = st.columns([1, 2])
    with c1:
        # 참가자가 랜덤 닉네임을 지우고 자신의 실명을 기록할 수도 있습니다.
        user_name = st.text_input("이름 (자동 닉네임 수정 가능) 🏷️", value=st.session_state["my_random_name"])
    with c2:
        selected_rating_label = st.select_slider(
            "오늘 수업 내용, 얼마나 이해하셨나요? 🌡️", 
            options=list(rating_options.keys()),
            value="😊 이해했어요"
        )
        
    user_feedback = st.text_area(
        "수업의 핵심 요약이나 궁금한 질문(Q&A)을 자유롭게 남겨주세요. 💬", 
        height=100,
        placeholder="질문이 있거나 요약할 내용을 이곳에 작성해 주세요..."
    )
    
    submitted = st.form_submit_button("✅ 피드백 날리기", use_container_width=True)
    
    if submitted:
        if user_name.strip() and user_feedback.strip():
            shared_records.append({
                "제출시간": datetime.now().strftime("%H:%M:%S"),
                "이름": user_name.strip(), # 여기에 입력된 이름이 최종 기록됩니다.
                "이해도": selected_rating_label.split(" ")[0], 
                "점수": rating_options[selected_rating_label], 
                "핵심 요약 및 Q&A": user_feedback.strip()
            })
            # 제출 성공 시 다음 번을 위해 랜덤 닉네임을 새로 갱신합니다.
            st.session_state["my_random_name"] = f"{random.choice(adjectives)} {random.choice(nouns)}"
            st.toast("피드백이 성공적으로 전달되었습니다!", icon="💌")
            st.rerun()
        else:
            st.warning("이름과 내용을 모두 입력해 주세요.")

st.divider()

# --- 6. 실시간 피드백 공유 현황판 ---
col_title, col_refresh = st.columns([4, 1])
with col_title:
    st.subheader(f"💬 전체 참가자 현황 ({len(shared_records)}건)")
with col_refresh:
    if st.button("🔄 최신글 새로고침", use_container_width=True):
        st.rerun()

if shared_records:
    df_display = pd.DataFrame(shared_records).iloc[::-1]
    df_display = df_display.drop(columns=["점수"])
    
    st.dataframe(df_display, use_container_width=True, hide_index=True)
else:
    st.info("아직 제출된 피드백이 없습니다. 첫 번째 피드백의 주인공이 되어주세요!")
