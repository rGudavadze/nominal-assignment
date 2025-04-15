# QuickBooks Integration API

This application provides a REST API for integrating with QuickBooks Online using OAuth 2.0 authentication. It includes features for account management, token handling, and data caching.

## Features

- OAuth 2.0 authentication with QuickBooks Online
- Token management with automatic refresh
- Account data caching and synchronization
- Account filtering by name prefix
- Hierarchical account structure support
- Error handling and rate limiting
- PostgreSQL database for data persistence

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file with your QuickBooks credentials and database settings:
```
CLIENT_ID=your_client_id
CLIENT_SECRET=your_client_secret
REDIRECT_URI=http://localhost:8000/callback

# Database settings
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432
DB_NAME=quickbooks
```

4. Set up the PostgreSQL database:
```bash
# Create the database
createdb quickbooks

# Initialize the database tables
python -m app.init_db
```

5. Run the application:
```bash
uvicorn app.main:app --reload
```

## API Endpoints

- `GET /login` - Initiates the OAuth login flow
- `GET /callback` - Handles the OAuth callback
- `GET /accounts` - Retrieves accounts (with optional name prefix filter)
- `GET /health` - Health check endpoint

## Usage

1. Visit `http://localhost:8000/login` to start the authentication process
2. After successful authentication, you can access the accounts endpoint:
   - `http://localhost:8000/accounts` - Get all accounts
   - `http://localhost:8000/accounts?name_prefix=Asset` - Get accounts with name prefix

## Data Model

### Account
- `qbo_id`: QuickBooks account ID
- `name`: Account name
- `classification`: Account classification
- `currency_ref`: Currency reference
- `account_type`: Account type
- `active`: Account status
- `current_balance`: Current balance
- `parent_id`: Parent account ID (for hierarchical structure)
- `last_synced_at`: Last synchronization timestamp

## Error Handling

The API includes comprehensive error handling for:
- Authentication failures
- Token expiration and refresh
- Rate limiting
- Invalid requests
- Server errors

## Caching

Account data is cached in the PostgreSQL database and automatically synchronized:
- Initial sync on first request
- Subsequent syncs after 1 hour
- Manual sync available through the API 