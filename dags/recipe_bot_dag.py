from airflow.decorators import dag, task
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# 모듈화된 함수 import
from recipe_tasks.homeplus import get_sale_items_from_homeplus
from recipe_tasks.recipe_api import get_recipe_from_api

# 기본 설정 정의
default_args = {
    'owner': 'menu-recommander',
    'start_date': datetime(2025, 1, 1),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

@dag(
    dag_id='recipe_bot_dag',
    default_args=default_args,
    description='홈플러스 할인 정보를 크롤링하여 추천 레시피를 알려주는 DAG',
    schedule='@daily',
    catchup=False,
    tags=['recipe-bot'],
)
def recipe_bot_dag():
    """TaskFlow API를 사용한 데이터 처리 파이프라인"""

    start = BashOperator(
        task_id='start',
        bash_command='echo "Recipe Bot DAG 시작!"'
    )

    load_dotenv()

    @task
    def sale_items_task():
        return get_sale_items_from_homeplus()

    @task
    def recipe_task(ingredients: list):
        return get_recipe_from_api(ingredients)

    end = BashOperator(
        task_id='end',
        bash_command='echo "Recipe Bot DAG 완료!"'
    )

    # 작업 흐름 설정
    sale_items = sale_items_task()
    recipes = recipe_task(sale_items)
    start >> sale_items >> recipes >> end


recipe_bot_dag()