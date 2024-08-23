from typing import Optional
from sqlalchemy import select
from models.db_models import Embeddings, User, Product
from interfaces.users_interface import User
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, NoResultFound


def get_user(db: Session, id: str):
    return db.query(User).filter(User.id == id).first()

def create_user(db: Session, user: User):
    try:
        db_video = User(**user.dict())
        db.add(db_video)
        db.commit()
        db.refresh(db_video)
        return db_video
    except IntegrityError as e:
        db.rollback()
        if "UNIQUE constraint failed: user.id" in str(e.orig):
            existing_user = db.query(User).filter_by(youtube_video_id=user.youtube_video_id).first()
            if existing_user:
                for key, value in user.dict().items():
                    setattr(existing_user, key, value)
                db.commit()
                db.refresh(existing_user)
                return existing_user       
        print(f"{type(e).__name__} at line {e.__traceback__.tb_lineno} of {__file__}: {e}")
    except Exception as e:
        db.rollback()
        print(f"{type(e).__name__} at line {e.__traceback__.tb_lineno} of {__file__}: {e}")


def create_product(db: Session, product: Product):
    try:
        db_product = Product(**product)
        db.add(db_product)
        db.commit()
        return db_product
    except IntegrityError as e:
        db.rollback()
        if "UNIQUE constraint failed: user.id" in str(e.orig):
            existing_user = db.query(Product).filter_by(product_id=product.product_id).first()
            if existing_user:
                for key, value in product.dict().items():
                    setattr(existing_user, key, value)
                db.commit()
                db.refresh(existing_user)
                return existing_user       
        print(f"{type(e).__name__} at line {e.__traceback__.tb_lineno} of {__file__}: {e}")
    except Exception as e:
        db.rollback()
        print(f"{type(e).__name__} at line {e.__traceback__.tb_lineno} of {__file__}: {e}")

def get_product(db:Session,product_id):
    return db.query(Product).filter(Product.product_id == product_id).first()
def get_product_by_id(db: Session, id):
    return db.query(Embeddings, Product).join(Product, Embeddings.product_id == Product.id).offset(id).limit(1).first()
    if result:
        embeddings, product = result
        return {
            "embeddings": EmbeddingSchema.from_orm(embeddings),
            "product": ProductSchema.from_orm(product),
        }
    return None

def update_product(db:Session,id,product: Product):
    try:
        db.query(Product).filter(Product.id == id).update(product)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"{type(e).__name__} at line {e.__traceback__.tb_lineno} of {__file__}: {e}")

def get_all_products(db:Session,product_id:Optional[str]):
    if product_id:
        return db.query(Product).filter(Product.id>product_id).all()
    return db.query(Product).all()

def get_last_row(db:Session):
    return db.query(Embeddings).order_by(Embeddings.id.desc()).first()

def get_all_embeddings(db:Session):
    return db.query(Embeddings).all()
