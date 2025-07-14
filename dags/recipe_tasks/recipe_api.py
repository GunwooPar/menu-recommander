import os
import requests
from xml.etree import ElementTree

def extract_manual(row):
    manual_steps = []
    for i in range(1, 21):
        step = row.get(f'MANUAL{str(i).zfill(2)}')
        if step and step.strip():
            manual_steps.append(step.strip())
    return "\n".join(manual_steps)

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
            manual = extract_manual(row)
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
    recipes = []
    for ingredient in ingredients:
        url = f"http://openapi.foodsafetykorea.go.kr/api/{api_key}/COOKRCP01/json/1/3/RCP_NM={ingredient}"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            rows = data.get('COOKRCP01', {}).get('row', [])
            for row in rows:
                title = row.get('RCP_NM')
                manual = extract_manual(row)
                img_url = row.get('ATT_FILE_NO_MAIN')
                recipes.append(f"[{title}]\n{manual}\n이미지: {img_url}\n---")
    if recipes:
        return "\n\n".join(recipes)  # str 반환!
    else:
        return "추천할 레시피가 없습니다." 