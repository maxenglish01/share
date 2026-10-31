import streamlit as st
import pandas as pd
from datetime import datetime
import random

# --- 1. 초기 화면 사이드바 접힘(collapsed) 및 CSS 설정 ---
st.set_page_config(
    page_title="실시간 강의 대시보드", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 데이터프레임(피드백 현황판) 우측 상단 툴바(다운로드 버튼 등) 숨김 CSS
# 참가자가 메인 화면에서 다른 사람들의 제출 기록을 임의로 다운로드하지 못하게 완벽히 차단합니다.
st.markdown(
    """
    <style>
    div[data-testid="stElementContainer"]:has([data-testid="stDataFrame"]) [data-testid="stElementToolbar"] {
        display: none !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --- 0. 참가자용 랜덤 닉네임 자동 생성 ---
adjectives = ["행복한", "즐거운", "용감한", "똑똑한", "호기심많은", "신나는", "귀여운", "멋진", "열정적인", "지혜로운"]
nouns = ["토끼", "강아지", "고양이", "다람쥐", "펭귄", "병아리", "호랑이", "사자", "쿼카", "돌고래", "부엉이"]

if "my_random_name" not in st.session_state:
    st.session_state["my_random_name"] = f"{random.choice(adjectives)} {random.choice(nouns)}"

if "uploader_key" not in st.session_state:
    st.session_state["uploader_key"] = str(random.random())

# 당첨자 풍선 효과 무한 반복 방지용
if "last_winner" not in st.session_state:
    st.session_state["last_winner"] = None

# --- 2. 서버 공유 메모리 ---
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

def get_embed_url(url):
    if not url: return ""
    url = url.strip()
    if "docs.google.com/presentation" in url:
        if "/pub" in url: return url.replace("/pub", "/embed")
        elif "/edit" in url: return url.split("/edit")[0] + "/preview"
        elif "/preview" not in url and "/embed" not in url: return url.rstrip('/') + "/preview"
        return url
    elif "youtube.com/watch?v=" in url:
        video_id = url.split("v=")[1].split("&")[0]
        return f"https://www.youtube.com/embed/{video_id}"
    elif "youtu.be/" in url:
        video_id = url.split("youtu.be/")[1].split("?")[0]
        return f"https://www.youtube.com/embed/{video_id}"
    return url

# --- 3. 사이드바: 강사 전용 메뉴 ---
with st.sidebar:
    with st.expander("🔒 강사 전용 메뉴 (클릭하여 열기)", expanded=False):
        admin_pw = st.text_input("강사 비밀번호", type="password", placeholder="기본값: 1234", key="admin_pw")
        
        if admin_pw == "rlaxornr":
            st.subheader("📝 강의 PPT 및 자료 설정")
            new_title = st.text_input("강의 제목", value=state["material_title"])
            st.info("※ 구글 프레젠테이션 주소창의 링크를 그대로 넣으시면 자동 변환됩니다.")
            new_url = st.text_input("PPT 웹 게시 주소 또는 유튜브 링크", value=state["video_or_slide_url"])
            
            new_prompt = st.text_area("복사용 프롬프트 (비워두면 화면에서 숨김)", value=state["prompt_template"], height=120)
            
            new_file = st.file_uploader("📎 공유할 파일 첨부", type=None, key=st.session_state["uploader_key"])
            
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

            if state["uploaded_file_name"] is not None:
                st.divider()
                st.caption(f"📁 현재 참가자에게 공유 중인 파일: **{state['uploaded_file_name']}**")
                if st.button("🗑️ 현재 첨부 파일 지우기", use_container_width=True):
                    state["uploaded_file_bytes"] = None
                    state["uploaded_file_name"] = None
                    state["uploaded_file_type"] = None
                    st.session_state["uploader_key"] = str(random.random()) 
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
                    st.session_state["last_winner"] = None
                    st.rerun()

            # ----- (핵심) 강사만 접근할 수 있는 참가자 '제출 자료' 다운로드 구역 -----
            st.divider()
            st.subheader("📊 제출된 피드백 자료 관리")
            if shared_records:
                df_export = pd.DataFrame(shared_records)
                avg_rating = df_export["점수"].astype(int).mean()
                st.metric("전체 평균 이해도", f"{avg_rating:.1f} / 5.0 점")
                
                summary_text = "\n".join([f"[{r['이름']}] {r['핵심 요약 및 Q&A']}" for r in shared_records])
                st.text_area("제출된 내용 한눈에 보기", value=summary_text, height=150)

                csv_data = df_export.to_csv(index=False).encode("utf-8-sig")
                st.download_button(
                    label="📥 제출된 전체 피드백 다운로드 (CSV)",
                    data=csv_data,
                    file_name=f"강의피드백_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv",
                    use_container_width=True,
                    type="primary"
                )
                if st.button("🗑️ 전체 기록 초기화", use_container_width=True):
                    shared_records.clear()
                    state["winner"] = None
                    st.session_state["last_winner"] = None
                    st.rerun()

# --- 4. 메인 화면 타이틀 ---
st.title("🚀 실시간 강의 대시보드")

# --- 5. 당첨자 발표 및 강사 제공 자료 카드 (3초마다 자동 갱신되는 프래그먼트) ---
@st.fragment(run_every=4)
def render_live_materials():
    # 당첨자 발표
    if state["winner"]:
        st.success(f"🎉 **축하합니다! 오늘의 발표자(이벤트 당첨자)는 [{state['winner']}] 님입니다!** 🎉")
        if st.session_state["last_winner"] != state["winner"]:
            st.balloons()
            st.session_state["last_winner"] = state["winner"]

    # 진행 중인 강의 카드
    with st.container(border=True):
        st.markdown(f"### 📌 [진행 중인 강의] {state['material_title']}")
        
        if state["video_or_slide_url"]:
            embed_link = get_embed_url(state["video_or_slide_url"])
            st.components.v1.iframe(embed_link, height=550, scrolling=True)
        
        if state["prompt_template"]:
            st.markdown("---")
            st.markdown("**📋 실습용 자료 (우측 상단 복사 아이콘 클릭)**")
            st.code(state["prompt_template"], language="markdown")
            
        if state["uploaded_file_bytes"] is not None:
            st.markdown("---")
            if state["uploaded_file_type"] and state["uploaded_file_type"].startswith("image"):
                img_col1, img_col2, img_col3 = st.columns([1, 2, 1])
                with img_col2:
                    st.image(state["uploaded_file_bytes"], use_container_width=True, caption=state['uploaded_file_name'])
            
            # 강의 보조 자료(첨부파일)는 참가자에게 배포하는 것이 목적이므로 모두가 다운로드할 수 있도록 원복했습니다.
            st.download_button(
                label=f"📥 강의 보조 자료 다운로드 ({state['uploaded_file_name']})",
                data=state["uploaded_file_bytes"],
                file_name=state["uploaded_file_name"],
                mime=state["uploaded_file_type"] or "application/octet-stream",
                type="primary",
                use_container_width=True
            )

# 프래그먼트 실행
render_live_materials()

st.divider()

# --- 6. 참가자 실시간 피드백 입력 폼 ---
rating_options = {
    "⭐ (어려워요)": 1,
    "⭐⭐ (헷갈려요)": 2,
    "⭐⭐⭐ (보통이에요)": 3,
    "⭐⭐⭐⭐ (이해했어요)": 4,
    "⭐⭐⭐⭐⭐ (완벽해요!)": 5
}

with st.form("feedback_form", clear_on_submit=True):
    st.subheader("✍️ 실시간 피드백 제출")
    c1, c2 = st.columns([1, 2])
    with c1:
        user_name = st.text_input("이름 (자동 닉네임 수정 가능) 🏷️", value=st.session_state["my_random_name"])
    with c2:
        selected_rating_label = st.select_slider(
            "오늘 수업 내용, 얼마나 이해하셨나요? (별점)", 
            options=list(rating_options.keys()),
            value="⭐⭐⭐⭐⭐ (완벽해요!)"
        )
        
    user_feedback = st.text_area(
        "수업의 핵심 요약이나 궁금한 질문(Q&A)을 자유롭게 남겨주세요. 💬", 
        height=100,
        placeholder="질문이 있거나 요약할 내용을 이곳에 작성해 주세요..."
    )
    
    submitted = st.form_submit_button("✅ 피드백 날리기", use_container_width=True)
    
    if submitted:
        if user_name.strip() and user_feedback.strip():
            score = rating_options[selected_rating_label]
            star_string = "⭐" * score
            
            shared_records.append({
                "제출시간": datetime.now().strftime("%H:%M:%S"),
                "이름": user_name.strip(), 
                "이해도": star_string,
                "점수": score, 
                "핵심 요약 및 Q&A": user_feedback.strip()
            })
            st.session_state["my_random_name"] = f"{random.choice(adjectives)} {random.choice(nouns)}"
            st.toast("피드백이 성공적으로 전달되었습니다!", icon="💌")
            st.rerun()
        else:
            st.warning("이름과 내용을 모두 입력해 주세요.")

st.divider()

# --- 7. 실시간 피드백 공유 현황판 ---
@st.fragment(run_every=3)
def render_live_board():
    col_title, col_refresh = st.columns([4, 1])
    with col_title:
        st.subheader(f"💬 전체 참가자 현황 ({len(shared_records)}건)")
    with col_refresh:
        if st.button("🔄 즉시 동기화", use_container_width=True):
            st.rerun()

    if shared_records:
        df_display = pd.DataFrame(shared_records).iloc[::-1]
        df_display = df_display.drop(columns=["점수"])
        # CSS를 통해 데이터프레임 툴바(다운로드 기능)가 가려져서 출력됩니다.
        st.dataframe(df_display.head(20), use_container_width=True, hide_index=True)
    else:
        st.info("아직 제출된 피드백이 없습니다. 첫 번째 피드백의 주인공이 되어주세요!")

# 현황판 프래그먼트 실행
render_live_board()
