# Docker 사용 가이드

## 개요
LinguaPal 프로젝트의 Docker 설정은 개발/운영 환경을 분리하여 관리합니다.

## 파일 구조
```
.
├── docker/                       # Docker 관련 파일 디렉토리
│   ├── Dockerfile.dev           # 개발 환경용 Dockerfile
│   ├── Dockerfile.prod          # 운영 환경용 Dockerfile
│   ├── docker-compose.dev.yml   # 개발 환경용 Docker Compose
│   └── docker-compose.prod.yml  # 운영 환경용 Docker Compose
├── requirements.txt             # Python 의존성 (gunicorn 포함)
├── .dockerignore               # Docker 빌드 제외 파일
├── .env.example                # 환경 변수 예시
└── DOCKER.md                   # 이 파일
```

## 환경 설정

### 1. 환경 변수 파일 생성

개발 환경:
```bash
cp .env.example .env
```

운영 환경:
```bash
cp .env.example .env.prod
# .env.prod 파일을 편집하여 운영 환경에 맞게 수정
# DEBUG=False
# RUN_MOD=PROD
# SECRET_KEY=강력한-시크릿-키-생성
```

## 개발 환경 실행

개발 환경은 소스 코드가 볼륨 마운트되어 실시간으로 변경사항이 반영됩니다.

### 실행
```bash
docker-compose -f docker/docker-compose.dev.yml up --build
```

### 백그라운드 실행
```bash
docker-compose -f docker/docker-compose.dev.yml up -d --build
```

### 종료
```bash
docker-compose -f docker/docker-compose.dev.yml down
```

### 특징
- Python 3.14 사용
- Django 개발 서버 (runserver) 실행
- 소스 코드 실시간 반영 (볼륨 마운트)
- 포트: 8000
- 자동 재시작 활성화

## 운영 환경 실행

운영 환경은 Gunicorn WSGI 서버로 실행되며, 코드가 이미지에 포함됩니다.

### 실행
```bash
docker-compose -f docker/docker-compose.prod.yml up --build
```

### 백그라운드 실행
```bash
docker-compose -f docker/docker-compose.prod.yml up -d --build
```

### 종료
```bash
docker-compose -f docker/docker-compose.prod.yml down
```

### 특징
- Python 3.14 사용
- Gunicorn WSGI 서버 실행
- Workers: 4, Threads: 2
- Static 파일 수집 자동화
- 포트: 8000
- 재시작 정책: unless-stopped
- 헬스체크 포함

## 유용한 명령어

### 컨테이너 로그 확인
```bash
# 개발 환경
docker-compose -f docker/docker-compose.dev.yml logs -f

# 운영 환경
docker-compose -f docker/docker-compose.prod.yml logs -f
```

### 컨테이너 내부 접속
```bash
# 개발 환경
docker-compose -f docker/docker-compose.dev.yml exec web bash

# 운영 환경
docker-compose -f docker/docker-compose.prod.yml exec web bash
```

### Django 관리 명령 실행
```bash
# 개발 환경
docker-compose -f docker/docker-compose.dev.yml exec web python manage.py migrate
docker-compose -f docker/docker-compose.dev.yml exec web python manage.py createsuperuser

# 운영 환경
docker-compose -f docker/docker-compose.prod.yml exec web python manage.py migrate
docker-compose -f docker/docker-compose.prod.yml exec web python manage.py createsuperuser
```

### 이미지 재빌드
```bash
# 개발 환경
docker-compose -f docker/docker-compose.dev.yml build --no-cache

# 운영 환경
docker-compose -f docker/docker-compose.prod.yml build --no-cache
```

### 모든 컨테이너, 볼륨 삭제
```bash
# 개발 환경
docker-compose -f docker/docker-compose.dev.yml down -v

# 운영 환경
docker-compose -f docker/docker-compose.prod.yml down -v
```

## 주의사항

1. **운영 환경 SECRET_KEY**: `.env.prod` 파일의 SECRET_KEY는 반드시 강력한 키로 변경하세요.
2. **DEBUG 설정**: 운영 환경에서는 반드시 `DEBUG=False`로 설정하세요.
3. **ALLOWED_HOSTS**: 운영 환경에서는 settings.py의 ALLOWED_HOSTS를 실제 도메인으로 설정하세요.
4. **.env 파일**: .env 파일은 절대 Git에 커밋하지 마세요 (.gitignore에 포함되어 있습니다).

## 트러블슈팅

### 포트 충돌
이미 8000 포트가 사용 중인 경우:
```bash
# docker/docker-compose.*.yml 파일에서 포트 변경
ports:
  - "8001:8000"  # 호스트 포트를 8001로 변경
```

### 권한 문제
Windows에서 볼륨 마운트 권한 문제 발생 시 Docker Desktop 설정에서 해당 드라이브를 공유하세요.

### 빌드 캐시 문제
빌드 캐시로 인한 문제 발생 시:
```bash
docker-compose -f docker/docker-compose.dev.yml build --no-cache
```
