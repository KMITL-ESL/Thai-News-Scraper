from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class MatichonRawNewsEntity(Base):
    __tablename__ = 'matichon_raw_news'

    id = Column(Integer, nullable=True, primary_key=True, autoincrement=True)
    publish_date = Column(DateTime)
    title = Column(String)
    content = Column(String)
    created_at = Column(DateTime, nullable=False)
    source = Column(String, nullable=False)
    link = Column(String, nullable=False, unique=True)
    category = Column(String, nullable=False)
    tags = Column(String)
    sub_category = Column(String)

    def __repr__(self):
        return f"<MatichonRawNewsEntity(id={self.id}, title={self.title}, publish_date={self.publish_date})>" 