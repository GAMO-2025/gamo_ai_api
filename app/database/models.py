from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.sql import func
from app.database.database import Base

class Keyword(Base):
    __tablename__ = "keywords"

    keywordId = Column(String(11), primary_key=True, index=True)
    keyword = Column(String(255), nullable=False)
    videocallId = Column(Integer, nullable=False)
    date = Column(DateTime(timezone=True), server_default=func.now())  # DB 자동 시간
