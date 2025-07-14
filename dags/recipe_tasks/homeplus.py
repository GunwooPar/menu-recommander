import requests
import json
import re

def extract_main_ingredient(item_name):
    # 1. 단위/수량/특수문자/불필요한 단어제거
    name = re.sub(r"[0-9]+[gkgmlL\\(\\)\\[\\]박스봉팩]+", "", item_name)  # 단위/수량 제거
    name = re.sub(r"[^가-힣a-zA-Z]", " ", name)  # 한글/영문 외 제거
    name = name.replace("햇", "").replace("국산", "").replace("수입", "")
    name = name.replace("특란", "계란").replace("왕란", "계란").replace("유정란", "계란")
    name = name.replace("냉동", "").replace("생", "").replace("신선", "")
    name = name.replace("정육", "").replace("특등급", "")
    name = name.strip()

    # 2. 키워드 매핑 (마트/레시피에서 자주 쓰는 재료)
    keyword_map = [
        ("마늘", "마늘"),
        ("감자", "감자"),
        ("고구마", "고구마"),
        ("양파", "양파"),
        ("파", "대파"),
        ("쪽파", "쪽파"),
        ("대파", "대파"),
        ("양배추", "양배추"),
        ("배추", "배추"),
        ("상추", "상추"),
        ("깻잎", "깻잎"),
        ("시금치", "시금치"),
        ("버섯", "버섯"),
        ("표고", "표고버섯"),
        ("팽이", "팽이버섯"),
        ("느타리", "느타리버섯"),
        ("토마토", "토마토"),
        ("오이", "오이"),
        ("호박", "호박"),
        ("애호박", "애호박"),
        ("가지", "가지"),
        ("당근", "당근"),
        ("브로콜리", "브로콜리"),
        ("계란", "계란"),
        ("달걀", "계란"),
        ("닭", "닭고기"),
        ("닭가슴살", "닭가슴살"),
        ("삼겹살", "돼지고기"),
        ("돼지", "돼지고기"),
        ("목살", "돼지고기"),
        ("소고기", "소고기"),
        ("우삼겹", "소고기"),
        ("차돌박이", "소고기"),
        ("오리", "오리고기"),
        ("연어", "연어"),
        ("고등어", "고등어"),
        ("꽁치", "꽁치"),
        ("참치", "참치"),
        ("명태", "명태"),
        ("오징어", "오징어"),
        ("주꾸미", "주꾸미"),
        ("문어", "문어"),
        ("두부", "두부"),
        ("김치", "김치"),
        ("김", "김"),
        ("멸치", "멸치"),
        ("새우", "새우"),
        ("조개", "조개"),
        ("홍합", "홍합"),
        ("미역", "미역"),
        ("다시마", "다시마"),
        ("콩나물", "콩나물"),
        ("숙주", "숙주나물"),
        ("두유", "두유"),
        ("치즈", "치즈"),
        ("우유", "우유"),
        ("버터", "버터"),
        ("베이컨", "베이컨"),
        ("햄", "햄"),
        ("베이비채소", "채소"),
        ("샐러드", "채소"),
        ("과일", "과일"),
        ("사과", "사과"),
        ("배", "배"),
        ("복숭아", "복숭아"),
        ("체리", "체리"),
        ("딸기", "딸기"),
        ("바나나", "바나나"),
        ("포도", "포도"),
        ("수박", "수박"),
        ("참외", "참외"),
        ("멜론", "멜론"),
        ("레몬", "레몬"),
        ("오렌지", "오렌지"),
        ("자몽", "자몽"),
        ("블루베리", "블루베리"),
        ("라임", "라임"),
        ("키위", "키위"),
        ("파프리카", "파프리카"),
        ("피망", "피망"),
        ("양상추", "양상추"),
        ("아보카도", "아보카도"),
        ("견과", "견과류"),
        ("호두", "호두"),
        ("아몬드", "아몬드"),
        ("땅콩", "땅콩"),
        ("잣", "잣"),
        ("캐슈넛", "캐슈넛"),
    ]
    for keyword, result in keyword_map:
        if keyword in name:
            return result

    # 3. 기본값: 가장 짧은 단어 반환
    tokens = name.split()
    if tokens:
        return tokens[-1]
    return item_name  # fallback

