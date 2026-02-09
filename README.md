# 🛡️ FastAPI Clean Board Architecture

<div align="center">

<img src="https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white">
<img src="https://img.shields.io/badge/FastAPI-0.109.0-009688?style=for-the-badge&logo=fastapi&logoColor=white">
<img src="https://img.shields.io/badge/SQLAlchemy-2.0-D71F00?style=for-the-badge&logo=sqlalchemy&logoColor=white">
<img src="https://img.shields.io/badge/Redis-7.0-DC382D?style=for-the-badge&logo=redis&logoColor=white">

<br>

**"기능 중심의 구현을 넘어, 지속 가능한 아키텍처를 지향합니다."**
<br>
Layered Architecture와 Unit of Work 패턴을 적용하여 **유지보수성**과 **데이터 무결성**을 확보한 게시판 API 서비스 아키텍처입니다.

</div>

---

## 📖 프로젝트 소개 (Introduction)

### 👨‍💻 Client Developer to Backend Engineer
C# WinForm 기반의 클라이언트 개발자로 실무를 경험하며, **API 서버가 제공하는 데이터의 구조와 품질이 클라이언트의 성능과 사용자 경험(UX)에 결정적인 영향**을 미친다는 것을 절감했습니다.

"화면이 잘 돌아가는 것"을 넘어, 그 기반이 되는 **안정적이고 확장 가능한 서버를 직접 설계**하고 싶다는 열정으로 백엔드 개발에 깊이 파고들게 되었습니다.

### 🎯 Development Motivation
이전 개인 프로젝트(`EliteMiko_Bot`)를 운영하면서, 기능이 추가될수록 비즈니스 로직과 API 코드가 뒤섞여 유지보수가 어려워지는 문제를 경험했습니다. **"혼자 만드는 작은 프로젝트라도 체계적인 구조가 없다면 확장이 불가능하다"**는 것을 깨닫고, 본 프로젝트를 시작했습니다.

이 프로젝트는 단순히 기능을 구현하는 것을 넘어, **Layered Architecture**와 **Unit of Work(UoW)** 패턴을 도입하여 **확장성**과 **데이터 무결성**을 최우선으로 설계했습니다.

---

## 🏗️ 시스템 아키텍처

본 프로젝트는 **관심사의 분리**를 위해 계층형 아키텍처를 사용했습니다.

* **Presentation Layer (API):** HTTP 요청/응답 처리, Pydantic을 이용한 데이터 검증
* **Service Layer (Business Logic):** 핵심 비즈니스 로직 수행, 트랜잭션 제어
* **Repository Layer (Data Access):** DB 접근 및 쿼리 수행, ORM(SQLAlchemy) 사용

### 🔑 Key Design Patterns
1.  **Unit of Work (UoW):** SQLAlchemy 세션을 추상화하여 서비스 계층에서 트랜잭션의 시작과 종료(Commit/Rollback)를 명시적으로 제어합니다.
2.  **RepoResult Pattern:** Repository 계층에서 `HTTPException`을 발생시키지 않고, 상태(SUCCESS, NOT_FOUND, FORBIDDEN 등)와 데이터를 캡슐화한 객체를 반환하여 **계층 간 결합도**를 낮췄습니다.

---

## 💡 기술적 의사결정 및 문제 해결

개발 과정에서 마주친 문제들과 이를 해결하기 위해 도입한 기술적 의사결정입니다.

