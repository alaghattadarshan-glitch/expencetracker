# Personal Expense Tracker

A full-stack, DevOps-engineered personal finance web application built with **HTML5, CSS3, Vanilla JavaScript, Python (Flask), MySQL, Docker, and Docker Compose**.

Designed to track daily income and expenses, monitor spending habits, manage monthly category budgets with automated threshold warnings (80% / 100%), and analyze financial trends through charts and key performance indicators.

---

## 📸 Overview & Key Highlights

- **Frontend:** Pure HTML5, CSS3, and Vanilla JavaScript (ES6+) with zero bloated client libraries. Uses Chart.js for data visualization.
- **Backend:** Modular Python Flask architecture organized into blueprints with parameter-sanitized SQL queries.
- **Database:** Production-grade MySQL 8.0 relational schema with connection pooling, indexes, foreign keys, timestamps, and aggregation queries.
- **DevOps & Containerization:** Multi-container Docker Compose orchestration with MySQL health checks, persistent volumes, bridge networks, and Gunicorn WSGI.
- **Localization:** Default currency formatted in Indian Rupees (₹) with Indian number formatting (e.g., ₹1,250.00).

---

## 🏛️ Architecture & Project Structure

```
devops/
├── app/
│   ├── __init__.py               # Flask application factory
│   ├── config.py                 # Configuration loader from environment
│   ├── database/
│   │   ├── connection.py         # PyMySQL connection manager & initializer
│   │   └── schema.sql            # Normalized MySQL DDL schema and initial tables
│   ├── routes/
│   │   ├── main.py               # Main page and health check endpoints
│   │   ├── transactions.py       # CRUD operations, search, filters & pagination
│   │   ├── budgets.py            # Monthly budget tracking & progress
│   │   ├── dashboard.py          # Real-time metrics & financial summary
│   │   ├── analytics.py          # Aggregation queries & spending trends
│   │   └── settings.py           # User preferences & realistic demo seeder
│   ├── static/
│   │   ├── css/
│   │   │   └── style.css         # Modern SaaS financial dashboard styles
│   │   └── js/
│   │       └── app.js            # Frontend controller, state & chart rendering
│   └── templates/
│       └── index.html            # Responsive single-page application shell
├── tests/
│   ├── test_validation.py        # Unit validation test suite
│   └── test_integration.py       # Live integration & API test suite
├── Dockerfile                    # Multi-stage optimized Flask container
├── docker-compose.yml            # Multi-service composition (web + db)
├── requirements.txt              # Pinned Python package dependencies
├── .dockerignore                 # Excludes local files from image build
├── .gitignore                    # Excludes virtualenvs, cache, and secrets
├── .env.example                  # Template configuration file
└── README.md                     # Documentation
```

---

## 🗄️ Database Schema

The application uses three normalized tables in MySQL:

1. **`transactions`**:
   - `id`: INT AUTO_INCREMENT PRIMARY KEY
   - `title`: VARCHAR(150) NOT NULL
   - `type`: ENUM('Income', 'Expense') NOT NULL
   - `amount`: DECIMAL(12, 2) NOT NULL
   - `category`: VARCHAR(50) NOT NULL
   - `transaction_date`: DATE NOT NULL
   - `description`: TEXT NULL
   - `created_at`, `updated_at`: TIMESTAMP

2. **`budgets`**:
   - `id`: INT AUTO_INCREMENT PRIMARY KEY
   - `category`: VARCHAR(50) NOT NULL (e.g., 'Overall', 'Food', 'Rent')
   - `monthly_limit`: DECIMAL(12, 2) NOT NULL
   - `month`: INT NOT NULL (1 - 12)
   - `year`: INT NOT NULL (e.g., 2026)
   - `created_at`, `updated_at`: TIMESTAMP
   - `UNIQUE KEY`: (`category`, `month`, `year`)

3. **`settings`**:
   - `id`: INT PRIMARY KEY
   - `display_name`: VARCHAR(100) NOT NULL
   - `currency`: VARCHAR(10) NOT NULL (Default: '₹')
   - `created_at`, `updated_at`: TIMESTAMP

---

## 🚀 Quick Start with Docker

### Prerequisites
- Docker Engine installed (v20+ recommended)
- Docker Compose (v2+ / `docker compose`)

### 1. Configure Environment Variables
Copy the template configuration file:
```bash
cp .env.example .env
```
*(You can customize `DB_PASSWORD` or leave default values for local development).*

### 2. Build and Start Application
Run the multi-container stack in the background:
```bash
docker compose up -d --build
```

### 3. Access the Web Application
Open your web browser and navigate to:
```
http://localhost:5000
```

### 4. Check Container Status & Logs
Verify all containers are healthy:
```bash
docker compose ps
```
Follow real-time logs:
```bash
docker compose logs -f
```

### 5. Stop the Application
Stop running containers safely without losing data:
```bash
docker compose down
```
*(The named volume `mysql_data` persists across restarts).*

---

## 🔄 Resetting the Database (Optional)
If you ever need a clean database reset:
```bash
docker compose down -v
docker compose up -d --build
```
> **Note:** The `-v` flag removes the MySQL volume and reinitializes `schema.sql` on startup.

---

## 🧪 Testing the Application

Automated unit and integration test suites are included.

### Run Unit Validation Tests:
```bash
python3 -m unittest tests/test_validation.py
```

### Run Live End-to-End Integration Tests (against running Docker container):
```bash
python3 -m unittest tests/test_integration.py
```

---

## 🌐 REST API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Serves the main HTML5 dashboard application |
| `GET` | `/health` | Application health check endpoint |
| `GET` | `/api/dashboard` | Returns summary cards, trends, and recent transactions |
| `GET` | `/api/transactions` | Lists transactions with search, filter, sort & pagination |
| `POST` | `/api/transactions` | Creates a new Income or Expense transaction |
| `GET` | `/api/transactions/<id>` | Fetches single transaction details |
| `PUT` | `/api/transactions/<id>` | Updates an existing transaction |
| `DELETE`| `/api/transactions/<id>` | Deletes a transaction |
| `GET` | `/api/budgets` | Returns category & overall budgets with actual spending |
| `POST` | `/api/budgets` | Creates or updates a monthly budget limit |
| `DELETE`| `/api/budgets/<id>` | Removes a monthly budget limit |
| `GET` | `/api/analytics` | Returns aggregated metrics, trends, and savings calculations |
| `GET` | `/api/settings` | Gets current user preferences and currency |
| `PUT` | `/api/settings` | Updates user display name and currency |
| `POST` | `/api/settings/seed-demo` | Seeds realistic sample financial data for live presentations |

---

## 📦 Git & GitHub Version Control Commands

To initialize and push this project to your GitHub repository:

```bash
# 1. Initialize local repository
git init

# 2. Add files
git add .

# 3. Create initial meaningful commits
git commit -m "feat: complete personal expense tracker with Flask, MySQL, and Docker"

# 4. Link to your GitHub repository
git remote add origin https://github.com/<your-username>/personal-expense-tracker.git
git branch -M main

# 5. Push to GitHub
git push -u origin main
```
