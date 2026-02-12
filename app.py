from flask import Flask, redirect
from flask_cors import CORS
from db import db
from config import settings
from models import Application, JobOffer, User
from flask import request, jsonify
from storage import (
    upload_resume,
    get_presigned_resume_url,
    resume_key_exists,
    upload_image,
    image_key_exists,
    get_presigned_image_url,
)

# Presigned resume URL expiry (seconds) — short-lived for security
RESUME_URL_EXPIRES_IN = 60 * 5  # 5 minutes
 

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

def _job_offer_with_image_url(offer):
    """Return offer dict with image_url set when offer has image_key and B2 is configured."""
    d = offer.to_dict()
    if offer.image_key and settings.b2_configured:
        try:
            d["image_url"] = get_presigned_image_url(offer.image_key, expires_in=RESUME_URL_EXPIRES_IN)
        except Exception:
            d["image_url"] = None
    else:
        d["image_url"] = None
    return d


@app.route("/api/job_offers", methods=["GET"])
def list_job_offers():
    try:
        # Get all job offers where status is "OPEN"
        offers = JobOffer.query.filter_by(status="OPEN").all()
        return jsonify([_job_offer_with_image_url(o) for o in offers]), 200
    except Exception as e:
        # Log the error (optional)
        print("Error listing job offers:", e)
        return jsonify({"error": "Failed to fetch job offers"}), 500


@app.route("/api/resumes", methods=["POST"])
def upload_resume_endpoint():
    """
    Upload a resume file to B2 (Python backend, boto3). Returns resume_key for use in POST /api/applications.
    Body: multipart/form-data with file (field "resume" or "file") and user_id (form field).
    """
    if not settings.b2_configured:
        return jsonify({"error": "Resume storage (B2) is not configured"}), 503
    file = request.files.get("resume") or request.files.get("file")
    user_id = (request.form.get("user_id") or "").strip()
    if not file or not file.filename:
        return jsonify({"error": "No file provided; send a file (field 'resume' or 'file') and user_id"}), 400
    if not user_id:
        return jsonify({"error": "user_id is required (form field)"}), 400
    try:
        resume_key = upload_resume(file.stream, file.filename, user_id)
        return jsonify({"resume_key": resume_key}), 201
    except Exception as e:
        print("Resume upload failed:", e)
        return jsonify({"error": "Resume upload failed", "detail": str(e)}), 500


@app.route("/api/images", methods=["POST"])
def upload_image_endpoint():
    """
    Upload an image file to B2 under images/. Returns image_key for use in POST /api/company/job_offers.
    Body: multipart/form-data with file (field "image" or "file") and company_id (form field).
    """
    if not settings.b2_configured:
        return jsonify({"error": "Image storage (B2) is not configured"}), 503
    file = request.files.get("image") or request.files.get("file")
    company_id = (request.form.get("company_id") or "").strip()
    if not file or not file.filename:
        return jsonify({"error": "No file provided; send a file (field 'image' or 'file') and company_id"}), 400
    if not company_id:
        return jsonify({"error": "company_id is required (form field)"}), 400
    try:
        image_key = upload_image(file.stream, file.filename, company_id)
        return jsonify({"image_key": image_key}), 201
    except Exception as e:
        print("Image upload failed:", e)
        return jsonify({"error": "Image upload failed", "detail": str(e)}), 500


@app.route("/api/applications", methods=["POST"])
def create_application():
    # JSON or form: user_id, job_offer_id, motivation_letter, optional resume_key
    if request.is_json:
        data = request.json or {}
    else:
        form = request.form or {}
        data = {
            "user_id": form.get("user_id"),
            "job_offer_id": form.get("job_offer_id"),
            "motivation_letter": form.get("motivation_letter"),
            "resume_key": form.get("resume_key"),
        }

    if not data.get("user_id") or not data.get("job_offer_id"):
        return jsonify({"error": "user_id and job_offer_id are required"}), 400

    resume_key = data.get("resume_key") or None
    if resume_key and settings.b2_configured and not resume_key_exists(resume_key):
        return jsonify({
            "error": "resume_key not found",
            "message": "The given resume_key does not exist in storage. Upload a resume first with POST /api/resumes.",
        }), 404

    job_offer = JobOffer.query.get(data["job_offer_id"])
    if not job_offer:
        return jsonify({
            "error": "job_offer_id not found",
            "message": "No job offer exists with the given job_offer_id. Create a job offer first or use an existing id.",
        }), 404

    application = Application(
        user_id=data["user_id"],
        job_offer_id=data["job_offer_id"],
        motivation_letter=data.get("motivation_letter"),
        status="applied",
        resume_key=resume_key if resume_key else None,
    )

    db.session.add(application)
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        err_msg = str(e.orig) if hasattr(e, "orig") else str(e)
        return jsonify({
            "error": "Database error while creating application",
            "detail": err_msg,
        }), 500

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
                resume_url = get_presigned_resume_url(a.resume_key, expires_in=RESUME_URL_EXPIRES_IN)
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

    image_key = data.get("image_key") or None
    if image_key and settings.b2_configured and not image_key_exists(image_key):
        return jsonify({
            "error": "image_key not found",
            "message": "The given image_key does not exist in storage. Upload an image first with POST /api/images.",
        }), 404

    offer = JobOffer(
        company_name=data["company_name"],
        company_id=data["company_id"],
        role=data["role"],
        description=data.get("description"),
        status=data.get("status", "OPEN"),
        image_key=image_key,
    )

    db.session.add(offer)
    db.session.commit()

    return _job_offer_with_image_url(offer), 201

@app.route("/api/company/job_offers", methods=["GET"])
def get_company_offers():
    company_id = request.args.get("company_id")
    if not company_id:
        return jsonify({"error": "Missing required query param: company_id"}), 400
    offers = JobOffer.query.filter_by(company_id=company_id).all()
    return jsonify([_job_offer_with_image_url(o) for o in offers]), 200


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
                user_data["resume_url"] = get_presigned_resume_url(application.resume_key, expires_in=RESUME_URL_EXPIRES_IN)
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
    resume_key = application.resume_key
    try:
        url = get_presigned_resume_url(resume_key, expires_in=RESUME_URL_EXPIRES_IN)
        return jsonify({"url": url}), 200
    except Exception as e:
        print("Presigned URL failed:", e)
        return jsonify({"error": "Failed to generate resume link"}), 500


@app.route("/api/job_offers/<offer_id>/image", methods=["GET"])
def job_offer_image(offer_id):
    """Redirect to presigned URL for the job offer image. Frontend can use this when image_url is not in the list payload."""
    offer = JobOffer.query.filter_by(id=offer_id).first()
    if not offer:
        return jsonify({"error": "Job offer not found"}), 404
    if not offer.image_key:
        return jsonify({"error": "No image for this job offer"}), 404
    if not settings.b2_configured:
        return jsonify({"error": "Image storage not configured"}), 503
    try:
        url = get_presigned_image_url(offer.image_key, expires_in=RESUME_URL_EXPIRES_IN)
        return redirect(url, code=302)
    except Exception as e:
        print("Presigned image URL failed:", e)
        return jsonify({"error": "Failed to generate image link"}), 500


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
