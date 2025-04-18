# Nominal - QuickBooks Integration Service

A FastAPI-based service that integrates with QuickBooks API to manage accounts and sync data.

## Features

- OAuth2 authentication with QuickBooks
- Account synchronization with QuickBooks
- RESTful API endpoints
- PostgreSQL database integration
- Comprehensive test suite
- Docker support for easy deployment

## Prerequisites

- Python 3.12+
- PostgreSQL
- Docker and Docker Compose (for containerized deployment)
- QuickBooks Developer Account

## Local Development Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd nominal
```

2. Build the Docker image:
```bash
docker build -t nominal .
```

3. Run with Docker Compose:
```bash
docker-compose up -d
```

The application will be available at `http://localhost:8000`

## API Documentation

Once the application is running, you can access:
- Swagger UI: `http://localhost:8000/docs`

### API Endpoints

#### Authentication Endpoints

- `GET /login`
  - Initiates the OAuth2 authentication flow with QuickBooks
  - Redirects to QuickBooks authorization page
  - No authentication required

- `GET /callback`
  - Handles the OAuth2 callback from QuickBooks
  - Required query parameters:
    - `code`: Authorization code from QuickBooks
    - `realmId`: QuickBooks realm ID
  - Returns:
    - Success: JSON with authentication status and tokens
    - Error: 400 Bad Request with error details

#### Account Endpoints

- `GET /accounts`
  - Retrieves all accounts from QuickBooks
  - Optional query parameters:
    - `name_prefix`: Filter accounts by name prefix
    - `from_api`: Force synchronization with QuickBooks (default: false)
  - Returns:
    - Success: List of accounts with their details
    - Error: 400 Bad Request or 401 Unauthorized

## Testing

### Running Tests in Docker

```bash
docker compose run api python run_tests.py
```

## Project Structure

```
app/
├── api/            # API endpoints
├── config/         # Configuration files
├── database/       # Database setup
├── models/         # SQLAlchemy models
├── schemas/        # Pydantic schemas
├── services/       # Business logic
├── tests/          # Test files
└── utils/          # Utility functions
```
