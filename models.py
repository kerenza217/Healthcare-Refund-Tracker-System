# from flask_sqlalchemy import SQLAlchemy
# from datetime import datetime
# from flask_login import UserMixin

# db = SQLAlchemy()

# class User(db.Model, UserMixin):
#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String(100), nullable=False)
#     email = db.Column(db.String(120), unique=True, nullable=False)
#     username = db.Column(db.String(80), unique=True, nullable=False)
#     password = db.Column(db.String(200), nullable=False)
#     role = db.Column(db.String(50), nullable=False)  # Customer Solution, Claims Team, MD, Finance

#     def __repr__(self):
#         return f'<User {self.username}>'

# class RefundApplication(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     company_name = db.Column(db.String(255), nullable=False)
#     member_name = db.Column(db.String(255), nullable=False)
#     policy_number = db.Column(db.String(50), nullable=False)
#     amount = db.Column(db.Float, nullable=False)
#     facility_name = db.Column(db.String(255), nullable=False)
#     date_attended = db.Column(db.Date, nullable=False)
#     reason = db.Column(db.Text, nullable=False)
#     attachments = db.Column(db.String(255))  # File paths for receipts/invoices
#     status = db.Column(db.String(50), default='Pending Vetting')  # Workflow status
#     created_by_user = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
#     assigned_to_user = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
#     created_at = db.Column(db.DateTime, default=datetime.utcnow)
#     updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

#     def __repr__(self):
#         return f'<RefundApplication {self.id}, Status: {self.status}>'

