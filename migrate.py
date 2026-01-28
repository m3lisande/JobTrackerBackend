from sqlalchemy import inspect


def init_db(app, db):
    """
    Initialize the database by creating all tables if the main ones don't exist yet.

    We use the presence of the `job_offers` table as the indicator that the schema
    has already been created.
    """
    with app.app_context():
        inspector = inspect(db.engine)

        existing_tables = inspector.get_table_names()

        # If job_offers does not exist yet, this is a fresh database: create all tables.
        if "job_offers" not in existing_tables:
            print("Creating tables (job_offers, applications, ...)...")
            db.create_all()
            print("Database initialized.")
        else:
            print("Database already initialized. Skipping.")
