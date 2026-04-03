"""
Analytics endpoints: summary, monthly breakdown, category breakdown.
All endpoints are accessible to analyst and admin roles.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database.session import get_db
from schemas.transaction import (
    CategoryBreakdown,
    MonthlyBreakdown,
    SummaryResponse,
    TopCategoryResponse,
    TransactionResponse,
    DashboardResponse,
    StandardResponse,
)
from services import transaction_service as svc
from services.auth import require_role

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get(
    "/summary",
    response_model=StandardResponse[SummaryResponse],
    dependencies=[Depends(require_role("viewer"))],
    summary="Overall financial summary",
)
def summary(db: Session = Depends(get_db)):
    """
    **Roles required:** viewer, analyst, admin

    Returns aggregate totals:
    - `total_income`: sum of all income transactions
    - `total_expense`: sum of all expense transactions
    - `balance`: total_income − total_expense
    """
    data = svc.get_summary(db)
    return StandardResponse(data=data, message="Summary retrieved successfully.")


@router.get(
    "/monthly",
    response_model=StandardResponse[list[MonthlyBreakdown]],
    dependencies=[Depends(require_role("analyst"))],
    summary="Income & expense grouped by month",
)
def monthly_breakdown(db: Session = Depends(get_db)):
    """
    **Roles required:** analyst, admin

    Returns a list of monthly totals sorted chronologically.
    Each record contains year, month, income, expense, and balance.
    """
    data = svc.get_monthly_breakdown(db)
    return StandardResponse(data=data, message="Monthly breakdown retrieved successfully.")


@router.get(
    "/category",
    response_model=StandardResponse[list[CategoryBreakdown]],
    dependencies=[Depends(require_role("analyst"))],
    summary="Totals grouped by category and type",
)
def category_breakdown(db: Session = Depends(get_db)):
    """
    **Roles required:** analyst, admin

    Returns spending/income split by category.
    Useful for building pie or bar charts.
    """
    data = svc.get_category_breakdown(db)
    return StandardResponse(data=data, message="Category breakdown retrieved successfully.")


@router.get(
    "/top-category",
    response_model=StandardResponse[TopCategoryResponse],
    dependencies=[Depends(require_role("analyst"))],
    summary="Highest expense category",
)
def top_category(db: Session = Depends(get_db)):
    """Returns the top expense category with its total amount."""
    res = svc.get_top_category(db)
    from fastapi import HTTPException, status
    if not res:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No expenses found")
    return StandardResponse(data=res, message="Top category retrieved successfully.")


@router.get(
    "/recent",
    response_model=StandardResponse[SummaryResponse],
    dependencies=[Depends(require_role("viewer"))],
    summary="Last 7 days financial summary",
)
def recent_summary(db: Session = Depends(get_db)):
    """Summary of income and expenses over the past 7 days."""
    data = svc.get_recent_summary(db)
    return StandardResponse(data=data, message="Recent summary retrieved successfully.")


@router.get(
    "/highest",
    response_model=StandardResponse[TransactionResponse],
    dependencies=[Depends(require_role("viewer"))],
    summary="Highest single transaction",
)
def highest_transaction(db: Session = Depends(get_db)):
    """Returns the largest transaction recorded."""
    tx = svc.get_highest_transaction(db)
    from fastapi import HTTPException, status
    if not tx:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No transactions found")
    return StandardResponse(data=tx, message="Highest transaction retrieved successfully.")


@router.get(
    "/dashboard",
    response_model=StandardResponse[DashboardResponse],
    dependencies=[Depends(require_role("viewer"))],
    summary="Aggregate dashboard metrics",
)
def dashboard(db: Session = Depends(get_db)):
    """
    **Roles required:** viewer, analyst, admin

    Returns a combined payload including:
    total income, total expense, balance, top category, highest transaction, and recent summary.
    """
    data = svc.get_dashboard(db)
    return StandardResponse(data=DashboardResponse(**data), message="Dashboard retrieved successfully.")
