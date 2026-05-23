import streamlit as st
import mysql.connector
import re # 정규표현식 라이브러리 (숫자만 추출할 때 사용)

def init_connection():
    return mysql.connector.connect(
        host=st.secrets["mysql"]["host"],
        port=st.secrets["mysql"]["port"],
        database=st.secrets["mysql"]["database"],
        user=st.secrets["mysql"]["user"],
        password=st.secrets["mysql"]["password"]
    )

st.title("교회 주차 관리 - 차량 등록 📝")

with st.form("register_form", clear_on_submit=True):
    new_name = st.text_input("이름 (필수)", placeholder="예: 홍길동")
    # 전화번호 힌트를 수정했습니다.
    new_phone = st.text_input("전화번호 (필수)", placeholder="숫자만 입력해 주세요 (예: 01012345678)")
    
    new_dept = st.text_input("소속 부서", placeholder="예: 남성 2교구")
    new_plate = st.text_input("차량 번호 (전체 입력)", placeholder="예: 12가3456")
    
    submit_button = st.form_submit_button("등록 완료")

if submit_button:
    if not new_name or not new_phone or not new_plate:
        st.error("이름, 전화번호, 차량 번호는 필수 입력 항목입니다.")
    else:
        # 입력된 전화번호에서 숫자(0-9)만 추출하여 저장합니다.
        cleaned_phone = re.sub(r'[^0-9]', '', new_phone)
        
        try:
            conn = init_connection()
            cursor = conn.cursor()
            
            insert_member_sql = """
                INSERT INTO members (name, phone_number, department, is_admin) 
                VALUES (%s, %s, %s, FALSE)
            """
            # 정제된 전화번호(cleaned_phone)를 DB에 넘깁니다.
            cursor.execute(insert_member_sql, (new_name, cleaned_phone, new_dept))
            new_member_id = cursor.lastrowid
            
            insert_vehicle_sql = """
                INSERT INTO vehicles (member_id, plate_number) 
                VALUES (%s, %s)
            """
            cursor.execute(insert_vehicle_sql, (new_member_id, new_plate))
            
            conn.commit()
            st.success(f"🎉 {new_name} 성도님의 차량({new_plate})이 성공적으로 등록되었습니다!")
            
        except mysql.connector.IntegrityError:
            st.error("이미 등록되어 있는 차량 번호입니다.")
        except Exception as e:
            st.error(f"등록 중 오류가 발생했습니다: {e}")
            if 'conn' in locals() and conn.is_connected():
                conn.rollback()
        finally:
            if 'conn' in locals() and conn.is_connected():
                cursor.close()
                conn.close()