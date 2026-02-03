from sqlalchemy import inspect, text


def init_db(app, db):
    """
    Initialize the database by creating all tables if the main ones don't exist yet.

    We use the presence of core tables as the indicator that the schema
    has already been created.
    """
    with app.app_context():
        inspector = inspect(db.engine)
        existing_tables = inspector.get_table_names()

        # Fresh database → create everything
        required_tables = {"job_offers", "applications", "users"}
        if not required_tables.issubset(existing_tables):
            print("Creating tables (job_offers, applications, user)...")
            db.create_all()
            print("Database initialized.")
            return
        
        print("Database already initialized. Skipping create_all().")
