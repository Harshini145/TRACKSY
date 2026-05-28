from datetime import date as date_type, datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from pydantic import BaseModel

from core.database import get_db
from core.security import get_current_user
from models.user import Expense, Category, User
from services.budget_service import check_budget_for_user

router = APIRouter(prefix="/expenses", tags=["Expenses"])


# ── Schemas ───────────────────────────────────────────────────────────────────

class ExpenseCreate(BaseModel):
    category_id: Optional[int] = None
    description: Optional[str] = None
    amount: float
    expense_date: date_type


class ExpenseUpdate(BaseModel):
    category_id: Optional[int] = None
    description: Optional[str] = None
    amount: Optional[float] = None
    expense_date: Optional[date_type] = None


class ExpenseOut(BaseModel):
    expense_id: int
    category_id: Optional[int]
    category_name: Optional[str]
    description: Optional[str]
    amount: float
    expense_date: date_type
    created_at: datetime

    class Config:
        from_attributes = True


# ── Helpers ───────────────────────────────────────────────────────────────────

def _enrich(expense: Expense, db: Session) -> dict:
    cat_name = None
    if expense.category_id:
        cat = db.query(Category).filter(Category.category_id == expense.category_id).first()
        cat_name = cat.name if cat else None
    return {
        "expense_id": expense.expense_id,
        "category_id": expense.category_id,
        "category_name": cat_name,
        "description": expense.description,
        "amount": float(expense.amount),
        "expense_date": expense.expense_date,
        "created_at": expense.created_at,
    }


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post("/", status_code=201)
async def add_expense(
    payload: ExpenseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if payload.category_id:
        cat = db.query(Category).filter(
            Category.category_id == payload.category_id,
            Category.user_id == current_user.user_id,
        ).first()
        if not cat:
            raise HTTPException(status_code=404, detail="Category not found")

    expense = Expense(
        user_id=current_user.user_id,
        category_id=payload.category_id,
        description=payload.description,
        amount=payload.amount,
        expense_date=payload.expense_date,
    )
    db.add(expense)
    db.commit()
    db.refresh(expense)

    # ── Real-time budget check ──────────────────────────────────────────────
    try:
        await check_budget_for_user(
            db,
            current_user.user_id,
            payload.expense_date.month,
            payload.expense_date.year,
        )
    except Exception:
        pass  # Never block the expense save because of email failure

    return _enrich(expense, db)


@router.get("/", response_model=List[dict])
def list_expenses(
    month: Optional[int] = None,
    year: Optional[int] = None,
    category_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(Expense).filter(Expense.user_id == current_user.user_id)
    if month:
        q = q.filter(func.month(Expense.expense_date) == month)
    if year:
        q = q.filter(func.year(Expense.expense_date) == year)
    if category_id:
        q = q.filter(Expense.category_id == category_id)

    expenses = q.order_by(Expense.expense_date.desc()).all()
    return [_enrich(e, db) for e in expenses]


@router.get("/summary")
def monthly_summary(
    month: int,
    year: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Total spent + per-category breakdown for a given month."""
    total = (
        db.query(func.sum(Expense.amount))
        .filter(
            Expense.user_id == current_user.user_id,
            func.month(Expense.expense_date) == month,
            func.year(Expense.expense_date) == year,
        )
        .scalar()
    ) or 0

    by_category = (
        db.query(Category.name, func.sum(Expense.amount).label("total"))
        .join(Expense, Expense.category_id == Category.category_id)
        .filter(
            Expense.user_id == current_user.user_id,
            func.month(Expense.expense_date) == month,
            func.year(Expense.expense_date) == year,
        )
        .group_by(Category.category_id)
        .all()
    )

    return {
        "month": month,
        "year": year,
        "total_spent": float(total),
        "by_category": [{"category": r[0], "spent": float(r[1])} for r in by_category],
    }


@router.get("/{expense_id}")
def get_expense(
    expense_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    expense = db.query(Expense).filter(
        Expense.expense_id == expense_id,
        Expense.user_id == current_user.user_id,
    ).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    return _enrich(expense, db)


@router.put("/{expense_id}")
async def update_expense(
    expense_id: int,
    payload: ExpenseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    expense = db.query(Expense).filter(
        Expense.expense_id == expense_id,
        Expense.user_id == current_user.user_id,
    ).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")

    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(expense, field, value)
    db.commit()
    db.refresh(expense)

    # Re-check budget after update
    check_month  = expense.expense_date.month
    check_year   = expense.expense_date.year
    try:
        await check_budget_for_user(db, current_user.user_id, check_month, check_year)
    except Exception:
        pass

    return _enrich(expense, db)


@router.delete("/{expense_id}", status_code=204)
def delete_expense(
    expense_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    expense = db.query(Expense).filter(
        Expense.expense_id == expense_id,
        Expense.user_id == current_user.user_id,
    ).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    db.delete(expense)
    db.commit()
