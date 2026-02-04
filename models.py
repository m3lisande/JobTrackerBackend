from db import db
from datetime import datetime
import uuid


class JobOffer(db.Model):
    __tablename__ = "job_offers"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    company_id = db.Column(db.String(36), db.ForeignKey("users.user_id"), nullable=False)
    company_name = db.Column(db.String, nullable=False)
    role = db.Column(db.String, nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(
        db.Enum("OPEN", "CLOSED", name="job_offer_status"),
        default="OPEN",
        nullable=False,
    )
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    applications = db.relationship(
        "Application", back_populates="job_offer", cascade="all, delete-orphan"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "company_name": self.company_name,
            "company_id": self.company_id,
            "role": self.role,
            "description": self.description,
            "status": self.status,
            "created_at": self.created_at,
        }


class Application(db.Model):
    __tablename__ = "applications"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String, nullable=False)
    job_offer_id = db.Column(db.String(36), db.ForeignKey("job_offers.id"), nullable=False)
    status = db.Column(db.String, default="applied")
    motivation_letter = db.Column(db.Text, nullable=True)
    applied_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    job_offer = db.relationship("JobOffer", back_populates="applications")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "job_offer": self.job_offer.to_dict() if self.job_offer else None,
            "status": self.status,
            "motivation_letter": self.motivation_letter,
            "applied_date": self.applied_date,
            "created_at": self.created_at,
        }


class User(db.Model):
    __tablename__ = "users"

    role = db.Column(db.String, nullable=False)
    user_id = db.Column(db.String(36), primary_key=True, nullable=False)
    first_name = db.Column(db.String, nullable=False)
    last_name = db.Column(db.String, nullable=False)
    email = db.Column(db.String, nullable=False)

    def to_dict(self):
        return {
            "id": self.user_id,
            "role": self.role,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email": self.email,
        }

