from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

# DB URL 생성
DB_URL = f"mysql+pymysql://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"

# 엔진 생성
engine = create_engine(
    DB_URL,
    echo=settings.DEBUG,
    # 연결 끊김 방지 옵션
    pool_pre_ping=True,   # 쿼리 실행 직전에 연결 상태를 확인하고, 끊어졌으면 자동으로 재연결한다.
    pool_recycle=3600     # => 1시간(3600초)마다 연결을 강제로 갱신하여 MySQL 타임아웃을 방지
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()