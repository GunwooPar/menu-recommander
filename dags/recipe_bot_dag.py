from airflow.decorators import dag, task
import pendulum
import requests
from bs4 import BeautifulSoup
import os
import json
from dotenv import load_dotenv  # 추가
import requests
from xml.etree import ElementTree

# .env 파일에서 환경변수 불러오기 (코드 최상단에서 실행)
load_dotenv()

def get_recipe_by_ingredient(api_key, ingredient, start=1, end=5):
    url = f"http://openapi.foodsafetykorea.go.kr/api/{api_key}/COOKRCP01/xml/{start}/{end}/RCP_NM={ingredient}"
    response = requests.get(url)
    if response.status_code == 200:
        root = ElementTree.fromstring(response.content)
        rows = root.findall('.//row')
        recipes = []
        for row in rows:
            title = row.find('RCP_NM').text
            manual = row.find('MANUAL01').text
            img_url = row.find('ATT_FILE_NO_MAIN').text
            recipes.append({
                "title": title,
                "manual": manual,
                "img_url": img_url
            })
        return recipes
    else:
        print(f"API 요청 실패: {response.status_code}")
        return []

# 사용 예시
api_key = os.getenv("FOOD_API_KEY")
ingredient = "돼지고기"
recipes = get_recipe_by_ingredient(api_key, ingredient)
for r in recipes:
    print(r)

import requests
import os

def get_recipe_by_ingredient_json(ingredient):
    api_key = os.getenv("FOOD_API_KEY")
    url = f"http://openapi.foodsafetykorea.go.kr/api/{api_key}/COOKRCP01/json/1/3/RCP_NM={ingredient}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        rows = data.get('COOKRCP01', {}).get('row', [])
        recipes = []
        for row in rows:
            title = row.get('RCP_NM')
            manual = row.get('MANUAL01')
            img_url = row.get('ATT_FILE_NO_MAIN')
            recipes.append({
                "title": title,
                "manual": manual,
                "img_url": img_url
            })
        return recipes
    else:
        print(f"API 요청 실패: {response.status_code}")
        return []

# 사용 예시
print(get_recipe_by_ingredient_json("김치찌개"))

