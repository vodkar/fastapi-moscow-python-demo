# Wallet API Implementation

This document describes the wallet and transaction functionality implemented as per the task requirements.

## Features Implemented

### Models

#### Wallet Model
- `id`: UUID primary key
- `user_id`: Foreign key to User (with CASCADE delete)
- `balance`: Decimal with 2 decimal places precision (starts at 0.00)
- `currency`: Enum (USD, EUR, RUB)

#### Transaction Model
- `id`: UUID primary key
- `wallet_id`: Foreign key to Wallet (with CASCADE delete)
- `amount`: Decimal with 2 decimal places
- `type`: Enum ('credit', 'debit')
- `timestamp`: DateTime with UTC timezone
- `currency`: Enum (USD, EUR, RUB)

### Business Rules

#### Wallet Rules
- A user can have maximum 3 wallets
- Wallet balance starts at 0.0
- Arithmetic operations maintain 2 decimal place precision
- Each user can have only one wallet per currency

#### Transaction Rules
- Credit transactions add amount to wallet balance
- Debit transactions subtract amount from wallet balance
- Wallet balance cannot go negative (debit transactions are rejected if insufficient balance)
- Currency conversion between different wallet currencies is supported with hardcoded exchange rates
- 2% conversion fee applied for cross-currency transactions

### API Endpoints

#### Create Wallet
```http
POST /wallets
Content-Type: application/json

{
  "currency": "USD"
}
```

**Response**: WalletPublic object with wallet details

#### Get User Wallets
```http
GET /wallets
```

**Response**: List of all wallets for the authenticated user

#### Get Wallet Details
```http
GET /wallets/{wallet_id}
```

**Response**: Wallet details including current balance

#### Create Transaction
```http
POST /wallets/{wallet_id}/transactions
Content-Type: application/json

{
  "amount": 100.50,
  "type": "credit",
  "currency": "USD"
}
```

**Response**: Transaction details

#### Get Wallet Transactions
```http
GET /wallets/{wallet_id}/transactions?skip=0&limit=100
```

**Response**: List of transactions for the wallet, ordered by timestamp (newest first)

### Exchange Rates

The following hardcoded exchange rates are used for currency conversion:

- USD to EUR: 0.85
- USD to RUB: 75.00
- EUR to USD: 1.18
- EUR to RUB: 88.24
- RUB to USD: 0.013
- RUB to EUR: 0.011

### Error Handling

The API includes proper error handling for:
- Maximum wallet limit exceeded
- Duplicate currency wallets for same user
- Insufficient balance for debit transactions
- Unsupported currency conversions
- Wallet not found or access denied

### Database Migration

A database migration has been created to add the new Wallet and Transaction tables with proper foreign key constraints and indexes.

### Authentication

All endpoints require user authentication and only allow access to wallets owned by the authenticated user.