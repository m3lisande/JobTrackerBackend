from flask import Flask, redirect
from flask_cors import CORS
from db import db
from config import settings
from models import Application, JobOffer, User
from flask import request, jsonify
from storage import upload_resume, get_presigned_resume_url
 

app = Flask(__name__)
CORS(app)

app.config["SQLALCHEMY_DATABASE_URI"] = settings.database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = settings.track_modifications

db.init_app(app)

# Initialize database tables on startup (works with gunicorn in production)
from migrate import init_db
init_db(app, db)


@app.route("/")
def health_check():
    return jsonify({"status": "healthy", "message": "JobTracker API is running"}), 200

@app.route("/api/job_offers", methods=["GET"])
def list_job_offers():
    try:
        # Get all job offers where status is "OPEN"
        offers = JobOffer.query.filter_by(status="OPEN").all()
        return jsonify([o.to_dict() for o in offers]), 200
    except Exception as e:
        # Log the error (optional)
        print("Error listing job offers:", e)
        return jsonify({"error": "Failed to fetch job offers"}), 500

@app.route("/api/applications", methods=["POST"])
def create_application():
    # Support both JSON and multipart (for resume upload)
    if request.is_json:
        data = request.json
        resume_file = None
        resume_filename = None
    else:
        data = {
            "user_id": request.form.get("user_id"),
            "job_offer_id": request.form.get("job_offer_id"),
            "motivation_letter": request.form.get("motivation_letter"),
        }
        if "user_id" not in data or "job_offer_id" not in data:
            return jsonify({"error": "user_id and job_offer_id are required"}), 400
        resume_file = request.files.get("resume")
        resume_filename = resume_file.filename if resume_file and resume_file.filename else None

    application = Application(
        user_id=data["user_id"],
        job_offer_id=data["job_offer_id"],
        motivation_letter=data.get("motivation_letter"),
        status="applied",
    )

    db.session.add(application)
    db.session.commit()

    # Upload resume to B2 if provided and B2 is configured
    if resume_file and resume_filename and settings.b2_configured:
        try:
            application.resume_key = upload_resume(
                application.id, resume_file.stream, resume_filename
            )
            db.session.commit()
        except Exception as e:
            print("Resume upload failed:", e)
            # Application was created; resume_key stays None

    return application.to_dict(), 201


@app.route("/api/user/applications", methods=["GET"])
def get_applications():
    user_id = request.args.get("user_id")
    apps = Application.query.filter_by(user_id=user_id, status="applied").all()

    out = []
    for a in apps:
        resume_url = None
        if a.resume_key and settings.b2_configured:
            try:
                resume_url = get_presigned_resume_url(a.resume_key)
            except Exception:
                pass
        out.append(a.to_dict(include_resume_url=resume_url))
    return out, 200

@app.route("/api/users", methods=["POST"])
def create_user():
    data = request.json
    user_id = data.get("user_id")
    first_name = data.get("first_name")
    last_name = data.get("last_name")
    email = data.get("email")
    user = User(
        role=data["role"],
        user_id=user_id,
        first_name=first_name,
        last_name=last_name,
        email=email,
    )
    db.session.add(user)
    db.session.commit()
    return user.to_dict(), 201


@app.route("/api/role", methods=["GET"])
def get_role():
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"error": "Missing required query param: user_id"}), 400

    user = User.query.filter_by(user_id=user_id).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    if not user.role:
        return jsonify({"error": "User role not found"}), 404

    return jsonify({"user_id": user_id, "role": user.role}), 200

@app.route("/api/company/job_offers", methods=["POST"])
def create_job_offer():
    data = request.json

    offer = JobOffer(
        company_name=data["company_name"],
        company_id=data["company_id"],
        role=data["role"],
        description=data.get("description"),
        status=data.get("status", "OPEN"),
    )

    db.session.add(offer)
    db.session.commit()

    return offer.to_dict(), 201

@app.route("/api/company/job_offers", methods=["GET"])
def get_company_offers(): 
    company_id = request.args.get("company_id")
    if not company_id:
        return jsonify({"error": "Missing required query param: company_id"}), 400
    offers = JobOffer.query.filter_by(company_id=company_id).all()
    return [o.to_dict() for o in offers], 200


@app.route("/api/company/job_offers/<offer_id>", methods=["PUT"])
def change_job_offer_status(offer_id): 
    if not offer_id:
        return jsonify({"error": "Missing required query param: offer_id"}), 400
    offer = JobOffer.query.filter_by(id=offer_id).first()
    if not offer:
        return jsonify({"error": "Offer not found"}), 404
    offer.status = "CLOSED"
    db.session.commit()
    return offer.to_dict(), 200


@app.route("/api/company/job_offers/<offer_id>", methods=["GET"])
def get_applications_for_offer(offer_id):
    if not offer_id:
        return jsonify({"error": "Missing required query param: offer_id"}), 400
    applications = Application.query.filter_by(job_offer_id=offer_id).all()

    # Build a map of user_id -> application for quick lookup
    app_by_user = {a.user_id: a for a in applications}

    users = User.query.filter(
        User.user_id.in_([a.user_id for a in applications]), User.role == "job_seeker"
    ).all()

    # Return user info along with motivation letter and resume URL for companies
    result = []
    for user in users:
        user_data = user.to_dict()
        application = app_by_user.get(user.user_id)
        user_data["motivation_letter"] = application.motivation_letter if application else None
        user_data["application_id"] = application.id if application else None
        user_data["has_resume"] = application.resume_key is not None if application else False
        if application and application.resume_key and settings.b2_configured:
            try:
                user_data["resume_url"] = get_presigned_resume_url(application.resume_key)
            except Exception:
                user_data["resume_url"] = None
        else:
            user_data["resume_url"] = None
        result.append(user_data)

    return jsonify(result)

@app.route("/api/applications/<application_id>/resume", methods=["GET"])
def open_resume(application_id):
    """Redirect to a presigned URL so the company (or user) can open the resume."""
    application = Application.query.filter_by(id=application_id).first()
    if not application:
        return jsonify({"error": "Application not found"}), 404
    if not application.resume_key:
        return jsonify({"error": "No resume for this application"}), 404
    if not settings.b2_configured:
        return jsonify({"error": "Resume storage not configured"}), 503
    try:
        url = get_presigned_resume_url(application.resume_key)
        return redirect(url, code=302)
    except Exception as e:
        print("Presigned URL failed:", e)
        return jsonify({"error": "Failed to generate resume link"}), 500


@app.route("/api/job_offers/<offer_id>/has_applied", methods=["GET"])
def has_applied(offer_id):
    user_id = request.args.get("user_id")
    print(user_id)
    print(offer_id)
    if not user_id:
        return jsonify({"error": "Missing required query param: user_id"}), 400

    application = Application.query.filter_by(
        user_id=user_id, 
        job_offer_id=offer_id
    ).first()

    print("Found application:", application)
    return jsonify({"has_applied": application is not None}), 200

if __name__ == "__main__":
    app.run(debug=True)
