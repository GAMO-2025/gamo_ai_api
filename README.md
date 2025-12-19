# 🧑‍🧑‍🧒🙋📞 GAMO 
안녕하세요. 시니어 맞춤 가족 소통 서비스 가모(GAMO)의 Spring Boot Backend & Frontend 통합 레포지토리입니다.
\
[2025 성신여자대학교 융합캡스톤디자인 프로젝트]

<img src="https://github.com/user-attachments/assets/a164e657-8ca5-4b80-bfe4-2494e8a5e32d" width="70%" />

### 🤦‍♀️ 담당

<div align="center">

| Team Leader | 
|:-----------:|
| <img src="https://github.com/pjhyun0225.png" width="100" /> |
| [박지현](https://github.com/pjhyun0225)<br />키워드 추천, 편지 교정, 서버 배포 |
</div>


## ✨ **프로젝트 소개**
<div align="center">
  
### **프로젝트 목표**
<img src="https://github.com/user-attachments/assets/8674020b-2af9-4583-ac7d-c8095cb99c54" width="70%" />


### 🎦 GAMO 데모 영상
https://www.youtube.com/watch?v=aL9ShCryn3M


## 🛠 기술 스택

### Front-end  
<img src="https://skillicons.dev/icons?i=javascript,html,css,tailwindcss&theme=light" height="50">  
<img src="https://skillicons.dev/icons?i=webrtc&theme=light" height="50">

### Infra & Back-end  
<img src="https://skillicons.dev/icons?i=spring,fastapi,mysql,nginx,jenkins,gcp&theme=light" height="50">  

| 구분 | 기술 |
|------|------|
| **Language** | Java,Python |
| **Framework** | Spring Boot, FastAPI |
| **Database** | MySQL, JPA|
| **Infra** | GCP, Nginx |
| **CI/CD** | Jenkins |
| **Auth** | JWT, Spring Security |
| **기타** | OAuth, WebSocket, SSE, WebRTC, Google Cloud Storage |
| **외부 API** | Google Speech To Text, Gemini API |
| **frontend** | TailWindCss, HTML, Javascript, Thymeleaf  |

## ⛏️ 서비스 아키텍쳐
<div align="center">
<img width="90%" src="https://github.com/user-attachments/assets/9a8ad650-43c2-4543-b232-ac1fb1d32179" />
</div>

## 📁 프로젝트 구조
### Python 레포지토리 폴더 구조 
```
GAMO_AI_API/
├── app/                 # 애플리케이션 코드
│   ├── core/            # 환경설정
│   ├── database/        # DB 연결 및 모델
│   ├── routers/         # API 엔드포인트
│   ├── utils/           # 유틸리티 함수
│   └── main.py          # 서버 실행 파일
├── venv/                # 가상 환경
├── .env                 # 환경 변수
├── .gitignore
├── Jenkinsfile          # 배포 스크립트
└── README.md
```
