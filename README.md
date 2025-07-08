# 🛒 마트 할인상품 기반 레시피 추천봇

매주 마트의 할인 전단지를 확인하고, 할인 중인 식재료로 만들 수 있는 요리 레시피를 자동으로 추천해주는 데이터 파이프라인 프로젝트입니다. '오늘 뭐 먹지?'와 '어떻게 하면 더 저렴하게 장을 볼까?'라는 두 가지 고민을 해결하는 것을 목표로 합니다.

## ✨ 주요 기능

* **홈플러스 온라인몰**의 할인 행사 상품 정보 크롤링
* **식품안전나라 공공데이터포털**의 레시피 Open API 연동
* **Apache Airflow**를 이용한 데이터 수집 및 추천 파이프라인 자동화
* 매주 정해진 시간에 자동으로 추천 메뉴 알림 (구현 예정)

## 🛠️ 기술 스택

* **Language**: Python
* **Orchestration**: Apache Airflow
* **Environment**: Docker, Astro CLI
* **Libraries**: Requests, BeautifulSoup4

## 🚀 로컬 환경에서 실행하기

이 프로젝트는 Astro CLI를 사용하여 로컬 환경에서 실행하는 것을 권장합니다.

**1. 프로젝트 클론**
```bash
git clone [https://github.com/GunwooPar/menu-recommander.git](https://github.com/GunwooPar/menu-recommander.git)
cd menu-recommander
```

**2. Astro CLI 설치 (WSL2/Linux/macOS)**
```bash
# 이전에 설치했다면 건너뛰세요.
curl -sSL install.astronomer.io | sudo bash
```

**3. 파이썬 라이브러리 추가**

프로젝트의 `requirements.txt` 파일에 아래 라이브러리가 포함되어 있는지 확인하고, 없다면 추가합니다.
```
requests
beautifulsoup4
```



## 🗓️ 추후 구현 계획

- [ ] 카카오톡 등 메신저를 통한 알림 기능 추가
