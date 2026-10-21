import logging

from sqlalchemy import func
from sqlalchemy.orm import joinedload

from database import db
from errors import NotFoundError, ValidationError
from models.category import Category
from models.task import CLOSED_STATUSES, Task
from models.user import User
from utils.helpers import calculate_percentage, utcnow
from utils.validators import validate_task_payload

logger = logging.getLogger(__name__)


def get_task_or_404(task_id):
    task = db.session.get(Task, task_id)
    if task is None:
        raise NotFoundError('Task não encontrada')
    return task


def overdue_filter(now):
    return db.and_(Task.due_date.isnot(None), Task.due_date < now, Task.status.notin_(CLOSED_STATUSES))


class TaskController:
    def __init__(self, notifier):
        self.notifier = notifier

    @staticmethod
    def _ensure_relations_exist(fields):
        if fields.get('user_id') and db.session.get(User, fields['user_id']) is None:
            raise NotFoundError('Usuário não encontrado')
        if fields.get('category_id') and db.session.get(Category, fields['category_id']) is None:
            raise NotFoundError('Categoria não encontrada')

    def list_tasks(self):
        tasks = Task.query.options(joinedload(Task.user), joinedload(Task.category)).all()
        now = utcnow()
        result = []
        for task in tasks:
            data = task.to_dict()
            data['overdue'] = task.is_overdue(now)
            data['user_name'] = task.user.name if task.user else None
            data['category_name'] = task.category.name if task.category else None
            result.append(data)
        return result

    def get_task(self, task_id):
        task = get_task_or_404(task_id)
        data = task.to_dict()
        data['overdue'] = task.is_overdue()
        return data

    def create_task(self, data):
        fields = validate_task_payload(data)
        self._ensure_relations_exist(fields)

        task = Task(**fields)
        db.session.add(task)
        db.session.commit()
        logger.info("Task criada: %s", task.id)

        if task.user is not None:
            self.notifier.notify_task_assigned(task.user, task)
        return task.to_dict()

    def update_task(self, task_id, data):
        task = get_task_or_404(task_id)
        fields = validate_task_payload(data, partial=True)
        self._ensure_relations_exist(fields)

        for name, value in fields.items():
            setattr(task, name, value)
        task.updated_at = utcnow()
        db.session.commit()
        logger.info("Task atualizada: %s", task.id)
        return task.to_dict()

    def delete_task(self, task_id):
        task = get_task_or_404(task_id)
        db.session.delete(task)
        db.session.commit()
        logger.info("Task deletada: %s", task_id)

    def search_tasks(self, text, status, priority, user_id):
        query = Task.query
        if text:
            pattern = f'%{text}%'
            query = query.filter(db.or_(Task.title.like(pattern), Task.description.like(pattern)))
        if status:
            query = query.filter(Task.status == status)
        try:
            if priority:
                query = query.filter(Task.priority == int(priority))
            if user_id:
                query = query.filter(Task.user_id == int(user_id))
        except ValueError:
            raise ValidationError('Parâmetros de busca inválidos')
        return [task.to_dict() for task in query.all()]

    def stats(self):
        by_status = dict(db.session.query(Task.status, func.count(Task.id)).group_by(Task.status).all())
        total = sum(by_status.values())
        done = by_status.get('done', 0)
        return {
            'total': total,
            'pending': by_status.get('pending', 0),
            'in_progress': by_status.get('in_progress', 0),
            'done': done,
            'cancelled': by_status.get('cancelled', 0),
            'overdue': Task.query.filter(overdue_filter(utcnow())).count(),
            'completion_rate': calculate_percentage(done, total),
        }
