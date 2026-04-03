"""
Export endpoints.
"""

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from database.session import get_db
from services import transaction_service as svc
from services.auth import require_role

router = APIRouter(prefix="/export", tags=["Export"])

@router.get(
    "/csv",
    dependencies=[Depends(require_role("viewer"))],
    summary="Export all transactions to CSV",
)
def export_csv(db: Session = Depends(get_db)):
    """
    **Roles required:** viewer, analyst, admin

    Streams all transactions as a CSV file to the client.
    """
    return StreamingResponse(
        svc.export_transactions_csv(db),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="transactions.csv"'},
    )