| 문제 상황 (Problem) | 해결 방안 (Solution) |
| :--- | :--- |
| **데이터 무결성 확보**<br>다중 테이블 업데이트 중 예외 발생 시 데이터 불일치 위험 | **Unit of Work (UoW) 패턴 구현**<br>트랜잭션 범위를 비즈니스 로직 단위로 묶어 원자성(Atomicity)을 보장하고, 로직 성공 시에만 Commit 되도록 설계 |
| **계층 간 결합도 완화**<br>Repository에서 직접 예외를 던질 시 프레임워크 종속성 발생 및 실패 원인 구분(403 vs 404)의 모호함 | **RepoResult 패턴 도입**<br>상태와 데이터를 캡슐화한 RepoResult 객체를 도입하여 Service 계층에서 명확한 비즈니스 예외 처리가 가능하도록 구현 |
| **DB 쓰기 부하 (I/O 병목)**<br>조회 시마다 발생하는 UPDATE 쿼리로 인한 성능 저하 | **Redis Write-Behind 전략**<br>Redis 캐시에 조회수를 선반영하고, 백그라운드 태스크로 DB에 일괄 업데이트하여 쓰기 연산 최소화 |
| **협업 효율 저하**<br>API마다 제각각인 에러 응답 포맷 | **Global Exception Handler & 표준화**<br>모든 예외를 일관된 JSON 포맷으로 반환하고, 구체적인 예외 클래스(`ReplyDepthLimitExceeded` 등)를 정의하여 명확한 피드백 제공 |
| **보안 취약점**<br>Refresh Token 탈취 및 계정 도용 위험 | **Token Rotation & Hashing**<br>토큰 갱신 시 기존 토큰 폐기(Rotation) 및 DB 저장 시 해싱(Hashing) 적용. 심층 방어(Defense in Depth) 전략 구현 |
| **디버깅 난이도**<br>비동기 요청 혼재 시 로그 추적 불가 | **Trace ID Middleware**<br>모든 요청 헤더에 고유 UUID를 부여하여 로그 컨텍스트에 포함. 요청의 전체 흐름을 한눈에 파악 가능한 모니터링 환경 구축 |

---

## 🚀 주요 기능

### 📋 Board Domain
* **게시글:** 작성, 수정, 삭제, 검색, 페이징
* **댓글:** 계층형 대댓글(Nested Comments) 구조 지원
* **권한:** 작성자 본인 확인 및 권한 검증 로직

### 🔒 Authentication & Security
* **JWT 인증:** Access Token & Refresh Token 분리
* **보안 강화:**
    * **Argon2** 알고리즘을 이용한 비밀번호 해싱
    * **Refresh Token Rotation** 적용으로 토큰 탈취 방지

### ⚡ Performance & Stability
* **Redis Write-Behind:** 조회수 카운팅 최적화
* **Global Exception Handler:** 표준화된 API 에러 응답 포맷 제공
* **Logging:** Trace ID 기반 요청/응답 로깅 및 모니터링

### 🧪 Testing
* **Pytest:** 통합 테스트(Integration Test) 작성
* **Coverage:** 인증, 게시글, 댓글 API 주요 로직 테스트

---

## 🛠️ 기술 스택

* **Language:** Python 3.11+
* **Framework:** FastAPI
* **Database:** PostgreSQL (Main), Redis (Cache/Buffer)
* **ORM:** SQLAlchemy
* **Migration:** Alembic
* **Testing:** Pytest, AsyncIO

---

## 🏁 설치 및 실행

### 1. Repository Clone
```bash
git clone https://github.com/Angelcon99/FastAPI-Clean-Board.git
cd FastAPI-Clean-Board
```

### 2. 가상환경 생성 및 의존성 설치
```bash
# 가상환경 생성 (권장)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 패키지 설치
pip install -r requirements.txt
```

### 3. 환경 변수 설정 (.env)
```env
# Program
PROJECT_NAME="FastAPI Clean Board"
VERSION="1.0.0"
TESTING=False

# DB (PostgreSQL)
DATABASE_URL=postgresql+asyncpg://your_user:your_password@localhost:5432/your_db

# Redis
REDIS_URL=redis://localhost:6379/0

# Security
SECRET_KEY=your_secret_key_string
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Other
USE_VIEWS_COUNTER_CACHE=True
```

### 4. 데이터베이스 마이그레이션 (Alembic)
```bash
alembic upgrade head
```

### 5. 서버 실행
``` bash
uvicorn app.main:app
```
