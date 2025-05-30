from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(50))  # Например: admin, omsu, oigv, governor


class Risk(db.Model):
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    source_link = db.Column(db.String(500))
    date_added = db.Column(db.DateTime, default=datetime.utcnow)
    time_to_resolve_hours = db.Column(db.Integer)
    is_repeating = db.Column(db.Boolean, default=False)
    description = db.Column(db.Text)
    justification = db.Column(db.Text)
    category = db.Column(db.String(100))
    omsu = db.Column(db.String(100))
    oigv = db.Column(db.String(100))
    governor = db.Column(db.String(100))
    municipality = db.Column(db.String(100))
    severity = db.Column(db.String(50))
    is_resolved = db.Column(db.Boolean, default=False)
    date_resolved = db.Column(db.DateTime)

    chat_messages = db.relationship('ChatMessage', backref='risk', lazy=True)
    notifications = db.relationship('Notification', lazy=True)


class ChatMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text)
    file_path = db.Column(db.String(300))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    risk_id = db.Column(db.Integer, db.ForeignKey('risk.id'))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='messages')





class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    message = db.Column(db.Text, nullable=False)
    risk_id = db.Column(db.Integer, db.ForeignKey('risk.id'))
    is_read = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='notifications')
    risk = db.relationship('Risk', backref='notification_list')