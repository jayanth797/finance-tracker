"""
Business logic for Transaction CRUD and analytics.
All DB interactions happen here; routes stay thin.
"""

from datetime import date
from decimal import Decimal
from typing import Optional

from sqlalchemy import func, extract
from sqlalchemy.orm import Session

from models.transaction import Transaction
from schemas.transaction import (
    TransactionCreate,
    TransactionUpdate,
    SummaryResponse,
    MonthlyBreakdown,
    CategoryBreakdown,
)


# ── CRUD ──────────────────────────────────────────────────────────────────────

def create_transaction(db: Session, payload: TransactionCreate) -> Transaction:
    """Insert a new transaction row and return the persisted object."""
    data = payload.model_dump(by_alias=False)
    # Pydantic field is `transaction_type`; ORM column is `type`
    data["type"] = data.pop("transaction_type")
    tx = Transaction(**data)
    db.add(tx)
    db.commit()
    db.refresh(tx)
    return tx


def get_transactions(
    db: Session,
    *,
    tx_type: Optional[str] = None,
    category: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    page: int = 1,
    limit: int = 10,
) -> tuple[int, list[Transaction]]:
    """
    Return (total_count, page_of_transactions) with optional filters.
    Supports type, category, and date-range filtering plus pagination.
    """
    query = db.query(Transaction)

    if tx_type:
        query = query.filter(Transaction.type == tx_type)
    if category:
        query = query.filter(Transaction.category.ilike(f"%{category}%"))
    if start_date:
        query = query.filter(Transaction.date >= start_date)
    if end_date:
        query = query.filter(Transaction.date <= end_date)

    total = query.count()
    items = (
        query.order_by(Transaction.date.desc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )
    return total, items


def get_transaction_by_id(db: Session, tx_id: int) -> Optional[Transaction]:
    """Fetch a single transaction by primary key, or None if not found."""
    return db.query(Transaction).filter(Transaction.id == tx_id).first()


def update_transaction(
    db: Session, tx: Transaction, payload: TransactionUpdate
) -> Transaction:
    """Partially update a transaction with only the provided fields."""
    update_data = payload.model_dump(exclude_unset=True, by_alias=False)
    # Map Pydantic's transaction_type → ORM's type column
    if "transaction_type" in update_data:
        update_data["type"] = update_data.pop("transaction_type")
    for field, value in update_data.items():
        setattr(tx, field, value)
    db.commit()
    db.refresh(tx)
    return tx


def delete_transaction(db: Session, tx: Transaction) -> None:
    """Permanently delete a transaction."""
    db.delete(tx)
    db.commit()


# ── Analytics ─────────────────────────────────────────────────────────────────

def get_summary(db: Session) -> SummaryResponse:
    """
    Return aggregate totals across all transactions.
    Uses SQL SUM with conditional grouping for performance.
    """
    rows = (
        db.query(
            Transaction.type,
            func.coalesce(func.sum(Transaction.amount), 0).label("total"),
        )
        .group_by(Transaction.type)
        .all()
    )

    totals = {row[0]: Decimal(str(row[1])) for row in rows}
    income = totals.get("income", Decimal("0"))
    expense = totals.get("expense", Decimal("0"))

    return SummaryResponse(
        total_income=income,
        total_expense=expense,
        balance=income - expense,
    )


def get_monthly_breakdown(db: Session) -> list[MonthlyBreakdown]:
    """
    Return income and expense totals grouped by year and month.
    Uses SQL GROUP BY with SUM aggregation.
    """
    rows = (
        db.query(
            extract("year", Transaction.date).label("year"),
            extract("month", Transaction.date).label("month"),
            Transaction.type,
            func.sum(Transaction.amount).label("total"),
        )
        .group_by("year", "month", Transaction.type)
        .order_by("year", "month")
        .all()
    )

    # Merge income and expense rows for the same year/month into one record
    buckets: dict[tuple[int, int], dict] = {}
    for row in rows:
        key = (int(row.year), int(row.month))
        if key not in buckets:
            buckets[key] = {"income": Decimal("0"), "expense": Decimal("0")}
        buckets[key][row[2]] = Decimal(str(row.total))  # row[2] = type

    return [
        MonthlyBreakdown(
            year=year,
            month=month,
            total_income=data["income"],
            total_expense=data["expense"],
            balance=data["income"] - data["expense"],
        )
        for (year, month), data in sorted(buckets.items())
    ]


def get_category_breakdown(db: Session) -> list[CategoryBreakdown]:
    """
    Return totals and counts grouped by category and type.
    Useful for pie/bar charts in frontends.
    """
    rows = (
        db.query(
            Transaction.category,
            Transaction.type,
            func.sum(Transaction.amount).label("total"),
            func.count(Transaction.id).label("count"),
        )
        .group_by(Transaction.category, Transaction.type)
        .order_by(Transaction.type, Transaction.category)
        .all()
    )

    return [
        CategoryBreakdown(
            category=row.category,
            type=row[1],   # type column, use alias
            total=Decimal(str(row.total)),
            count=row.count,
        )
        for row in rows
    ]


def get_top_category(db: Session) -> Optional[dict]:
    """Retrieve the category with the highest total expense."""
    row = (
        db.query(
            Transaction.category,
            func.sum(Transaction.amount).label("total")
        )
        .filter(Transaction.type == "expense")
        .group_by(Transaction.category)
        .order_by(func.sum(Transaction.amount).desc())
        .first()
    )
    if row:
        return {"category": row.category, "total": Decimal(str(row.total))}
    return None


def get_recent_summary(db: Session) -> SummaryResponse:
    """Calculate summary over the last 7 days."""
    import datetime
    seven_days_ago = datetime.date.today() - datetime.timedelta(days=7)
    
    rows = (
        db.query(
            Transaction.type,
            func.coalesce(func.sum(Transaction.amount), 0).label("total"),
        )
        .filter(Transaction.date >= seven_days_ago)
        .group_by(Transaction.type)
        .all()
    )

    totals = {row[0]: Decimal(str(row[1])) for row in rows}
    income = totals.get("income", Decimal("0"))
    expense = totals.get("expense", Decimal("0"))

    return SummaryResponse(
        total_income=income,
        total_expense=expense,
        balance=income - expense,
    )


def get_highest_transaction(db: Session) -> Optional[Transaction]:
    """Return the single transaction with the highest documented amount."""
    return db.query(Transaction).order_by(Transaction.amount.desc()).first()


def export_transactions_csv(db: Session):
    """
    Generator that yields CSV rows for all transactions.
    Fetches iteratively to avoid keeping large datasets in memory.
    """
    import csv
    import io
    
    # Send CSV header
    header = io.StringIO()
    writer = csv.writer(header)
    writer.writerow(["ID", "Amount", "Type", "Category", "Date", "Notes"])
    yield header.getvalue()
    
    query = db.query(Transaction).order_by(Transaction.date.desc())
    for chunk in query.yield_per(100):
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow([
            chunk.id,
            chunk.amount,
            chunk.type,
            chunk.category,
            chunk.date,
            chunk.notes or ""
        ])
        yield buffer.getvalue()


def get_dashboard(db: Session) -> dict:
    """
    Returns an aggregated dictionary comprising all dashboard metrics.
    """
    summary = get_summary(db)
    top_cat = get_top_category(db)
    highest_tx = get_highest_transaction(db)
    recent = get_recent_summary(db)
    
    return {
        "total_income": summary.total_income,
        "total_expense": summary.total_expense,
        "balance": summary.balance,
        "top_category": top_cat,
        "highest_transaction": highest_tx,
        "recent_summary": recent,
    }
