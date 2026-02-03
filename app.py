from flask import Flask
from flask_cors import CORS
from db import db
from config import settings
from models import Application, JobOffer, User
from flask import request, jsonify
 

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
    data = request.json

    application = Application(
        user_id=data["user_id"],
        job_offer_id=data["job_offer_id"],
        status="applied",
    )

    db.session.add(application)
    db.session.commit()

    return application.to_dict(), 201


@app.route("/api/user/applications", methods=["GET"])
def get_applications():
    user_id = request.args.get("user_id")
    apps = Application.query.filter_by(user_id=user_id, status="applied").all()

    return [a.to_dict() for a in apps], 200

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
    users = User.query.filter(User.user_id.in_([a.user_id for a in applications]), User.role == "job_seeker").all()
    return jsonify([user.to_dict() for user in users])

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
