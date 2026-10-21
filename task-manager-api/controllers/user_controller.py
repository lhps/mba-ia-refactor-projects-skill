import logging

from sqlalchemy import func

from database import db
from errors import ConflictError, ForbiddenError, NotFoundError, UnauthorizedError, ValidationError
from models.task import Task
from models.user import DEFAULT_ROLE, User
from utils.helpers import format_date, utcnow
from utils.validators import require_payload, validate_email, validate_password, validate_role

logger = logging.getLogger(__name__)


def get_user_or_404(user_id):
    user = db.session.get(User, user_id)
    if user is None:
        raise NotFoundError('Usuário não encontrado')
    return user


class UserController:
    def __init__(self, auth_service):
        self.auth_service = auth_service

    def list_users(self):
        counts = dict(db.session.query(Task.user_id, func.count(Task.id)).group_by(Task.user_id).all())
        result = []
        for user in User.query.all():
            data = user.to_dict()
            data['task_count'] = counts.get(user.id, 0)
            result.append(data)
        return result

    def get_user(self, user_id):
        user = get_user_or_404(user_id)
        data = user.to_dict()
        data['tasks'] = [task.to_dict() for task in Task.query.filter_by(user_id=user_id).all()]
        return data

    def create_user(self, data):
        require_payload(data)
        for field, message in (('name', 'Nome é obrigatório'), ('email', 'Email é obrigatório'),
                               ('password', 'Senha é obrigatória')):
            if not data.get(field):
                raise ValidationError(message)
        validate_email(data['email'])
        validate_password(data['password'])
        if User.query.filter_by(email=data['email']).first():
            raise ConflictError('Email já cadastrado')
        role = data.get('role', DEFAULT_ROLE)
        validate_role(role)

        user = User(name=data['name'], email=data['email'], role=role)
        user.set_password(data['password'])
        db.session.add(user)
        db.session.commit()
        logger.info("Usuário criado: %s", user.id)
        return user.to_dict()

    def update_user(self, user_id, data):
        user = get_user_or_404(user_id)
        require_payload(data)

        if 'name' in data:
            user.name = data['name']
        if 'email' in data:
            validate_email(data['email'])
            existing = User.query.filter_by(email=data['email']).first()
            if existing and existing.id != user_id:
                raise ConflictError('Email já cadastrado')
            user.email = data['email']
        if 'password' in data:
            validate_password(data['password'])
            user.set_password(data['password'])
        if 'role' in data:
            validate_role(data['role'])
            user.role = data['role']
        if 'active' in data:
            user.active = bool(data['active'])

        db.session.commit()
        return user.to_dict()

    def delete_user(self, user_id):
        user = get_user_or_404(user_id)
        Task.query.filter_by(user_id=user_id).delete()
        db.session.delete(user)
        db.session.commit()
        logger.info("Usuário deletado: %s", user_id)

    def get_user_tasks(self, user_id):
        get_user_or_404(user_id)
        now = utcnow()
        return [
            {
                'id': task.id,
                'title': task.title,
                'description': task.description,
                'status': task.status,
                'priority': task.priority,
                'created_at': str(task.created_at),
                'due_date': format_date(task.due_date),
                'overdue': task.is_overdue(now),
            }
            for task in Task.query.filter_by(user_id=user_id).all()
        ]

    def login(self, data):
        require_payload(data)
        email, password = data.get('email'), data.get('password')
        if not email or not password:
            raise ValidationError('Email e senha são obrigatórios')

        user = User.query.filter_by(email=email).first()
        if user is None or not user.check_password(password):
            raise UnauthorizedError('Credenciais inválidas')
        if not user.active:
            raise ForbiddenError('Usuário inativo')

        db.session.commit()  # persiste eventual migração de hash legado
        return {
            'message': 'Login realizado com sucesso',
            'user': user.to_dict(),
            'token': self.auth_service.issue_token(user),
        }
