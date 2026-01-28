from flask import Flask
from flask_cors import CORS
from db import db
from config import settings
from models import Application, JobOffer
from flask import request, jsonify

app = Flask(__name__)
CORS(app)

app.config["SQLALCHEMY_DATABASE_URI"] = settings.database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = settings.track_modifications

db.init_app(app)


@app.route("/job_offers", methods=["POST"])
def create_job_offer():
    data = request.json

    offer = JobOffer(
        company=data["company"],
        role=data["role"],
        status=data.get("status", "OPEN"),
    )

    db.session.add(offer)
    db.session.commit()

    return offer.to_dict(), 201


@app.route("/job_offers", methods=["GET"])
def list_job_offers():
    offers = JobOffer.query.all()
    return jsonify([o.to_dict() for o in offers])


@app.route("/applications", methods=["POST"])
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


@app.route("/applications", methods=["GET"])
def get_applications():
    user_id = request.args.get("user_id")
    apps = Application.query.filter_by(user_id=user_id).all()

    return jsonify([a.to_dict() for a in apps])


if __name__ == "__main__":
    from migrate import init_db

    init_db(app, db)
    app.run(debug=True)
