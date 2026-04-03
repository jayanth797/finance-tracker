"""
SQLAlchemy ORM model for the transactions table.
"""

from sqlalchemy import Column, Integer, String, Numeric, Date, Text, Enum as SAEnum
from database.connection import Base


class Transaction(Base):
    """Represents a financial transaction (income or expense)."""

    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    amount = Column(Numeric(precision=12, scale=2), nullable=False)
    type = Column(SAEnum("income", "expense", name="transaction_type"), nullable=False)
    category = Column(String(100), nullable=False)
    date = Column(Date, nullable=False)
    notes = Column(Text, nullable=True)
