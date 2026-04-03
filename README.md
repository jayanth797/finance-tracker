# Finance Tracker API

A production-ready FastAPI backend for tracking personal or business finances.

## Architecture & Structure
This project maintains a highly modular layout optimized for readability and scalability:

```
├── main.py                # Application entry point and router attachments
├── database/              # DB connection and session configuration
├── models/                # SQLAlchemy models (Database Tables)
├── schemas/               # Pydantic schemas (Request/Response contracts)
├── routes/                # FastAPI routing logic mapped by domains
├── services/              # Business logic decoupling
├── requirements.txt       # Core project dependencies 
```

## Features
- **Categorical Transactions**: Modular, full CRUD for income/expense data records.
- **Analytics Dashboard**: Efficient querying endpoints for retrieving standard reporting heuristics (e.g., aggregators over recent rolling periods).
- **Lightweight Authentication**: Implemented via simple, modular OAuth2 JWT mappings over an access-role hierarchy tree (`viewer`, `analyst`, `admin`).
- **Standardized Responses**: Securely standardized request layouts and strictly unified JSON error responses wrapped natively within custom exception overrides.

## Setting Up
1. Clone the repository and navigate inside:
   ```bash
   cd finance-tracker
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Start the server (creates SQLite database `finance_tracker.db` automatically):
   ```bash
   uvicorn main:app --reload
   ```

## API Documentation
The fully interactive OpenAPI integration is actively deployed by FastAPI when spinning up the project. Once the server runs, visit `http://127.0.0.1:8000/docs` to examine the full API ecosystem or manually authorize token generations.
