"""
Budget alert service.

Called:
  • Every time a new expense is added  (real-time check)
  • By the APScheduler job once per hour  (catch-all)

Logic:
  1. If spent >= budget                → "exceeded" alert  (type='alert')
  2. If spent >= WARNING_PERCENT * budget → "warning" alert (type='warning')

We store each sent alert type in the Notifications table so we never spam
the same email twice per month per threshold.
"""

from datetime import datetime
from decimal import Decimal

from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from core.config import settings
from models.user import Expense, MonthlyBudget, Notification, User
from services.email_service import send_budget_warning_email, send_budget_exceeded_email

import calendar


def _month_name(month: int, year: int) -> str:
    return f"{calendar.month_name[month]} {year}"


def _already_notified(db: Session, user_id: int, month: int, year: int, notif_type: str) -> bool:
    """Check if we already sent this type of notification this month."""
    tag = f"[{year}-{month:02d}:{notif_type}]"
    existing = (
        db.query(Notification)
        .filter(
            Notification.user_id == user_id,
            Notification.type == notif_type,
            Notification.message.contains(tag),
        )
        .first()
    )
    return existing is not None


def _record_notification(db: Session, user_id: int, month: int, year: int, notif_type: str, message: str):
    tag = f"[{year}-{month:02d}:{notif_type}]"
    notif = Notification(user_id=user_id, message=f"{tag} {message}", type=notif_type)
    db.add(notif)
    db.commit()


async def check_budget_for_user(db: Session, user_id: int, month: int, year: int):
    """Run budget check for a single user for the given month/year."""

    budget_row = (
        db.query(MonthlyBudget)
        .filter(
            MonthlyBudget.user_id == user_id,
            MonthlyBudget.month == month,
            MonthlyBudget.year == year,
        )
        .first()
    )
    if not budget_row or not budget_row.amount:
        return  # No budget set — nothing to check

    budget = float(budget_row.amount)

    # Total spent this month
    total_spent_row = (
        db.query(func.sum(Expense.amount))
        .filter(
            Expense.user_id == user_id,
            func.month(Expense.expense_date) == month,
            func.year(Expense.expense_date) == year,
        )
        .scalar()
    )
    spent = float(total_spent_row or 0)
    percent = (spent / budget * 100) if budget > 0 else 0
    month_label = _month_name(month, year)

    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        return

    # ── EXCEEDED ─────────────────────────────────────────────────────────────
    if spent >= budget:
        if not _already_notified(db, user_id, month, year, "alert"):
            over_by = spent - budget
            await send_budget_exceeded_email(
                to_email=user.email,
                username=user.username,
                spent=spent,
                budget=budget,
                month=month_label,
                over_by=over_by,
            )
            _record_notification(
                db, user_id, month, year, "alert",
                f"Budget exceeded for {month_label}. Spent ₹{spent:.2f} / ₹{budget:.2f}."
            )
        return  # Don't send warning if already exceeded

    # ── WARNING (approaching) ─────────────────────────────────────────────────
    if percent >= settings.BUDGET_WARNING_PERCENT:
        if not _already_notified(db, user_id, month, year, "warning"):
            await send_budget_warning_email(
                to_email=user.email,
                username=user.username,
                spent=spent,
                budget=budget,
                month=month_label,
                percent=percent,
            )
            _record_notification(
                db, user_id, month, year, "warning",
                f"Budget warning for {month_label}. Spent ₹{spent:.2f} ({percent:.1f}%) of ₹{budget:.2f}."
            )


async def run_budget_checks_for_all_users(db: Session):
    """Scheduled job — runs for all users for the current month."""
    now = datetime.now()
    month, year = now.month, now.year

    # Only check users who have a budget set this month
    budget_rows = (
        db.query(MonthlyBudget)
        .filter(MonthlyBudget.month == month, MonthlyBudget.year == year)
        .all()
    )
    for row in budget_rows:
        await check_budget_for_user(db, row.user_id, month, year)
