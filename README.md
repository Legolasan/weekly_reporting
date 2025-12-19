# Work Tracker

A FastAPI web application for tracking weekly work activities using a 100-point system.

## Features

- **Dashboard**: Current week summary with pending/delayed tasks from previous weeks
- **Input**: Add and manage work items for any week
- **Analytics**: Charts for points trend, task distribution, completion rates
- **Reports**: View and export data to Excel/CSV

## Task Types

- **Planned**: Pre-scheduled work items
- **Unplanned**: Work that comes up during the week
- **Ad-Hoc**: Miscellaneous tasks

## Points System

- Each work week (Mon-Fri) has 100 total points
- 20 points per day
- Points are allocated across all task types

## Setup

### 1. Create virtual environment

```bash
cd work-tracker
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure database

Copy `sample.env` to `.env` and update with your Railway PostgreSQL connection string:

```bash
cp sample.env .env
# Edit .env with your Railway PostgreSQL URL
```

**Railway PostgreSQL Setup:**
1. Go to [Railway](https://railway.app)
2. Create a new project
3. Add PostgreSQL service
4. Copy the connection string from the Variables tab
5. Paste it as `DATABASE_URL` in your `.env` file

### 4. Run database migrations

```bash
alembic upgrade head
```

### 5. Start the application

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Visit `http://localhost:8000` in your browser.

## Railway Deployment

To deploy on Railway:

1. Push your code to GitHub
2. Connect your repo to Railway
3. Add PostgreSQL service
4. Set environment variable: `DATABASE_URL` (auto-configured if using Railway PostgreSQL)
5. Railway will auto-deploy on push

## Project Structure

```
work-tracker/
├── app/
│   ├── main.py           # FastAPI application
│   ├── config.py         # Settings
│   ├── database.py       # SQLAlchemy setup
│   ├── models/           # Database models
│   ├── schemas/          # Pydantic schemas
│   ├── crud/             # Database operations
│   ├── routers/          # API routes
│   ├── services/         # Business logic
│   ├── templates/        # Jinja2 HTML templates
│   └── static/           # CSS, JS assets
├── alembic/              # Database migrations
├── requirements.txt
└── README.md
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Dashboard |
| GET | `/input` | Input page (current week) |
| GET | `/input/{week_start}` | Input page for specific week |
| POST | `/api/work-items` | Create work item |
| PUT | `/api/work-items/{id}` | Update work item |
| DELETE | `/api/work-items/{id}` | Delete work item |
| GET | `/analytics` | Analytics page |
| GET | `/reports` | Reports page |
| GET | `/reports/export/csv` | Export to CSV |
| GET | `/reports/export/excel` | Export to Excel |
