from airflow.decorators import dag, task
from airflow.operators.email import EmailOperator
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

    def send_recipe_email(recipes_content):
        # Airflow Connection을 사용한 이메일 발송
        from airflow.providers.smtp.hooks.smtp import SmtpHook
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        try:
            # YAML에서 설정 정보 읽기 (SMTP Hook 대신)
            
            # 환경변수에서 SMTP 설정 읽기
            smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
            smtp_port = int(os.getenv('SMTP_PORT', '587'))
            smtp_user = os.getenv('SMTP_USER')
            smtp_password = os.getenv('SMTP_PASSWORD')
            from_email = os.getenv('NOTIFICATION_FROM_EMAIL')
            to_email = os.getenv('NOTIFICATION_TO_EMAIL')
            
            print(f"환경변수 확인:")
            print(f"- SMTP_HOST: {smtp_host}")
            print(f"- SMTP_PORT: {smtp_port}")
            print(f"- SMTP_USER: {'설정됨' if smtp_user else '미설정'}")
            print(f"- SMTP_PASSWORD: {'설정됨' if smtp_password else '미설정'}")
            print(f"- FROM_EMAIL: {from_email if from_email else '미설정'}")
            print(f"- TO_EMAIL: {to_email if to_email else '미설정'}")
            
            if not smtp_user or not smtp_password:
                raise Exception("SMTP_USER 또는 SMTP_PASSWORD 환경변수가 설정되지 않았습니다")
            
            if not from_email or not to_email:
                print("이메일 주소 환경변수 미설정. SMTP_USER를 기본값으로 사용")
                from_email = smtp_user
                to_email = smtp_user
                
            print(f"이메일 발송 설정: {from_email} -> {to_email}")
            
            # 이메일 구성
            msg = MIMEMultipart('alternative')
            msg['Subject'] = "📧 이번 주 추천 레시피"
            msg['From'] = from_email
            msg['To'] = to_email
            
            html_content = f"""
            <h2>🍳 이번 주 추천 레시피</h2>
            <p>홈플러스 할인 상품을 기반으로 한 맞춤 레시피를 보내드립니다!</p>
            <hr>
            <pre style="font-family: Arial, sans-serif; white-space: pre-wrap;">{recipes_content}</pre>
            <hr>
            <p><small>자동 생성된 이메일입니다. 매주 목요일 오전 10시에 발송됩니다.</small></p>
            """
            
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            # 환경변수 설정으로 직접 SMTP 발송
            import smtplib
            
            print(f"SMTP 서버 연결: {smtp_host}:{smtp_port}")
            server = smtplib.SMTP(smtp_host, smtp_port)
            server.starttls()
            print("TLS 연결 성공")
            server.login(smtp_user, smtp_password)
            print("로그인 성공")
            server.send_message(msg)
            server.quit()
            print("이메일 발송 완료")
            
            print("✅ Airflow SMTP Hook으로 이메일 발송 성공!")
            return True
            
        except Exception as e:
            print(f"❌ SMTP Hook 발송 실패: {e}")
            import traceback
            print(f"상세 에러: {traceback.format_exc()}")
            return False

    @task
    def send_recipe_notification(recipes):
        """EmailOperator로 레시피 이메일 발송"""
        print("레시피 이메일을 발송합니다...")
        print(f"레시피 개수: {len(recipes)}")
        
        # 레시피 딕셔너리 리스트를 HTML로 변환
        html_recipes = []
        for recipe in recipes:
            html_recipes.append(f"<h3>요리 제목: {recipe['title']}</h3>")
            html_recipes.append(f"<p><strong>레시피:</strong><br>{recipe['manual'].replace(chr(10), '<br>')}</p>")
            html_recipes.append(f"<p><strong>이미지 주소:</strong> <a href='{recipe['img_url']}'>보기</a></p>")
            html_recipes.append("<hr>")
        
        recipes_html = "".join(html_recipes)
        
        print("=== 이메일 내용 미리보기 ===")
        print(recipes_html[:500] + "..." if len(recipes_html) > 500 else recipes_html)
        print("=== 미리보기 끝 ===")
        
        try:
            print("📧 EmailOperator로 이메일 발송 시작...")
            
            # airflow_settings.yaml에서 이메일 주소 가져오기
            import yaml
            
            settings_path = '/mnt/c/Users/Public/menu-recommander/airflow_settings.yaml'
            if not os.path.exists(settings_path):
                settings_path = '../airflow_settings.yaml'
            if not os.path.exists(settings_path):
                settings_path = './airflow_settings.yaml'
            
            with open(settings_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            # Variables에서 이메일 주소 찾기
            variables = config.get('airflow', {}).get('variables', [])
            to_email = None
            
            for var in variables:
                if var.get('variable_name') == 'NOTIFICATION_TO_EMAIL':
                    to_email = var.get('variable_value')
                    break
            
            if not to_email:
                raise Exception("airflow_settings.yaml에서 NOTIFICATION_TO_EMAIL을 찾을 수 없습니다")
            
            print(f"YAML에서 이메일 주소: {to_email}")
            
            # EmailOperator 사용
            email_op = EmailOperator(
                task_id='send_recipe_email_op',
                to=[to_email],
                subject='📧 이번 주 추천 레시피',
                html_content=f"""
                <html>
                <head><meta charset="UTF-8"></head>
                <body>
                    <h2>🍳 이번 주 추천 레시피</h2>
                    <p>홈플러스 할인 상품을 기반으로 한 맞춤 레시피를 보내드립니다!</p>
                    <hr>
                    {recipes_html}
                    <hr>
                    <p><small>자동 생성된 이메일입니다. 매주 목요일 오전 10시에 발송됩니다.</small></p>
                </body>
                </html>
                """,
                conn_id='smtp_default'
            )
            
            # 현재 context 가져와서 실행
            from airflow.operators.python import get_current_context
            context = get_current_context()
            
            email_op.execute(context)
            print("✅ EmailOperator 이메일 발송 완료!")
            return "✅ 이메일 발송 성공"
            
        except Exception as e:
            print(f"❌ EmailOperator 이메일 발송 실패: {e}")
            import traceback
            print("=== 상세 에러 스택 ===")
            print(traceback.format_exc())
            print("=== 에러 스택 끝 ===")
            return "⚠️ 이메일 발송 실패"

    sale_items = get_sale_items()
    recipes = recommend_recipe(sale_items)
    email_task = send_recipe_notification(recipes)

    sale_items >> recipes >> email_task

mart_recipe_bot()