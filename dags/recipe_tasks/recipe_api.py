import os
import requests
from xml.etree import ElementTree

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