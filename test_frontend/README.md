# LinguaPal API 테스트 프론트엔드

이 디렉토리에는 LinguaPal API를 테스트할 수 있는 프론트엔드 HTML 페이지들이 포함되어 있습니다.

## 파일 구조

```
test_frontend/
├── index.html           # 메인 페이지 (테스트 메뉴)
├── test_login.html      # Google OAuth 로그인 테스트
├── test_profile.html    # 프로필 생성/수정 테스트
└── README.md           # 이 문서
```

## 사용 방법

### 1. Django 서버 실행

먼저 Django 개발 서버가 실행 중이어야 합니다.

```bash
cd docker
docker-compose -f docker-compose.dev.yml up
```

서버가 `http://localhost:8000`에서 실행되는지 확인하세요.

### 2. 초기 데이터 로드 (처음 한 번만)

언어 및 국가 마스터 데이터를 로드합니다.

```bash
cd docker
docker-compose -f docker-compose.dev.yml exec web python manage.py load_initial_data
```

### 3. HTTP 서버 실행

테스트 페이지는 `file://` 프로토콜이 아닌 HTTP 서버를 통해 접근해야 합니다.

#### 방법 1: Python 내장 서버 (권장)

```bash
# test_frontend 디렉토리에서 실행
cd test_frontend
python -m http.server 3000
```

그 후 브라우저에서 `http://localhost:3000` 접속

#### 방법 2: Node.js http-server

```bash
# http-server 설치 (처음 한 번만)
npm install -g http-server

# test_frontend 디렉토리에서 실행
cd test_frontend
http-server -p 3000
```

#### 방법 3: VSCode Live Server 확장

1. VSCode에서 Live Server 확장 설치
2. `index.html` 파일 우클릭
3. "Open with Live Server" 선택

### 4. Google Cloud Console 설정

Google OAuth가 정상적으로 작동하려면 Google Cloud Console에서 다음을 설정해야 합니다:

