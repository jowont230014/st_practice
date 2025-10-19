import streamlit as st
import folium
import geopy
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim

st.title("🗺️ 나만의 위치 북마크 지도")

st.write("아래에 장소 정보를 입력하고 지도에 표시해보세요!")

# 장소 입력
place = st.text_input("장소 이름", value="서울 시청")

# 지오코딩 설정
geolocator = Nominatim(user_agent="my_geo_app")

# 세션 상태 저장
if "places" not in st.session_state:
    st.session_state.places = []

# 버튼 클릭 시 장소 좌표 변환
if st.button("지도에 추가하기"):
    try:
        location = geolocator.geocode(place)
        if location:
            lat, lon = location.latitude, location.longitude
            st.session_state.places.append((place, lat, lon))
            st.success(f"{place} 추가 완료! (위도: {lat:.4f}, 경도: {lon:.4f})")
        else:
            st.warning("장소를 찾을 수 없습니다. 정확한 이름을 입력해주세요.")
    except Exception as e:
        st.error(f"지오코딩 중 오류 발생: {e}")

# 지도 생성
if st.session_state.places:
    # 마지막으로 추가한 위치를 중심으로
    last_lat, last_lon = st.session_state.places[-1][1], st.session_state.places[-1][2]
    m = folium.Map(location=[last_lat, last_lon], zoom_start=12)
else:
    # 기본 지도 위치: 서울
    m = folium.Map(location=[37.5665, 126.9780], zoom_start=6)

# 마커 추가
for name, lat, lon in st.session_state.places:
    folium.Marker([lat, lon], tooltip=name).add_to(m)

# 지도 표시
st_folium(m, width=700, height=500)
