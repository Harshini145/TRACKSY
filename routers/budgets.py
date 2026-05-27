from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel

from core.database import get_db
from core.security import get_current_user
from models.user import MonthlyBudget, CategoryBudget, Expense, Category, User

router = APIRouter(prefix="/budgets", tags=["Budgets"])


# ── Schemas ───────────────────────────────────────────────────────────────────

class MonthlyBudgetUpsert(BaseModel):
    month: int
    year: int
    amount: float


class CategoryBudgetUpsert(BaseModel):
    category_id: int
    month: int
    year: int
    amount: float


# ── Monthly budget ────────────────────────────────────────────────────────────

@router.post("/monthly", status_code=201)
def upsert_monthly_budget(
    payload: MonthlyBudgetUpsert,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing = db.query(MonthlyBudget).filter(
        MonthlyBudget.user_id == current_user.user_id,
        MonthlyBudget.month == payload.month,
        MonthlyBudget.year == payload.year,
    ).first()

    if existing:
        existing.amount = payload.amount
        db.commit()
        db.refresh(existing)
        return existing
    else:
        budget = MonthlyBudget(
            user_id=current_user.user_id,
            month=payload.month,
            year=payload.year,
            amount=payload.amount,
        )
        db.add(budget)
        db.commit()
        db.refresh(budget)
        return budget


@router.get("/monthly")
def get_monthly_budget(
    month: int,
    year: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Returns budget + how much is spent + remaining for the month."""
    budget = db.query(MonthlyBudget).filter(
        MonthlyBudget.user_id == current_user.user_id,
        MonthlyBudget.month == month,
        MonthlyBudget.year == year,
    ).first()

    spent = (
        db.query(func.sum(Expense.amount))
        .filter(
            Expense.user_id == current_user.user_id,
            func.month(Expense.expense_date) == month,
            func.year(Expense.expense_date) == year,
        )
        .scalar()
    ) or 0

    budget_amount = float(budget.amount) if budget else 0
    spent = float(spent)

    return {
        "month": month,
        "year": year,
        "budget": budget_amount,
        "spent": spent,
        "remaining": budget_amount - spent,
        "percent_used": round((spent / budget_amount * 100), 1) if budget_amount > 0 else 0,
    }


# ── Category budget ───────────────────────────────────────────────────────────

@router.post("/category", status_code=201)
def upsert_category_budget(
    payload: CategoryBudgetUpsert,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cat = db.query(Category).filter(
        Category.category_id == payload.category_id,
        Category.user_id == current_user.user_id,
    ).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")

    existing = db.query(CategoryBudget).filter(
        CategoryBudget.user_id == current_user.user_id,
        CategoryBudget.category_id == payload.category_id,
        CategoryBudget.month == payload.month,
        CategoryBudget.year == payload.year,
    ).first()

    if existing:
        existing.amount = payload.amount
        db.commit()
        db.refresh(existing)
        return existing

    cb = CategoryBudget(
        user_id=current_user.user_id,
        category_id=payload.category_id,
        month=payload.month,
        year=payload.year,
        amount=payload.amount,
    )
    db.add(cb)
    db.commit()
    db.refresh(cb)
    return cb


@router.get("/category")
def get_category_budgets(
    month: int,
    year: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rows = db.query(CategoryBudget).filter(
        CategoryBudget.user_id == current_user.user_id,
        CategoryBudget.month == month,
        CategoryBudget.year == year,
    ).all()

    result = []
    for row in rows:
        cat = db.query(Category).filter(Category.category_id == row.category_id).first()
        spent = (
            db.query(func.sum(Expense.amount))
            .filter(
                Expense.user_id == current_user.user_id,
                Expense.category_id == row.category_id,
                func.month(Expense.expense_date) == month,
                func.year(Expense.expense_date) == year,
            )
            .scalar()
        ) or 0

        budget_amount = float(row.amount)
        spent = float(spent)
        result.append({
            "category_id": row.category_id,
            "category_name": cat.name if cat else None,
            "budget": budget_amount,
            "spent": spent,
            "remaining": budget_amount - spent,
            "percent_used": round((spent / budget_amount * 100), 1) if budget_amount > 0 else 0,
        })

    return result
