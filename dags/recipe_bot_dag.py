from airflow.decorators import dag, task
from dags.recipe_tasks.homeplus import get_sale_items_from_homeplus
from dags.recipe_tasks.recipe_api import get_recipe_from_api
import pendulum
import os
import requests

@dag(
    dag_id='mart_recipe_recommender',
    start_date=pendulum.datetime(2025, 7, 8, tz="Asia/Seoul"),
    schedule='0 10 * * 4',
    catchup=False
)
def mart_recipe_bot():
    @task
    def get_sale_items():
        return get_sale_items_from_homeplus()

    def extract_manual(row):
        manual_steps = []
        for i in range(1, 21):
            step = row.get(f'MANUAL{str(i).zfill(2)}')
            if step and step.strip():
                manual_steps.append(step.strip())
        return "\n".join(manual_steps)

    @task
    def recommend_recipe(ingredients: list):
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
                    recipes.append({
                        'title': title,
                        'manual': manual,
                        'img_url': img_url
                    })
        return recipes

    sale_items = get_sale_items()
    recipes = recommend_recipe(sale_items)

mart_recipe_bot()