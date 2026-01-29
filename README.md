# JobTracker Backend

Flask API backend for the JobTracker application. It provides endpoints for job offers, applications, and user management.

---

## Prerequisites

### 1. Python

- **Python 3.9**

**macOS (Homebrew):**

```bash
brew install python
```

Check your version:

```bash
python3 --version
```

### 2. Poetry (recommended)

The project uses [Poetry](https://python-poetry.org/) for dependency management.

**macOS (Homebrew):**

```bash
brew install poetry
```

Other install options: <https://python-poetry.org/docs/#installation>

Verify:

```bash
poetry --version
```

### 3. PostgreSQL

- **PostgreSQL 14** (or a compatible version)

**macOS (Homebrew):**

```bash
brew install postgresql@14
brew services start postgresql@14
```

The backend stores all data in PostgreSQL. You need:

1. **PostgreSQL installed and running** (e.g. via [postgresapp](https://postgresapp.com/), Homebrew, or your system package manager).

2. **A database** named `jobtracker` (or another name if you override the URL).

3. **A Postgres user** that can connect to that database. On many setups, a user matching your OS username already exists.

**Check your OS username (often used as the Postgres user):**

```bash
whoami
```

**Create the database** (using the `psql` CLI or any PostgreSQL client):

```sql
CREATE DATABASE jobtracker;
```

If you need a dedicated user:

```sql
CREATE USER your_username WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE jobtracker TO your_username;
```

---

## Configuration

The app reads the database URL from **environment variables** (via Pydantic Settings). If not set, it falls back to a default.

| Variable          | Description                    | Default (example)                          |
|-------------------|--------------------------------|-------------------------------------------|
| `DATABASE_URL`    | PostgreSQL connection string   | `postgresql://<user>@localhost:5432/jobtracker` |

**Example:** if your OS username is `alex` and the database is `jobtracker` on default port:

```bash
export DATABASE_URL="postgresql://alex@localhost:5432/jobtracker"
```

With password:

```bash
export DATABASE_URL="postgresql://alex:yourpassword@localhost:5432/jobtracker"
```

The default in code uses the project author’s username; set `DATABASE_URL` so it matches your Postgres user and database.

---

## Setup and run

### 1. Install dependencies (with Poetry)

From the project root:

```bash
cd JobTrackerBackend
poetry install
```

### 2. Set the database URL

You must provide `DATABASE_URL` so the app can connect to PostgreSQL. Use either method:

**Option A — `.env` file** (in the project root):

```bash
echo 'DATABASE_URL=postgresql://YOUR_USER@localhost:5432/jobtracker' >> .env
```

**Option B — export in the shell:**

```bash
export DATABASE_URL="postgresql://YOUR_USER@localhost:5432/jobtracker"
```

Replace `YOUR_USER` with your Postgres username (often your OS username). If you set both, the exported value overrides the `.env` value.

### 3. Run the backend

```bash
poetry run python app.py
```

Or activate the Poetry shell first:

```bash
poetry shell
python app.py
```

The server starts in **debug mode** (e.g. `http://127.0.0.1:5000`). On first run, the app creates the required tables (`job_offers`, `applications`, `user`) if they do not exist.

---

## Summary checklist

- [ ] Python ≥ 3.9 installed  
- [ ] Poetry installed  
- [ ] PostgreSQL installed and running  
- [ ] Database `jobtracker` (or your chosen name) created  
- [ ] `DATABASE_URL` set to match your user and database (or default is correct)  
- [ ] `poetry install` run in the project directory  
- [ ] `poetry run python app.py` (or `python app.py` inside `poetry shell`) to start the server  
