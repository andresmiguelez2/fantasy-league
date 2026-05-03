# fantasy-league

A fantasy football league application with user authentication.

## Features

- JWT-based user authentication (login/logout)
- Protected routes for authenticated users only
- Player management and squad selection
- Market bidding system
- Real-time leaderboard

## Project Structure

```
app/
├── main.py              # Application entry point (uvicorn target)
├── api/                 # FastAPI routers and route handlers
│   ├── app.py           # FastAPI app factory and middleware
│   ├── deps.py          # Shared dependencies (e.g. auth guard)
│   └── routes/          # Individual resource routers
│       ├── auth.py
│       ├── footballers.py
│       ├── general.py
│       ├── leaderboard.py
│       ├── leagues.py
│       ├── market.py
│       ├── players.py
│       ├── squads.py
│       └── teams.py
├── core/                # Core configuration and utilities
│   ├── config.py        # Application constants
│   ├── logging.py       # Logging setup
│   └── security.py      # JWT auth and password hashing
├── db/                  # Database layer
│   └── session.py       # PostgreSQL and MongoDB connection helpers
├── models/              # Domain model classes
│   ├── bid.py
│   ├── fixture.py
│   ├── footballer.py
│   ├── league.py
│   ├── market.py
│   └── player.py
├── utils/               # Shared utility functions
│   └── scraper.py       # Web scraping helpers
├── workers/             # Background task runners
│   └── background.py    # Async background loop (market/fixture processing)
├── scripts/             # One-off admin and setup scripts
│   ├── insert_fixtures.py
│   ├── insert_footballers.py
│   └── setup_db.py
└── frontend/            # React/Vite frontend application
```

## Documentation

- [Authentication Setup Guide](docs/AUTHENTICATION.md) - Complete guide for setting up and using JWT authentication

## Quick Start

See the [Authentication Setup Guide](docs/AUTHENTICATION.md) for detailed setup instructions.
