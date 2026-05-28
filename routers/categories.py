from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from core.database import get_db
from core.security import get_current_user
from models.user import Category, User

router = APIRouter(prefix="/categories", tags=["Categories"])


class CategoryCreate(BaseModel):
    name: str


@router.post("/", status_code=201)
def create_category(
    payload: CategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cat = Category(user_id=current_user.user_id, name=payload.name)
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat


@router.get("/")
def list_categories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return db.query(Category).filter(Category.user_id == current_user.user_id).all()


@router.put("/{category_id}")
def update_category(
    category_id: int,
    payload: CategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cat = db.query(Category).filter(
        Category.category_id == category_id,
        Category.user_id == current_user.user_id,
    ).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    cat.name = payload.name
    db.commit()
    db.refresh(cat)
    return cat


@router.delete("/{category_id}", status_code=204)
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cat = db.query(Category).filter(
        Category.category_id == category_id,
        Category.user_id == current_user.user_id,
    ).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    db.delete(cat)
    db.commit()