1. [Google Cloud Console](https://console.cloud.google.com/) 접속
2. 프로젝트 선택 또는 생성
3. "API 및 서비스" > "사용자 인증 정보" 메뉴로 이동
4. "OAuth 2.0 클라이언트 ID" 생성 또는 수정
5. **승인된 JavaScript 원본**에 다음 추가:
   - `http://localhost:3000`
   - `http://localhost:8000`
6. **승인된 리디렉션 URI**에 다음 추가 (필요시):
   - `http://localhost:3000`
   - `http://localhost:8000`

## 테스트 시나리오

### 시나리오 1: 신규 사용자 가입 및 프로필 생성

1. `http://localhost:3000` 접속 (메인 페이지)
2. "Google 로그인" 클릭
3. Google 계정으로 로그인
4. JWT 토큰이 로컬 스토리지에 저장됨
5. 메인 페이지로 돌아가서 "프로필 관리" 클릭
6. 닉네임, 출신 국가, 배우고자 하는 언어 선택
7. "프로필 생성" 버튼 클릭
8. 생성된 프로필 확인

### 시나리오 2: 기존 사용자 로그인 및 프로필 조회

1. Google 로그인
2. 프로필 관리 페이지에서 "프로필 조회" 버튼 클릭
3. 기존 프로필 정보 확인

### 시나리오 3: 프로필 수정

1. 프로필 관리 페이지에서 프로필 조회
2. "프로필 수정" 섹션에서 닉네임 또는 언어 변경
3. "프로필 수정" 버튼 클릭
4. 수정된 프로필 확인

### 시나리오 4: 현재 사용자 정보 조회

1. 프로필 관리 페이지 하단의 "현재 사용자 정보 조회" 버튼 클릭
2. 사용자 정보 및 프로필 정보 통합 조회

## 테스트 페이지 기능

### index.html (메인 페이지)
- 서버 상태 확인
- 테스트 메뉴 제공
- 로그아웃 기능

### test_login.html (로그인 테스트)
- Google OAuth 로그인
- JWT 토큰 발급 및 저장
- 사용자 정보 표시
- 로그인 성공/실패 처리

### test_profile.html (프로필 테스트)
- 프로필 조회
- 프로필 생성 (닉네임, 국가, 언어)
- 프로필 수정 (닉네임, 언어만)
- 현재 사용자 정보 조회 (프로필 포함)
- 마스터 데이터 조회 (언어, 국가)
- 유효성 검증 메시지 표시

## 주의사항

1. **CORS 설정**: Django 서버의 `settings.py`에서 개발 모드일 때 `CORS_ALLOW_ALL_ORIGINS = True`가 설정되어 있어야 합니다.

2. **JWT 토큰**: 로그인 시 발급받은 JWT 토큰은 브라우저의 로컬 스토리지에 저장됩니다. 개발자 도구에서 확인할 수 있습니다.

3. **토큰 만료**: Access Token은 1시간 후 만료됩니다. 만료되면 다시 로그인해야 합니다.

4. **프로토콜**: 반드시 HTTP 서버를 통해 접근해야 하며, `file://` 프로토콜로는 CORS 및 OAuth가 정상 작동하지 않습니다.

5. **출신 국가 수정 불가**: 프로필 생성 시 설정한 출신 국가는 이후 수정할 수 없습니다.

## 디버깅

### 브라우저 개발자 도구 확인

- **Console**: API 요청/응답 로그 확인
- **Network**: API 호출 상태 및 응답 데이터 확인
- **Application > Local Storage**: JWT 토큰 확인

### 일반적인 문제 해결

1. **"Django 서버에 연결할 수 없습니다"**
   - Django 서버가 실행 중인지 확인
   - `http://localhost:8000/api/accounts/google/config/` 직접 접속 시도

2. **"origin_mismatch" 오류**
   - Google Cloud Console에서 승인된 JavaScript 원본에 `http://localhost:3000` 추가 확인

3. **"Failed to fetch" 오류**
   - CORS 설정 확인 (settings.py)
   - 브라우저 콘솔에서 자세한 오류 확인

4. **"프로필이 존재하지 않습니다"**
   - 정상적인 메시지입니다. "프로필 생성" 섹션에서 프로필을 생성하세요.

5. **"닉네임은 최소 2자 이상이어야 합니다"**
   - 닉네임을 2~50자 사이로 입력하세요.

6. **"이미 사용 중인 닉네임입니다"**
   - 다른 사용자가 사용 중인 닉네임입니다. 다른 닉네임을 선택하세요.

## API 엔드포인트

모든 API는 `http://localhost:8000/api/accounts/` 기준입니다.

### 인증 불필요
- `GET /google/config/` - Google OAuth Client ID 조회
- `GET /languages/` - 언어 목록 조회
- `GET /countries/` - 국가 목록 조회
- `POST /google/login/` - Google OAuth 로그인

### 인증 필요 (JWT 토큰 필요)
- `GET /me/` - 현재 사용자 정보 조회 (프로필 포함)
- `GET /profile/` - 프로필 조회
- `POST /profile/` - 프로필 생성
- `PATCH /profile/` - 프로필 수정 (닉네임, 언어만)

자세한 API 문서는 프로젝트 루트의 `PROFILE_API_GUIDE.md`를 참조하세요.

## 테스트 데이터

### 언어 (14개)
영어, 한국어, 일본어, 중국어, 스페인어, 프랑스어, 독일어, 러시아어, 아랍어, 포르투갈어, 이탈리아어, 베트남어, 태국어, 인도네시아어

### 국가 (19개)
대한민국, 미국, 일본, 중국, 영국, 프랑스, 독일, 스페인, 이탈리아, 캐나다, 호주, 브라질, 멕시코, 인도, 러시아, 싱가포르, 베트남, 태국, 인도네시아

## 라이선스

이 테스트 페이지는 개발 및 테스트 목적으로만 사용됩니다.
