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
            print("Creating tables (job_offers, applications, users)...")
            db.create_all()
            print("Database initialized.")
            return
        
        print("Database already initialized. Running migrations...")
        
        # Add description column to job_offers if it doesn't exist
        job_offer_columns = [col["name"] for col in inspector.get_columns("job_offers")]
        if "description" not in job_offer_columns:
            print("Adding 'description' column to job_offers...")
            db.session.execute(text("ALTER TABLE job_offers ADD COLUMN description TEXT"))
            db.session.commit()
            print("Added 'description' column.")
        
        # Add motivation_letter column to applications if it doesn't exist
        application_columns = [col["name"] for col in inspector.get_columns("applications")]
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
