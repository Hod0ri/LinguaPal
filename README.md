# LinguaPal

외국어 학습을 위한 인터랙티브 웹 애플리케이션입니다. 퀴즈, 플래시카드 등 다양한 학습 방식을 통해 효과적으로 언어를 학습할 수 있습니다.

## 서비스 소개

LinguaPal은 사용자 맞춤형 언어 학습 플랫폼입니다. xAPI(Experience API) 기반의 학습 기록 시스템을 통해 학습 진도와 성과를 추적하고, 개인화된 학습 경험을 제공합니다.

### 주요 특징
- **다국어 지원**: 일본어, 영어 등 다양한 언어 학습 지원
- **학습 분석**: xAPI/LRS 기반 상세 학습 데이터 분석
- **적응형 학습**: 취약 부분 집중 학습 기능
- **관리자 대시보드**: 실시간 학습 통계 및 사용자 분석

## 주요 기능

### 학습 기능
| 기능 | 설명 |
|------|------|
| **단어 퀴즈** | 외국어 단어를 다양한 형식으로 학습 (선택형, 입력형) |
| **가나 퀴즈** | 일본어 히라가나/가타카나 학습 전용 퀴즈 |
| **플래시카드** | 스와이프 방식의 단어 암기 학습 |
| **학습 대시보드** | 개인 학습 통계 및 진도 확인 |

### 관리자 기능
| 기능 | 설명 |
|------|------|
| **LRS 대시보드** | xAPI 기반 전체 사용자 학습 분석 |
| **단어 관리** | 학습 단어 추가/수정/삭제 |
| **정책 관리** | 이용약관/개인정보처리방침 편집 (마크다운) |

### 사용자 기능
| 기능 | 설명 |
|------|------|
| **Google 로그인** | OAuth 2.0 기반 간편 로그인 |
| **프로필 관리** | 닉네임, 학습 언어 설정 |
| **학습 기록** | 퀴즈 히스토리 및 정답률 추적 |

## 기술 스택

### Backend
| 기술 | 용도 |
|------|------|
| **Django 5.2** | 웹 프레임워크 |
| **Django REST Framework** | RESTful API |
| **PostgreSQL** | 메인 데이터베이스 |
| **Elasticsearch 8.11** | 학습 데이터 분석 및 검색 |
| **Celery** | 비동기 작업 처리 |
| **RabbitMQ** | 메시지 브로커 |
| **MinIO** | 오브젝트 스토리지 (S3 호환) |

### Frontend
| 기술 | 용도 |
|------|------|
| **React 18** | UI 라이브러리 |
| **TypeScript** | 타입 안정성 |
| **Vite** | 빌드 도구 |
| **TailwindCSS** | 스타일링 |
| **React Router** | 라우팅 |
| **Axios** | HTTP 클라이언트 |

> 프론트엔드는 **바이브코딩**으로 개발되었습니다.

### Infrastructure
| 기술 | 용도 |
|------|------|
| **Docker** | 컨테이너화 |
| **Docker Compose** | 멀티 컨테이너 오케스트레이션 |

### 학습 분석 (xAPI/LRS)
- **xAPI 표준**: 학습 활동 추적을 위한 국제 표준
- **커스텀 LRS**: Elasticsearch 기반 자체 구현
- **실시간 분석**: 학습 패턴 및 성과 분석

## 설치 및 실행

### 환경 변수 설정
```env
# Django Settings
SECRET_KEY=<your-secret-key>
DEBUG=True
RUN_MOD=dev

# Database
POSTGRES_DB=linguapal
POSTGRES_USER=linguapal
POSTGRES_PASSWORD=<your-db-password>

# Google OAuth
GOOGLE_CLIENT_ID=<your-google-client-id>
GOOGLE_CLIENT_SECRET=<your-google-client-secret>

# Elasticsearch
ELASTICSEARCH_HOST=http://elasticsearch:9200

# RabbitMQ
CELERY_BROKER_URL=amqp://linguapal:linguapal_mq@rabbitmq:5672//

# MinIO
MINIO_ACCESS_KEY=<your-minio-access-key>
MINIO_SECRET_KEY=<your-minio-secret-key>
```

### Docker로 실행
```bash
# 개발 환경
cd docker
docker compose -f docker-compose.dev.yml up -d

# 프로덕션 환경
docker compose -f docker-compose.prod.yml up -d
```

### 접속 URL
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000/api/v1
- **API 문서**: http://localhost:8000/api/schema/swagger-ui/

## 프로젝트 구조

```
LinguaPal/
├── LinguaPal/          # Django 프로젝트
│   ├── accounts/       # 사용자 인증/계정
│   ├── lrs/            # xAPI/LRS 시스템
│   ├── words/          # 단어/퀴즈 관리
│   └── policies/       # 정책 문서 (MD 파일)
├── frontend/           # React 프론트엔드
│   ├── src/
│   │   ├── components/ # 공통 컴포넌트
│   │   ├── pages/      # 페이지 컴포넌트
│   │   ├── services/   # API 서비스
│   │   └── contexts/   # React Context
│   └── ...
├── docker/             # Docker 설정
│   ├── docker-compose.dev.yml
│   └── docker-compose.prod.yml
└── requirements.txt    # Python 의존성
```

## 라이선스

This project is licensed under the MIT License.
