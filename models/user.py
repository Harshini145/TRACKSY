from sqlalchemy import (
    Column, Integer, String, Text, DECIMAL, Date,
    TIMESTAMP, ForeignKey, Enum, UniqueConstraint, func
)
from sqlalchemy.orm import relationship
from core.database import Base


class User(Base):
    __tablename__ = "Users"

    user_id    = Column(Integer, primary_key=True, autoincrement=True)
    username   = Column(String(50), nullable=False)
    email      = Column(String(100), unique=True, nullable=False)
    password   = Column(String(255), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())

    expenses         = relationship("Expense",         back_populates="user", cascade="all, delete")
    categories       = relationship("Category",        back_populates="user", cascade="all, delete")
    monthly_budgets  = relationship("MonthlyBudget",   back_populates="user", cascade="all, delete")
    category_budgets = relationship("CategoryBudget",  back_populates="user", cascade="all, delete")
    notifications    = relationship("Notification",    back_populates="user", cascade="all, delete")
    settings         = relationship("UserSetting",     back_populates="user", cascade="all, delete", uselist=False)


class Category(Base):
    __tablename__ = "Categories"

    category_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id     = Column(Integer, ForeignKey("Users.user_id", ondelete="CASCADE"))
    name        = Column(String(50))
    created_at  = Column(TIMESTAMP, server_default=func.now())

    user     = relationship("User",    back_populates="categories")
    expenses = relationship("Expense", back_populates="category")


class Expense(Base):
    __tablename__ = "Expenses"

    expense_id   = Column(Integer, primary_key=True, autoincrement=True)
    user_id      = Column(Integer, ForeignKey("Users.user_id", ondelete="CASCADE"))
    category_id  = Column(Integer, ForeignKey("Categories.category_id"))
    description  = Column(Text)
    amount       = Column(DECIMAL(10, 2))
    expense_date = Column(Date)
    created_at   = Column(TIMESTAMP, server_default=func.now())

    user     = relationship("User",     back_populates="expenses")
    category = relationship("Category", back_populates="expenses")


class MonthlyBudget(Base):
    __tablename__ = "Monthly_Budgets"

    budget_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id   = Column(Integer, ForeignKey("Users.user_id", ondelete="CASCADE"))
    month     = Column(Integer)
    year      = Column(Integer)
    amount    = Column(DECIMAL(10, 2))

    __table_args__ = (UniqueConstraint("user_id", "month", "year"),)

    user = relationship("User", back_populates="monthly_budgets")


class CategoryBudget(Base):
    __tablename__ = "Category_Budgets"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    user_id     = Column(Integer, ForeignKey("Users.user_id", ondelete="CASCADE"))
    category_id = Column(Integer, ForeignKey("Categories.category_id"))
    month       = Column(Integer)
    year        = Column(Integer)
    amount      = Column(DECIMAL(10, 2))

    user     = relationship("User",     back_populates="category_budgets")
    category = relationship("Category")


class UserSetting(Base):
    __tablename__ = "User_Settings"

    id      = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("Users.user_id", ondelete="CASCADE"))
    theme   = Column(String(20))

    user = relationship("User", back_populates="settings")


class Notification(Base):
    __tablename__ = "Notifications"

    notification_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id         = Column(Integer, ForeignKey("Users.user_id", ondelete="CASCADE"))
    message         = Column(Text)
    type            = Column(Enum("warning", "alert"))
    created_at      = Column(TIMESTAMP, server_default=func.now())

    user = relationship("User", back_populates="notifications")
