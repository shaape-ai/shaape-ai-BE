from sqlalchemy import create_engine
from sqlalchemy import create_engine, URL
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

load_dotenv()


def get_db_engine():
    ca_path = os.getenv('CA_PATH')
    connect_args = {
            "ssl": {
                "ssl_ca": ca_path,
            }
        }    
    return create_engine(
        URL.create(
            drivername="mysql+pymysql",
            username=os.getenv('TIDB_USER'),
            password=os.getenv('TIDB_PASSWORD'),
            host=os.getenv('TIDB_HOST'),
            port=os.getenv('TIDB_PORT'),
            database=os.getenv('TIDB_DB_NAME'),
        ),
        connect_args=connect_args,
    )

engine = get_db_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
