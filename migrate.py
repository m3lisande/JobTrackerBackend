import time

from sqlalchemy import inspect, text
from sqlalchemy.exc import OperationalError


def init_db(app, db):
    """
    Initialize the database in an idempotent, empty-db-safe way.

    - Always calls `db.create_all()` (safe if tables already exist).
    - Applies lightweight "ALTER TABLE ..." migrations for older schemas.
    - Retries initial DB connection briefly so app startup doesn't fail
      on transient network/DNS delays in hosting environments.
    """
    with app.app_context():
        last_err: Exception | None = None
        for attempt in range(1, 8):
            try:
                with db.engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                last_err = None
                break
            except OperationalError as e:
                last_err = e
                sleep_s = min(2**attempt, 15)
                print(
                    f"Database connection not ready (attempt {attempt}/7). "
                    f"Retrying in {sleep_s}s..."
                )
                time.sleep(sleep_s)

        if last_err is not None:
            # Don't crash the import/startup path with an unhandled exception.
            # Routes will still fail until the DB is reachable, but the service
            # can at least boot and expose health checks/logs.
            print("Database connection failed during init_db(). Skipping init for now.")
            print(f"Last error: {last_err}")
            return

        # Empty DB or partially missing tables → create what's needed (idempotent).
        print("Ensuring database schema exists (create_all)...")
        db.create_all()

        inspector = inspect(db.engine)
        existing_tables = set(inspector.get_table_names())

        print("Database schema ensured. Running lightweight migrations (if needed)...")

        def _column_names(table_name: str) -> set[str]:
            if table_name not in existing_tables:
                return set()
            return {col["name"] for col in inspector.get_columns(table_name)}
        
        # Add description column to job_offers if it doesn't exist
        job_offer_columns = _column_names("job_offers")
        if "description" not in job_offer_columns:
            print("Adding 'description' column to job_offers...")
            db.session.execute(text("ALTER TABLE job_offers ADD COLUMN description TEXT"))
            db.session.commit()
            print("Added 'description' column.")
        if "image_key" not in job_offer_columns:
            print("Adding 'image_key' column to job_offers...")
            db.session.execute(text("ALTER TABLE job_offers ADD COLUMN image_key VARCHAR(512)"))
            db.session.commit()
            print("Added 'image_key' column.")
        if "location" not in job_offer_columns:
            print("Adding 'location' column to job_offers...")
            db.session.execute(text("ALTER TABLE job_offers ADD COLUMN location TEXT"))
            db.session.commit()
            print("Added 'location' column.")
        if "salary" not in job_offer_columns:
            print("Adding 'salary' column to job_offers...")
            db.session.execute(text("ALTER TABLE job_offers ADD COLUMN salary TEXT"))
            db.session.commit()
            print("Added 'salary' column.")
        if "empl_type" not in job_offer_columns:
            print("Adding 'empl_type' column to job_offers...")
            db.session.execute(text("ALTER TABLE job_offers ADD COLUMN empl_type TEXT"))
            db.session.commit()
            print("Added 'empl_type' column.")
        
        # Add motivation_letter column to applications if it doesn't exist
        application_columns = _column_names("applications")
        if "motivation_letter" not in application_columns:
            print("Adding 'motivation_letter' column to applications...")
            db.session.execute(text("ALTER TABLE applications ADD COLUMN motivation_letter TEXT"))
            db.session.commit()
            print("Added 'motivation_letter' column.")
        if "resume_key" not in application_columns:
            print("Adding 'resume_key' column to applications...")
            db.session.execute(text("ALTER TABLE applications ADD COLUMN resume_key VARCHAR(512)"))
            db.session.commit()
            print("Added 'resume_key' column.")
        
        print("Migrations complete.")