@dag(
    dag_id='mart_recipe_recommender',
    start_date=pendulum.datetime(2025, 7, 8, tz="Asia/Seoul"),
    schedule='0 10 * * 4',  # 매주 목요일 오전 10시에 실행
    catchup=False
)
def mart_recipe_bot():
    """
    홈플러스 할인 정보를 크롤링하여 추천 레시피를 알려주는 DAG
    """
    @task
    def get_sale_items_from_homeplus():
        """1단계: 홈플러스에서 할인 품목 크롤링 (JSON API 사용)"""
        print("홈플러스 JSON API 호출을 시작합니다.")
        
        # JSON API 엔드포인트 사용 (더 완전한 헤더로 보완)
        api_url = "https://mfront.homeplus.co.kr/api/v1/leaflets/items?categoryId=25&leafletNo=243&limit=20&offset=0&sort=RANK"
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
            # 세션 사용으로 브라우저 환경 모방
            session = requests.Session()
            
            # 1단계: 먼저 메인 페이지에 접근해서 쿠키 받기
            main_page = "https://mfront.homeplus.co.kr/leaflet"
            session.get(main_page, headers=headers)
            
            # 2단계: API 호출
            response = session.get(api_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # 디버깅: 응답 내용 확인
            print(f"API 응답 상태 코드: {response.status_code}")
            print(f"API 응답 헤더: {response.headers.get('content-type', 'unknown')}")
            
            # HTML 응답인지 확인
            if 'text/html' in response.headers.get('content-type', ''):
                print("HTML 응답을 받았습니다. 다른 방법을 시도합니다.")
                
                # 다른 API 패턴 시도
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
                    return "돼지고기"
            
            # JSON 데이터로 변환
            data = response.json()
            print(f"파싱된 JSON 데이터 구조: {type(data)}")
            
            # JSON 데이터에서 상품 정보 추출
            items = data.get('data', {}).get('dataList', [])
            
            if not items:
                print("API 응답에 상품 목록이 없습니다.")
                return "돼지고기"

            # 상품 이름(itemNm) 추출
            item_names = [item.get('itemNm') for item in items if item.get('itemNm')]
            
            if not item_names:
                print("상품 이름을 찾지 못했습니다.")
                return "돼지고기"

            print("--- 홈플러스 금주 할인 품목 ---")
            for i, name in enumerate(item_names[:5], 1):  # 상위 5개만 출력
                print(f"{i}. {name}")
            
            # 상품명에서 주재료 추출
            def extract_main_ingredient(item_name):
                """상품명에서 주재료명 추출"""
                if "특란" in item_name or "계란" in item_name:
                    return "계란"
                elif "닭갈비" in item_name or "닭" in item_name:
                    return "닭고기"
                elif "삼겹살" in item_name or "돼지" in item_name:
                    return "돼지고기"
                elif "우삼겹" in item_name or "소고기" in item_name:
                    return "소고기"
                elif "오리" in item_name:
                    return "오리고기"
                elif "버섯" in item_name:
                    return "버섯"
                elif "토마토" in item_name:
                    return "토마토"
                elif "복숭아" in item_name:
                    return "복숭아"
                elif "체리" in item_name:
                    return "체리"
                elif "김" in item_name:
                    return "김"
                elif "오징어" in item_name:
                    return "오징어"
                elif "주꾸미" in item_name:
                    return "주꾸미"
                elif "두부" in item_name:
                    return "두부"
                else:
                    return item_name  # 변환할 수 없으면 원래 이름 사용
            
            # 요리 가능한 재료들 추출
            cooking_ingredients = []
            for item_name in item_names[:10]:  # 상위 10개 품목 확인
                ingredient = extract_main_ingredient(item_name)
                if ingredient and ingredient not in cooking_ingredients:
                    cooking_ingredients.append(ingredient)
            
            print(f"요리 가능한 재료들: {cooking_ingredients}")
            return cooking_ingredients

        except requests.exceptions.RequestException as e:
            print(f"홈플러스 API 호출 중 오류 발생: {e}")
            return "돼지고기"
        except json.JSONDecodeError as e:
            print(f"JSON 파싱 중 오류 발생: {e}")
            return "돼지고기"
        except Exception as e:
            print(f"홈플러스 데이터 처리 중 오류 발생: {e}")
            return "돼지고기"

    @task
    def get_recipe_from_api(ingredients: list):
        api_key = os.getenv("FOOD_API_KEY")
        all_recipes = []
        
        for ingredient in ingredients[:3]:  # 최대 3개 재료로 제한
            url = f"http://openapi.foodsafetykorea.go.kr/api/{api_key}/COOKRCP01/json/1/1/RCP_NM={ingredient}"
            try:
                response = requests.get(url)
                if response.status_code == 200:
                    data = response.json()
                    rows = data.get('COOKRCP01', {}).get('row', [])
                    if rows:
                        row = rows[0]
                        title = row.get('RCP_NM')
                        manual = row.get('MANUAL01')
                        img_url = row.get('ATT_FILE_NO_MAIN')
                        recipe_info = (
                            f"'{ingredient}'(으)로 추천하는 레시피: {title}\n"
                            f"조리법: {manual}\n"
                            f"이미지: {img_url}"
                        )
                        all_recipes.append(recipe_info)
                        print(recipe_info)
                    else:
                        print(f"'{ingredient}'에 대한 레시피를 찾지 못했습니다.")
                else:
                    print(f"'{ingredient}' API 요청 실패: {response.status_code}")
            except Exception as e:
                print(f"'{ingredient}' 레시피 조회 중 오류: {e}")
        
        if all_recipes:
            return "\n\n".join(all_recipes)
        else:
            return "추천할 레시피를 찾지 못했습니다."

    # @task
    # def send_notification(recipe_info: str):
    #     """3단계: 결과 알림 (카카오톡 연동)"""
    #     print(f"오늘의 추천 메뉴 알림: {recipe_info}")

    #     # 실제 Access Token은 환경 변수 등으로 관리
    #     KAKAO_ACCESS_TOKEN = os.getenv("KAKAO_ACCESS_TOKEN")
    #     if not KAKAO_ACCESS_TOKEN:
    #         print("카카오 Access Token이 설정되지 않았습니다. 알림을 보낼 수 없습니다.")
    #         return

    #     headers = {
    #         "Authorization": f"Bearer {KAKAO_ACCESS_TOKEN}"
    #     }
    #     data = {
    #         "template_object": json.dumps({
    #             "object_type": "text",
    #             "text": recipe_info,
    #             "link": {
    #                 "web_url": "https://www.10000recipe.com",
    #                 "mobile_web_url": "https://www.10000recipe.com"
    #             },
    #             "button_title": "자세히 보기"
    #         })
    #     }
    #     response = requests.post("https://kapi.kakao.com/v2/api/talk/memo/default/send", headers=headers, data=data)
    #     if response.status_code == 200:
    #         print("카카오톡 알림 성공!")
    #     else:
    #         print(f"카카오톡 알림 실패: {response.status_code}, {response.json()}")

    # 작업 흐름 설정
    sale_items = get_sale_items_from_homeplus()
    recipes = get_recipe_from_api(sale_items)
    # send_notification(recipes)

mart_recipe_bot()