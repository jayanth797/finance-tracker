"""
Pydantic schemas for Transaction request/response validation.

Design note:
  The ORM model uses `type` as the column name, but `type` is a Python
  built-in that Pydantic v2 can conflict with when used as a bare annotation.
  We call the Pydantic field `transaction_type` and give it alias `type` so:
    • JSON body / response uses the key "type"
    • Python code uses .transaction_type
"""

from datetime import date as DateType
from decimal import Decimal
from typing import Literal, Optional, Generic, TypeVar
from pydantic import BaseModel, Field, validator

T = TypeVar("T")

class StandardResponse(BaseModel, Generic[T]):
    """Standard API response envelope."""
    success: bool = True
    data: Optional[T] = None
    message: Optional[str] = None


# ── Shared base ───────────────────────────────────────────────────────────────

class TransactionBase(BaseModel):
    """
    Shared base for create / response schemas.
    `populate_by_name=True` accepts both the alias ("type") and the
    Python attribute name ("transaction_type") during validation.
    """
    class Config:
        orm_mode = True
        allow_population_by_field_name = True

    amount: Decimal = Field(..., description="Transaction amount (must be > 0)")
    transaction_type: Literal["income", "expense"] = Field(
        ...,
        alias="type",
        description="income or expense",
    )
    category: str = Field(..., min_length=1, max_length=100, description="e.g. Salary, Food")
    date: DateType = Field(..., description="Transaction date (YYYY-MM-DD)")
    notes: Optional[str] = Field(None, max_length=500, description="Optional notes")

    @validator("amount")
    @classmethod
    def amount_must_be_positive(cls, value: Decimal) -> Decimal:
        if value <= 0:
            raise ValueError("Transaction amount must be strictly greater than zero.")
        return value


# ── Request schemas ───────────────────────────────────────────────────────────

class TransactionCreate(TransactionBase):
    """Payload for creating a new transaction."""
    pass


class TransactionUpdate(BaseModel):
    """
    Payload for partially updating a transaction (PATCH semantics).
    All fields are optional — only provided fields are applied.
    """
    class Config:
        orm_mode = True
        allow_population_by_field_name = True

    amount: Optional[Decimal] = Field(None, description="New amount (must be > 0)")
    transaction_type: Optional[Literal["income", "expense"]] = Field(
        None,
        alias="type",
    )
    category: Optional[str] = Field(None, min_length=1, max_length=100)
    date: Optional[DateType] = None
    notes: Optional[str] = Field(None, max_length=500)

    @validator("amount")
    @classmethod
    def amount_must_be_positive(cls, value: Optional[Decimal]) -> Optional[Decimal]:
        if value is not None and value <= 0:
            raise ValueError("Transaction amount must be strictly greater than zero.")
        return value


# ── Response schemas ──────────────────────────────────────────────────────────

class TransactionResponse(TransactionBase):
    """Full transaction as returned by the API (inherits from_attributes=True)."""
    id: int


class PaginatedTransactionsResponse(BaseModel):
    """Paginated list of transactions."""
    total: int
    page: int
    limit: int
    items: list[TransactionResponse]


# ── Analytics schemas ─────────────────────────────────────────────────────────

class SummaryResponse(BaseModel):
    total_income: Decimal
    total_expense: Decimal
    balance: Decimal


class MonthlyBreakdown(BaseModel):
    year: int
    month: int
    total_income: Decimal
    total_expense: Decimal
    balance: Decimal


class CategoryBreakdown(BaseModel):
    class Config:
        allow_population_by_field_name = True

    category: str
    transaction_type: str = Field(..., alias="type")
    total: Decimal
    count: int

class TopCategoryResponse(BaseModel):
    category: str
    total: Decimal


class DashboardResponse(BaseModel):
    """Aggregate dashboard metrics."""
    total_income: Decimal
    total_expense: Decimal
    balance: Decimal
    top_category: Optional[TopCategoryResponse]
    highest_transaction: Optional[TransactionResponse]
    recent_summary: SummaryResponse
