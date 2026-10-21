from database import db
from utils.helpers import format_date, utcnow

VALID_STATUSES = ("pending", "in_progress", "done", "cancelled")
CLOSED_STATUSES = ("done", "cancelled")
MIN_PRIORITY, MAX_PRIORITY = 1, 5
DEFAULT_PRIORITY = 3
HIGH_PRIORITY_THRESHOLD = 2
MIN_TITLE_LENGTH, MAX_TITLE_LENGTH = 3, 200
PRIORITY_LABELS = {1: "critical", 2: "high", 3: "medium", 4: "low", 5: "minimal"}


class Task(db.Model):
    __tablename__ = 'tasks'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(MAX_TITLE_LENGTH), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), default='pending')
    priority = db.Column(db.Integer, default=DEFAULT_PRIORITY)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)
    due_date = db.Column(db.DateTime, nullable=True)
    tags = db.Column(db.String(500), nullable=True)

    user = db.relationship('User', backref='tasks')
    category = db.relationship('Category', backref='tasks')

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'priority': self.priority,
            'user_id': self.user_id,
            'category_id': self.category_id,
            'created_at': str(self.created_at),
            'updated_at': str(self.updated_at),
            'due_date': format_date(self.due_date),
            'tags': self.tags.split(',') if self.tags else [],
        }

    def is_overdue(self, now=None):
        now = now or utcnow()
        return bool(self.due_date and self.due_date < now and self.status not in CLOSED_STATUSES)

    def days_overdue(self, now=None):
        return ((now or utcnow()) - self.due_date).days if self.due_date else 0
