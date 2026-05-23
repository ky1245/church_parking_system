import streamlit as st
import mysql.connector

# 💡 [디자인 1] 화면을 넓게 쓰고 브라우저 탭 꾸미기
st.set_page_config(
    page_title="교회 주차 관리 시스템 - 조회",
    page_icon="🚗",
    layout="wide"
)

def init_connection():
    return mysql.connector.connect(
        host=st.secrets["mysql"]["host"],
        port=st.secrets["mysql"]["port"],
        database=st.secrets["mysql"]["database"],
        user=st.secrets["mysql"]["user"],
        password=st.secrets["mysql"]["password"]
    )

def format_phone(phone_str):
    if len(phone_str) == 11:
        return f"{phone_str[:3]}-{phone_str[3:7]}-{phone_str[7:]}"
    elif len(phone_str) == 10:
        return f"{phone_str[:3]}-{phone_str[3:6]}-{phone_str[6:]}"
    return phone_str

# --- 메인 타이틀 ---
st.title("🚗 교회 주차 차량 검색 시스템")
st.markdown(" 차량 조회 페이지입니다.")
st.divider()

# --- 🔐 [흐름 변경] 메인 화면에서 관리자 인증하기 ---
# 화면을 2칸으로 나누어 비밀번호 입력창을 슬림하게 만듭니다.
auth_col1, auth_col2 = st.columns([1, 2])

with auth_col1:
    admin_password = st.text_input("🔑 주차팀 비밀번호를 입력하세요", type="password", placeholder="비밀번호 4자리")

# 비밀번호가 '0000'인지 확인
is_admin = (admin_password == "0000")

if admin_password:
    if is_admin:
        st.success("🔒 관리자 권한이 승인되었습니다.")
    else:
        st.error("❌ 비밀번호가 틀렸습니다. 일반 모드로 조회됩니다. (연락처 확인 불가능)")
else:
    st.info("💡 일반 모드로 동작 중입니다. (주차팀 비밀번호 입력 시 연락처 확인 가능)")

st.divider()

# --- 🔍 차량 검색 영역 ---
st.subheader("🔎 차량 번호 검색")
search_query = st.text_input("차량 번호 뒤 4자리를 입력하세요", placeholder="예: 1234", max_chars=4)

if search_query:
    if len(search_query) < 2:
        st.warning("⚠️ 최소 2자리 이상의 숫자를 입력해 주세요.")
    else:
        try:
            conn = init_connection()
            cursor = conn.cursor(dictionary=True)
            
            sql = """
                SELECT m.name, m.department, m.phone_number, v.plate_number 
                FROM vehicles v
                JOIN members m ON v.member_id = m.id
                WHERE v.plate_number LIKE %s
            """
            cursor.execute(sql, ('%' + search_query,))
            results = cursor.fetchall()
            
            if results:
                st.success(f"🎉 총 {len(results)}대의 차량이 검색되었습니다.")
                
                # 💡 [디자인 2] 검색 결과를 카드 모양 테두리 상자로 예쁘게 배치
                for row in results:
                    with st.container(border=True): # 얇은 테두리 상자 생성
                        
                        # 대시보드 스타일로 정보 배치
                        col_plate, col_name, col_dept, col_phone = st.columns(4)
                        
                        with col_plate:
                            st.markdown(f"#### 🚘 차량 번호\n### `{row['plate_number']}`")
                        
                        with col_name:
                            st.markdown(f"#### 👤 차주 성도\n### {row['name']}")
                            
                        with col_dept:
                            st.markdown(f"#### ⛪ 소속 부서\n### {row['department']}")
                            
                        with col_phone:
                            st.markdown("#### 📱 연락처")
                            if is_admin:
                                formatted_phone = format_phone(row['phone_number'])
                                # 관리자일 때는 강조된 초록색 박스로 표시
                                st.info(f"**{formatted_phone}**")
                            else:
                                # 일반 모드일 때는 마스킹 처리
                                st.text("🔒 개인정보 보호됨")
                                
            else:
                st.error("😭 등록되지 않은 차량입니다.")
                
        except Exception as e:
            st.error(f"❌ 조회 중 오류가 발생했습니다: {e}")
        finally:
            if 'conn' in locals() and conn.is_connected():
                cursor.close()
                conn.close()
