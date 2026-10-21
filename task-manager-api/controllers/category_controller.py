from sqlalchemy import func

from database import db
from errors import NotFoundError
from models.category import Category
from models.task import Task
from utils.validators import validate_category_payload


def get_category_or_404(category_id):
    category = db.session.get(Category, category_id)
    if category is None:
        raise NotFoundError('Categoria não encontrada')
    return category


def list_categories():
    counts = dict(db.session.query(Task.category_id, func.count(Task.id)).group_by(Task.category_id).all())
    result = []
    for category in Category.query.all():
        data = category.to_dict()
        data['task_count'] = counts.get(category.id, 0)
        result.append(data)
    return result


def create_category(data):
    category = Category(**validate_category_payload(data))
    db.session.add(category)
    db.session.commit()
    return category.to_dict()


def update_category(category_id, data):
    category = get_category_or_404(category_id)
    for name, value in validate_category_payload(data, partial=True).items():
        setattr(category, name, value)
    db.session.commit()
    return category.to_dict()


def delete_category(category_id):
    category = get_category_or_404(category_id)
    # Desvincula tasks para não deixar chaves estrangeiras apontando para categoria inexistente.
    Task.query.filter_by(category_id=category_id).update({Task.category_id: None})
    db.session.delete(category)
    db.session.commit()
