from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Business(db.Model):
    __tablename__ = 'businesses'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    address = db.Column(db.Text)
    phone = db.Column(db.String(50))
    website = db.Column(db.String(500))
    rating = db.Column(db.Float)
    has_email = db.Column(db.Boolean, default=False)
    scraped_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship to emails
    emails = db.relationship('Email', backref='business', lazy=True)

class Email(db.Model):
    __tablename__ = 'emails'
    id = db.Column(db.Integer, primary_key=True)
    business_id = db.Column(db.Integer, db.ForeignKey('businesses.id'), nullable=False)
    email = db.Column(db.String(255))
    source = db.Column(db.String(100)) # scraped or hunter
    email_body = db.Column(db.Text)
    subject = db.Column(db.String(500))
    status = db.Column(db.String(50), default='pending') # pending, generated, approved, sent, failed, skipped
    generated_at = db.Column(db.DateTime)
    
    # Relationship to logs
    logs = db.relationship('SendLog', backref='email_entry', lazy=True)

class SendLog(db.Model):
    __tablename__ = 'send_log'
    id = db.Column(db.Integer, primary_key=True)
    email_id = db.Column(db.Integer, db.ForeignKey('emails.id'), nullable=False)
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(50)) # sent, failed, skipped
    error_msg = db.Column(db.Text)

class Setting(db.Model):
    __tablename__ = 'settings'
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text)

    @staticmethod
    def get(key, default=None):
        res = Setting.query.filter_by(key=key).first()
        return res.value if res else default

    @staticmethod
    def set(key, value):
        res = Setting.query.filter_by(key=key).first()
        if not res:
            res = Setting(key=key, value=value)
            db.session.add(res)
        else:
            res.value = value
        db.session.commit()
