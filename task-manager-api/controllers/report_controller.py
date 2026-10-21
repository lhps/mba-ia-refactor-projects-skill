from datetime import timedelta

from sqlalchemy import case, func

from controllers.task_controller import overdue_filter
from controllers.user_controller import get_user_or_404
from database import db
from models.category import Category
from models.task import HIGH_PRIORITY_THRESHOLD, PRIORITY_LABELS, VALID_STATUSES, Task
from models.user import User
from utils.helpers import calculate_percentage, utcnow

RECENT_ACTIVITY_DAYS = 7


def _count_by(column):
    return dict(db.session.query(column, func.count(Task.id)).group_by(column).all())


def summary_report():
    now = utcnow()
    since = now - timedelta(days=RECENT_ACTIVITY_DAYS)

    by_status = _count_by(Task.status)
    by_priority = _count_by(Task.priority)
    overdue_tasks = Task.query.filter(overdue_filter(now)).all()

    completed = func.sum(case((Task.status == 'done', 1), else_=0))
    per_user = {
        user_id: (total, done or 0)
        for user_id, total, done in db.session.query(Task.user_id, func.count(Task.id), completed).group_by(Task.user_id)
    }
    user_stats = []
    for user in User.query.all():
        total, done = per_user.get(user.id, (0, 0))
        user_stats.append({
            'user_id': user.id,
            'user_name': user.name,
            'total_tasks': total,
            'completed_tasks': done,
            'completion_rate': calculate_percentage(done, total),
        })

    return {
        'generated_at': str(now),
        'overview': {
            'total_tasks': Task.query.count(),
            'total_users': User.query.count(),
            'total_categories': Category.query.count(),
        },
        'tasks_by_status': {status: by_status.get(status, 0) for status in VALID_STATUSES},
        'tasks_by_priority': {label: by_priority.get(p, 0) for p, label in PRIORITY_LABELS.items()},
        'overdue': {
            'count': len(overdue_tasks),
            'tasks': [
                {'id': t.id, 'title': t.title, 'due_date': str(t.due_date), 'days_overdue': t.days_overdue(now)}
                for t in overdue_tasks
            ],
        },
        'recent_activity': {
            'tasks_created_last_7_days': Task.query.filter(Task.created_at >= since).count(),
            'tasks_completed_last_7_days': Task.query.filter(Task.status == 'done', Task.updated_at >= since).count(),
        },
        'user_productivity': user_stats,
    }


def user_report(user_id):
    user = get_user_or_404(user_id)
    tasks = Task.query.filter_by(user_id=user_id).all()
    now = utcnow()

    stats = {status: 0 for status in VALID_STATUSES}
    for task in tasks:
        if task.status in stats:
            stats[task.status] += 1
    total = len(tasks)

    return {
        'user': {'id': user.id, 'name': user.name, 'email': user.email},
        'statistics': {
            'total_tasks': total,
            'done': stats['done'],
            'pending': stats['pending'],
            'in_progress': stats['in_progress'],
            'cancelled': stats['cancelled'],
            'overdue': sum(1 for t in tasks if t.is_overdue(now)),
            'high_priority': sum(1 for t in tasks if t.priority <= HIGH_PRIORITY_THRESHOLD),
            'completion_rate': calculate_percentage(stats['done'], total),
        },
    }
