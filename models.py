from db import db
from datetime import datetime
import uuid


class JobOffer(db.Model):
    __tablename__ = "job_offers"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    company = db.Column(db.String, nullable=False)
    role = db.Column(db.String, nullable=False)
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
            "company": self.company,
            "role": self.role,
            "status": self.status,
            "created_at": self.created_at,
        }


class Application(db.Model):
    __tablename__ = "applications"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String, nullable=False)
    job_offer_id = db.Column(db.String(36), db.ForeignKey("job_offers.id"), nullable=False)
    status = db.Column(db.String, default="applied")
    applied_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    job_offer = db.relationship("JobOffer", back_populates="applications")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "job_offer": self.job_offer.to_dict() if self.job_offer else None,
            "status": self.status,
            "applied_date": self.applied_date,
            "created_at": self.created_at,
        }
