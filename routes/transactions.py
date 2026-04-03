"""
Transaction CRUD endpoints.

All business logic is delegated to services/transaction_service.py.
Role enforcement:
  - GET   → viewer+
  - POST  → admin only
  - PUT   → admin only
  - DELETE→ admin only
"""

from datetime import date
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from database.session import get_db
from schemas.transaction import (
    PaginatedTransactionsResponse,
    TransactionCreate,
    TransactionResponse,
    TransactionUpdate,
    StandardResponse,
)
from services import transaction_service as svc
from services.auth import require_role

router = APIRouter(prefix="/transactions", tags=["Transactions"])


# ── Create ────────────────────────────────────────────────────────────────────

@router.post(
    "/",
    response_model=StandardResponse[TransactionResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role("admin"))],
    summary="Create a new transaction",
)
def create_transaction(
    payload: TransactionCreate,
    db: Session = Depends(get_db),
):
    """
    **Roles required:** admin

    Create a new income or expense transaction.
    Amount must be a positive decimal value.
    """
    tx = svc.create_transaction(db, payload)
    return StandardResponse(data=tx, message="Transaction created successfully.")


# ── Read (list) ───────────────────────────────────────────────────────────────

@router.get(
    "/",
    response_model=StandardResponse[PaginatedTransactionsResponse],
    dependencies=[Depends(require_role("viewer"))],
    summary="List transactions with optional filters",
)
def list_transactions(
    tx_type: Annotated[Optional[str], Query(alias="type", description="income | expense")] = None,
    category: Annotated[Optional[str], Query(description="Filter by category (partial match)")] = None,
    start_date: Annotated[Optional[date], Query(description="Start of date range (YYYY-MM-DD)")] = None,
    end_date: Annotated[Optional[date], Query(description="End of date range (YYYY-MM-DD)")] = None,
    page: Annotated[int, Query(ge=1, description="Page number (1-indexed)")] = 1,
    limit: Annotated[int, Query(ge=1, le=100, description="Items per page (max 100)")] = 10,
    db: Session = Depends(get_db),
):
    """
    **Roles required:** viewer, analyst, admin

    Returns a paginated list of transactions.
    Supports filtering by type, category, and date range.
    """
    if tx_type and tx_type not in ("income", "expense"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query parameter 'type' must be 'income' or 'expense'.",
        )
    if start_date and end_date and start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start_date must not be later than end_date.",
        )

    total, items = svc.get_transactions(
        db,
        tx_type=tx_type,
        category=category,
        start_date=start_date,
        end_date=end_date,
        page=page,
        limit=limit,
    )
    res = PaginatedTransactionsResponse(
        total=total,
        page=page,
        limit=limit,
        items=items,
    )
    return StandardResponse(data=res, message="Transactions retrieved successfully.")


# ── Read (single) ─────────────────────────────────────────────────────────────

@router.get(
    "/{tx_id}",
    response_model=StandardResponse[TransactionResponse],
    dependencies=[Depends(require_role("viewer"))],
    summary="Get a single transaction by ID",
)
def get_transaction(tx_id: int, db: Session = Depends(get_db)):
    """**Roles required:** viewer, analyst, admin"""
    tx = svc.get_transaction_by_id(db, tx_id)
    if not tx:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction with id={tx_id} not found.",
        )
    return StandardResponse(data=tx, message="Transaction retrieved successfully.")


# ── Update ────────────────────────────────────────────────────────────────────

@router.patch(
    "/{tx_id}",
    response_model=StandardResponse[TransactionResponse],
    dependencies=[Depends(require_role("admin"))],
    summary="Partially update a transaction",
)
def update_transaction(
    tx_id: int,
    payload: TransactionUpdate,
    db: Session = Depends(get_db),
):
    """
    **Roles required:** admin

    Partially update any fields of a transaction.
    Only provided fields are modified (PATCH semantics).
    """
    tx = svc.get_transaction_by_id(db, tx_id)
    if not tx:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction with id={tx_id} not found.",
        )
    updated_tx = svc.update_transaction(db, tx, payload)
    return StandardResponse(data=updated_tx, message="Transaction updated successfully.")


# ── Delete ────────────────────────────────────────────────────────────────────

@router.delete(
    "/{tx_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_role("admin"))],
    summary="Delete a transaction",
)
def delete_transaction(tx_id: int, db: Session = Depends(get_db)):
    """
    **Roles required:** admin

    Permanently deletes a transaction. Returns 204 No Content on success.
    """
    tx = svc.get_transaction_by_id(db, tx_id)
    if not tx:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction with id={tx_id} not found.",
        )
    svc.delete_transaction(db, tx)
