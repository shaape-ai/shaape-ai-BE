from sqlalchemy import BLOB, Column, Float, Integer, String, TIMESTAMP, func, JSON
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True)
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.current_timestamp())
    updated_at = Column(TIMESTAMP, nullable=False, server_default=func.current_timestamp(), onupdate=func.current_timestamp())
    source = Column(String(255), nullable=False)

class Product(Base):
    __tablename__ = 'products'

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    name = Column(String(255), nullable=True)
    description = Column(String(255), nullable=True)
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.current_timestamp())
    updated_at = Column(TIMESTAMP, nullable=False, server_default=func.current_timestamp(), onupdate=func.current_timestamp())
    product_id = Column(String(255), nullable=False)
    url = Column(String(255), nullable=False)
    color = Column(String(255), nullable=False)
    ocassion = Column(String(255), nullable=False)
    category = Column(String(255), nullable=False)
    embedding_index_id = Column(String(255), nullable=False)
    source = Column(String(255), nullable=False)
    price = Column(Float, nullable=False)
    size_chart = Column(JSON, nullable=True)
    media = Column(JSON, nullable=True)

class Embeddings(Base):
    __tablename__ = 'embeddings'
    id = Column(Integer, primary_key=True, nullable=False)
    product_id = Column(String(255), nullable=True)
    embedding = Column(BLOB, nullable=True)




