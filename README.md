# LinguaPal

외국어 학습을 위한 인터랙티브 웹 애플리케이션입니다. 스마트 학습, 퀴즈, 단어장 등 다양한 학습 방식을 통해 효과적으로 언어를 학습할 수 있습니다.

## 서비스 소개

LinguaPal은 사용자 맞춤형 언어 학습 플랫폼입니다. xAPI(Experience API) 기반의 학습 기록 시스템을 통해 학습 진도와 성과를 추적하고, 개인화된 학습 경험을 제공합니다.

### 주요 특징
- **다국어 지원**: 일본어, 스페인어, 영어 등 다양한 언어 학습 지원
- **스마트 학습 알고리즘**: 1/3 복습 + 2/3 새 단어 구성, 퀴즈 오답 단어 우선 복습
- **TTS 음성 지원**: Web Speech API 기반 단어/예문 발음 재생
- **학습 분석**: xAPI/LRS 기반 상세 학습 데이터 분석
- **적응형 퀴즈**: 오답률, 최근 학습, 출제 빈도 기반 스마트 문제 선택
- **관리자 대시보드**: 실시간 학습 통계 및 다차원 사용자 분석

## 주요 기능

### 학습 기능
| 기능 | 설명 |
|------|------|
| **학습하기** | 스마트 알고리즘 기반 단어 학습 (1/3 복습 + 2/3 새 단어, 퀴즈 오답 우선 복습) |
| **단어 퀴즈** | 5가지 유형 - 단어→모국어, 모국어→단어(선택/입력), 예문 빈칸 채우기, 혼합 |
| **가나 퀴즈** | 일본어 히라가나/가타카나 학습 전용 퀴즈 (가나→로마자, 로마자→가나 선택/입력) |
| **학습한 단어** | 학습하기에서 본 단어 목록 조회 및 복습 |
| **내 단어장** | 개인 단어장 생성/관리, 단어장별 퀴즈 출제 |
| **배운 단어 퀴즈** | 학습한 단어만으로 퀴즈 구성 (오답률/최근학습/출제빈도 기반 스마트 선택) |
| **단어 탐색** | 학습 언어별 전체 단어 브라우징 및 랜덤 단어 |
| **TTS 음성 재생** | 단어 및 예문 발음 듣기 (10개 이상 언어 지원) |

### 관리자 기능
| 기능 | 설명 |
|------|------|
| **LRS 대시보드** | xAPI 기반 학습 분석 (개요/활동별/학생별/분석 4개 탭) |
| **단어 관리** | 단어/번역/예문/예문번역 CRUD, 품사/난이도/카테고리 관리 |
| **정책 관리** | 이용약관/개인정보처리방침 편집 (마크다운) |

### 사용자 기능
| 기능 | 설명 |
|------|------|
| **Google 로그인** | OAuth 2.0 기반 간편 로그인 |
| **프로필 관리** | 닉네임, 학습 언어, 국가 설정 |
| **학습 기록** | 퀴즈/학습 히스토리 및 정답률 추적 |
| **학습 대시보드** | 퀴즈별 개인 성과 통계 및 취약 단어 분석 |

## 기술 스택

### Backend
| 기술 | 용도 |
|------|------|
| **Django 5.2** | 웹 프레임워크 |
| **Django REST Framework** | RESTful API |
| **PostgreSQL** | 메인 데이터베이스 |
| **Elasticsearch 8.11** | 학습 데이터 분석 및 검색 |
| **Celery** | 비동기 작업 처리 (xAPI Statement 생성) |
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
| **Web Speech API** | TTS 음성 재생 |

> 프론트엔드는 **바이브코딩**으로 개발되었습니다.

### Infrastructure
| 기술 | 용도 |
|------|------|
| **Docker** | 컨테이너화 |
| **Docker Compose** | 멀티 컨테이너 오케스트레이션 |

### 학습 분석 (xAPI/LRS)
- **xAPI 1.0.3 표준**: 학습 활동 추적을 위한 국제 표준 준수
- **커스텀 LRS**: Elasticsearch 기반 자체 구현
- **cmi5 세션 관리**: 학습 세션 라이프사이클 관리
- **실시간 분석**: 학습 패턴 및 성과 분석
- **비동기 처리**: Celery + RabbitMQ 기반 Statement 비동기 생성
- **다차원 대시보드**: 개요/활동별/학생별/분석 4개 탭

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
│   ├── accounts/       # 사용자 인증/계정 (Google OAuth)
│   ├── lrs/            # xAPI/LRS 시스템 (Elasticsearch 기반)
│   ├── words/          # 단어/퀴즈/학습하기/단어장 관리
│   └── policies/       # 정책 문서 (MD 파일)
├── frontend/           # React 프론트엔드
│   ├── src/
│   │   ├── components/ # 공통 컴포넌트 (Layout, Modal, TTS 등)
│   │   ├── pages/      # 페이지 컴포넌트 (19개)
│   │   ├── services/   # API 서비스 + LRS 미들웨어
│   │   ├── contexts/   # React Context (Auth)
│   │   ├── types/      # TypeScript 타입 정의
│   │   └── utils/      # 유틸리티 (TTS 등)
│   └── ...
├── docker/             # Docker 설정
│   ├── docker-compose.dev.yml
│   └── docker-compose.prod.yml
└── requirements.txt    # Python 의존성
```

## 라이선스

This project is licensed under the MIT License.