def get_latest_leaflet_no():
    url = "https://mfront.homeplus.co.kr/api/v1/leaflets?categoryId=25"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8",
        "Connection": "keep-alive",
        "Referer": "https://mfront.homeplus.co.kr/leaflet",
        "Origin": "https://mfront.homeplus.co.kr"
    }
    resp = requests.get(url, headers=headers)
    if resp.status_code == 200:
        try:
            data = resp.json()
            leaflet_list = data.get("data", {}).get("leafletList", [])
            if leaflet_list:
                return leaflet_list[0].get("leafletNo")
        except Exception as e:
            print(f"JSON 파싱 실패: {e}")
    return "244"  # 실패 시 fallback

def get_sale_items_from_homeplus():
    """홈플러스에서 할인 품목 크롤링 (JSON API 사용)"""
    print("홈플러스 JSON API 호출을 시작합니다.")
    latest_leaflet_no = get_latest_leaflet_no()
    api_url = f"https://mfront.homeplus.co.kr/leaf/item.json?categoryId=25&leafletNo={latest_leaflet_no}&limit=20&offset=0&sort=RANK"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Referer": "https://mfront.homeplus.co.kr/leaflet",
        "Origin": "https://mfront.homeplus.co.kr",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin"
    }
    try:
        session = requests.Session()
        main_page = "https://mfront.homeplus.co.kr/leaflet"
        session.get(main_page, headers=headers)
        response = session.get(api_url, headers=headers, timeout=10)
        response.raise_for_status()
        print(f"API 응답 상태 코드: {response.status_code}")
        print(f"API 응답 헤더: {response.headers.get('content-type', 'unknown')}")
        if 'text/html' in response.headers.get('content-type', ''):
            print("HTML 응답을 받았습니다. 다른 방법을 시도합니다.")
            alternative_urls = [
                "https://mfront.homeplus.co.kr/leaflet/item.json?categoryId=25&leafletNo=243&limit=20&offset=0&sort=RANK",
                "https://mfront.homeplus.co.kr/leaf/item.json?categoryId=25&leafletNo=243&limit=20&offset=0&sort=RANK",
                "https://mfront.homeplus.co.kr/api/leaflets/items?categoryId=25&leafletNo=243&limit=20&offset=0&sort=RANK"
            ]
            for alt_url in alternative_urls:
                print(f"대안 URL 시도: {alt_url}")
                try:
                    alt_response = session.get(alt_url, headers=headers, timeout=10)
                    if alt_response.status_code == 200 and 'application/json' in alt_response.headers.get('content-type', ''):
                        print("대안 URL 성공!")
                        response = alt_response
                        break
                except:
                    continue
            else:
                print("모든 대안 URL 실패. 기본 재료를 사용합니다.")
                return ["돼지고기"]
        data = response.json()
        print(f"파싱된 JSON 데이터 구조: {type(data)}")
        items = data.get('data', {}).get('dataList', [])
        if not items:
            print("API 응답에 상품 목록이 없습니다.")
            return ["돼지고기"]
        item_names = [item.get('itemNm') for item in items if item.get('itemNm')]
        if not item_names:
            print("상품 이름을 찾지 못했습니다.")
            return ["돼지고기"]
        print("--- 홈플러스 금주 할인 품목 ---")
        for i, name in enumerate(item_names[:5], 1):
            print(f"{i}. {name}")
        cooking_ingredients = []
        for item_name in item_names[:10]:
            ingredient = extract_main_ingredient(item_name)
            if ingredient and ingredient not in cooking_ingredients:
                cooking_ingredients.append(ingredient)
        print(f"요리 가능한 재료들: {cooking_ingredients}")
        return cooking_ingredients
    except requests.exceptions.RequestException as e:
        print(f"홈플러스 API 호출 중 오류 발생: {e}")
        return ["돼지고기"]
    except json.JSONDecodeError as e:
        print(f"JSON 파싱 중 오류 발생: {e}")
        return ["돼지고기"]
    except Exception as e:
        print(f"홈플러스 데이터 처리 중 오류 발생: {e}")
        return ["돼지고기"] 