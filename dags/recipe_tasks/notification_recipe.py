from datetime import datetime
from airflow.decorators import dag, task
from airflow.providers.smtp.notifications.smtp import send_smtp_notification
from airflow.models import Variable
from recipe_tasks.homeplus import get_sale_items_from_homeplus
from recipe_tasks.recipe_api import get_recipe_from_api

# SMTP 알림 설정
# https://airflow.apache.org/docs/apache-airflow-providers-smtp/stable/_api/airflow/providers/smtp/notifications/smtp/index.html

def send_recipe_email(recipes_content):
    from_email = Variable.get('NOTIFICATION_FROM_EMAIL')  # 발신자 이메일
    to_email = Variable.get('NOTIFICATION_TO_EMAIL')      # 수신자 이메일
    
    return send_smtp_notification(
        
        from_email=from_email,
        to=to_email,
        smtp_conn_id="smtp_default",
        subject="이번 주 추천 레시피",
        html_content=f"""
        <h2>🍳 이번 주 추천 레시피</h2>
        <p>홈플러스 할인 상품을 기반으로 한 맞춤 레시피를 보내드립니다!</p>
        <hr>
        <pre style="font-family: Arial, sans-serif; white-space: pre-wrap;">{recipes_content}</pre>
        <hr>
        <p><small>자동 생성된 이메일입니다. 매주 목요일 오전 10시에 발송됩니다.</small></p>
        """
    )

@dag(
    dag_id="email_notifications",
    schedule=None,
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=["example", "notifications"],
    doc_md="""
    ## 이메일 알림 테스트 DAG
    
    이 DAG는 Airflow의 최신 SMTP 알림 기능을 테스트합니다.
    - 성공 태스크: 정상적으로 완료됩니다
    - 실패 태스크: 의도적으로 실패하여 이메일 알림을 트리거합니다
    """,
)
def email_notifications():
    """이메일 알림 테스트 DAG"""

    @task
    def success_task():
        """성공 테스트 태스크"""
        print("Success task completed!")
        return "success"

    @task(on_failure_callback=[get_smtp_notification()])
    def fail_task():
        """실패 테스트 태스크 (의도적 실패)"""
        raise Exception("Task failed intentionally for testing purpose")

    # Task dependencies 설정
    success_task() >> fail_task()


email_notifications()