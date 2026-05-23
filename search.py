import streamlit as st
import mysql.connector

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

# --- 사이드바 암호 기반 관리자 인증 ---
st.sidebar.title("관리자 인증")
admin_password = st.sidebar.text_input("주차팀 비밀번호 입력", type="password")

# 임시 비밀번호를 '0000'로 설정
is_admin = (admin_password == "0000")

if admin_password and is_admin:
    st.sidebar.success("🔒 관리자 권한이 승인되었습니다. 연락처가 노출됩니다.")
elif admin_password and not is_admin:
    st.sidebar.error("❌ 비밀번호가 틀렸습니다.")

# --- 메인 화면 ---
st.title("교회 주차 관리 - 차량 조회 🔍")
st.write("이중 주차 시 차량 번호 뒤 4자리를 검색해 주세요.")

search_query = st.text_input("차량 번호 4자리 입력", max_chars=4, placeholder="예: 1234")

if st.button("검색"):
    if len(search_query) == 4:
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
                st.success(f"{len(results)}대의 차량이 검색되었습니다.")
                for row in results:
                    with st.container():
                        st.subheader(f"차량: {row['plate_number']}")
                        st.write(f"**차주:** {row['name']} 성도님")
                        st.write(f"**소속:** {row['department']}")
                        
                        # 💡 버튼 대신 안내 문구로 대체
                        if is_admin:
                            formatted_phone = format_phone(row['phone_number'])
                            st.error(f"**연락처:** {formatted_phone}")
                        else:
                            st.write("**연락처:** 개인정보 보호됨")
                            st.warning("관리자 권한이 필요합니다.")
                            
                        st.divider()
            else:
                st.warning("등록되지 않은 차량입니다.")
                
        except Exception as e:
            st.error(f"조회 중 오류가 발생했습니다: {e}")
        finally:
            if 'conn' in locals() and conn.is_connected():
                cursor.close()
                conn.close()
    else:
        st.error("숫자 4자리를 정확히 입력해 주세요.")