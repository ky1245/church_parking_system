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

st.title("교회 주차 관리 - 관리자 전용 페이지 🛠️")

# --- 로그인 인증 ---
current_pw = "0000"
password_input = st.text_input("주차팀 비밀번호를 입력하세요", type="password")

if password_input == current_pw:
    st.success("🔒 관리자 인증 성공! 데이터를 수정하거나 삭제할 수 있습니다.")
    
    # 기능 선택 (수정 또는 삭제)
    menu = st.radio("원하는 작업을 선택하세요", ["정보 수정", "데이터 삭제"])
    
    # 데이터 조회를 위해 DB 연결
    conn = init_connection()
    cursor = conn.cursor(dictionary=True)

    # 전체 성도 및 차량 목록 가져오기
    sql = """
        SELECT m.id AS member_id, m.name, m.department, m.phone_number, v.id AS vehicle_id, v.plate_number 
        FROM members m
        LEFT JOIN vehicles v ON m.id = v.member_id
    """
    cursor.execute(sql)
    all_data = cursor.fetchall()
    
    st.divider() # 화면 구분선
    
    # 💡 1. 검색어 입력창 만들기
    search_keyword = st.text_input("🔍 이름 또는 차량번호로 검색하세요", placeholder="예: 홍길동 또는 1234")
    
    # 💡 2. 검색어에 맞춰 데이터 걸러내기 (필터링)
    filtered_data = []
    for row in all_data:
        name = row['name'] if row['name'] else ""
        plate = row['plate_number'] if row['plate_number'] else ""
        
        # 검색어가 비어있거나, 이름/차량번호에 검색어가 포함되어 있으면 목록에 추가
        if not search_keyword or search_keyword in name or search_keyword in plate:
            filtered_data.append(row)

    # 💡 3. 걸러진 데이터가 없을 때의 처리
    if not filtered_data:
        st.warning("일치하는 성도나 차량이 없습니다.")
    else:
        # 걸러진 데이터로 선택창 목록 만들기
        member_options = {f"{row['name']} ({row['department']}) - {row['plate_number'] if row['plate_number'] else '차량없음'}": row for row in filtered_data}
        
        if menu == "정보 수정":
            st.subheader("✏️ 성도 및 차량 정보 수정")
            selected_member_str = st.selectbox("수정할 성도를 선택하세요", list(member_options.keys()))
            
            if selected_member_str:
                selected_data = member_options[selected_member_str]
                
                # 기존 정보 입력창에 띄워주기
                new_name = st.text_input("이름", value=selected_data['name'])
                new_dept = st.text_input("소속 부서", value=selected_data['department'])
                new_phone = st.text_input("전화번호", value=selected_data['phone_number'])
                new_plate = st.text_input("차량 번호", value=selected_data['plate_number'] if selected_data['plate_number'] else "")
                
                if st.button("수정 내용 저장하기"):
                    try:
                        # 1. 성도 정보 수정
                        cursor.execute("""
                            UPDATE members 
                            SET name = %s, department = %s, phone_number = %s 
                            WHERE id = %s
                        """, (new_name, new_dept, new_phone, selected_data['member_id']))
                        
                        # 2. 차량 정보 수정
                        if selected_data['vehicle_id']:
                            cursor.execute("""
                                UPDATE vehicles SET plate_number = %s WHERE id = %s
                            """, (new_plate, selected_data['vehicle_id']))
                        elif new_plate: # 기존엔 차량이 없었는데 새로 입력한 경우
                            cursor.execute("""
                                INSERT INTO vehicles (member_id, plate_number) VALUES (%s, %s)
                            """, (selected_data['member_id'], new_plate))
                            
                        conn.commit()
                        st.success("🎉 정보가 성공적으로 수정되었습니다! 페이지를 새로고침(F5) 해주세요.")
                    except Exception as e:
                        st.error(f"수정 중 오류 발생: {e}")
                        
        elif menu == "데이터 삭제":
            st.subheader("❌ 데이터 삭제 (성도 탈퇴 및 차량 번호 삭제)")
            selected_member_str = st.selectbox("삭제할 성도를 선택하세요", list(member_options.keys()))
            
            if selected_member_str:
                selected_data = member_options[selected_member_str]
                st.warning(f"⚠️ [{selected_data['name']}] 성도님의 모든 정보와 차량({selected_data['plate_number']}) 정보가 영구 삭제됩니다.")
                
                if st.button("정말 삭제하겠습니다"):
                    try:
                        cursor.execute("DELETE FROM members WHERE id = %s", (selected_data['member_id'],))
                        conn.commit()
                        st.success("삭제가 완료되었습니다. 페이지를 새로고침 해주세요.")
                    except Exception as e:
                        st.error(f"삭제 중 오류 발생: {e}")
                        
    cursor.close()
    conn.close()

elif password_input:
    st.error("❌ 비밀번호가 틀렸습니다.")
