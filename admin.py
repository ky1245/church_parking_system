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
    st.success("🔒 관리자 인증 성공! 데이터를 관리할 수 있습니다.")
    
    # 💡 [흐름 1] 이름 또는 차량번호 검색창이 맨 처음에 나옴
    search_keyword = st.text_input("🔍 1. 이름 또는 차량번호로 검색하세요", placeholder="예: 홍길동 또는 1234")
    
    # 💡 [흐름 2] 작업 선택 (정보 수정 또는 데이터 삭제)
    menu = st.radio("📂 2. 원하는 작업을 선택하세요", ["정보 수정", "데이터 삭제"])
    
    # DB에서 전체 데이터 가져오기
    conn = init_connection()
    cursor = conn.cursor(dictionary=True)
    
    sql = """
        SELECT m.id AS member_id, m.name, m.department, m.phone_number, v.id AS vehicle_id, v.plate_number 
        FROM members m
        LEFT JOIN vehicles v ON m.id = v.member_id
    """
    cursor.execute(sql)
    all_data = cursor.fetchall()
    
    # 검색어에 맞춰 데이터 필터링(걸러내기)
    filtered_data = []
    for row in all_data:
        name = row['name'] if row['name'] else ""
        plate = row['plate_number'] if row['plate_number'] else ""
        if not search_keyword or search_keyword in name or search_keyword in plate:
            filtered_data.append(row)
            
    st.divider() # 화면 구분선
    
    if not filtered_data:
        st.warning("일치하는 성도나 차량이 없습니다.")
    else:
        # 걸러진 데이터로 딕셔너리 만들기
        member_options = {
            f"{row['name']} ({row['department']}) - {row['plate_number'] if row['plate_number'] else '차량없음'}": row 
            for row in filtered_data
        }
        
        # 💡 [흐름 3] 선택창 목록 맨 앞에 '선택해주세요' 추가하기
        selectbox_options = ["🔽 선택해주세요"] + list(member_options.keys())
        
        selected_member_str = st.selectbox("👥 3. 대상을 선택하세요", selectbox_options)
        
        # 💡 사용자가 진짜 성도를 선택했을 때만 아래 수정/삭제 입력창이 나타남
        if selected_member_str and selected_member_str != "🔽 선택해주세요":
            selected_data = member_options[selected_member_str]
            
            # --- [작업 1] 정보 수정 모드 ---
            if menu == "정보 수정":
                st.subheader(f"✏️ [{selected_data['name']}] 성도 정보 수정")
                
                new_name = st.text_input("이름", value=selected_data['name'])
                new_dept = st.text_input("소속 부서", value=selected_data['department'])
                new_phone = st.text_input("전화번호", value=selected_data['phone_number'])
                new_plate = st.text_input("차량 번호", value=selected_data['plate_number'] if selected_data['plate_number'] else "")
                
                if st.button("수정 내용 저장하기"):
                    try:
                        # 1. 성도 테이블 업데이트
                        cursor.execute("""
                            UPDATE members 
                            SET name = %s, department = %s, phone_number = %s 
                            WHERE id = %s
                        """, (new_name, new_dept, new_phone, selected_data['member_id']))
                        
                        # 2. 차량 테이블 업데이트
                        if selected_data['vehicle_id']:
                            cursor.execute("""
                                UPDATE vehicles SET plate_number = %s WHERE id = %s
                            """, (new_plate, selected_data['vehicle_id']))
                        elif new_plate: # 기존엔 차량이 없었는데 새로 입력한 경우
                            cursor.execute("""
                                INSERT INTO vehicles (member_id, plate_number) VALUES (%s, %s)
                            """, (selected_data['member_id'], new_plate))
                            
                        conn.commit()
                        st.success("🎉 정보가 성공적으로 수정되었습니다! 페이지가 곧 새로고침됩니다.")
                        st.rerun() # 화면 즉시 새로고침
                    except Exception as e:
                        st.error(f"수정 중 오류 발생: {e}")
            
            # --- [작업 2] 데이터 삭제 모드 ---
            elif menu == "데이터 삭제":
                st.subheader(f"❌ [{selected_data['name']}] 성도 데이터 삭제")
                st.error(f"⚠️ 경고: [{selected_data['name']}] 성도님의 인적 사항과 차량 번호({selected_data['plate_number']})가 시스템에서 완전히 삭제됩니다.")
                
                if st.button("🚨 정말로 삭제하겠습니다"):
                    try:
                        cursor.execute("DELETE FROM members WHERE id = %s", (selected_data['member_id'],))
                        conn.commit()
                        st.success("삭제가 완료되었습니다.")
                        st.rerun() # 화면 즉시 새로고침
                    except Exception as e:
                        st.error(f"삭제 중 오류 발생: {e}")
                        
        else:
            # 아무것도 선택하지 않았을 때 보여줄 안내 문구
            st.info("💡 위의 3번 선택창에서 관리할 대상을 선택하시면 수정/삭제 화면이 나타납니다.")
            
    cursor.close()
    conn.close()

elif password_input:
    st.error("❌ 비밀번호가 틀렸습니다.")
