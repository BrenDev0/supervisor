# app/repositories/base_repository.py
from sqlalchemy.orm import Session
from typing import TypeVar, Generic, Type, List, Optional
from sqlalchemy import select, update, delete
import uuid

T = TypeVar("T") 

class BaseRepository(Generic[T]):
    def __init__(self, model: Type[T]):
        self.model = model

    def create(self, db: Session, data: T) -> T:
        db.add(data)
        db.commit()
        db.refresh(data)
        
        return data

    def get_one(self, db: Session, key: str, value: str | uuid.UUID) -> Optional[T]:
        stmt = select(self.model).where(getattr(self.model, key) == value)
        result = db.execute(stmt).scalar_one_or_none()
        
        return result

    def get_many(self, db: Session, key: str, value: str | uuid.UUID) -> List[T]:
        stmt = select(self.model).where(getattr(self.model, key) == value)
        
        return db.execute(stmt).scalars().all()

    def update(self, db: Session,  key: str, value: str | uuid.UUID, changes: dict) -> Optional[T]:
        stmt = update(self.model).where(getattr(self.model, key) == value).values(**changes).returning(*self.model.__table__.c)
        result = db.execute(stmt)
        db.commit()
        updated_row = result.fetchone()
        
        updated_user = self.model(**updated_row._mapping)
        return updated_user

    def delete(self, db: Session, key: str, value: str | uuid.UUID) -> Optional[T]:
        stmt = delete(self.model).where(getattr(self.model, key) == value).returning(*self.model.__table__.c)
        result = db.execute(stmt)
        db.commit()
        deleted_row = result.fetchone()
        
        
        deleted_user = self.model(**deleted_row._mapping)
        return deleted_user
    