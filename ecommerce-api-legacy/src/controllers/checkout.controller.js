const { NotFoundError, PaymentDeclinedError, ValidationError } = require('../errors/AppError');
const { PAYMENT_STATUS } = require('../models/payment.model');

const EMAIL_REGEX = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;
const CARD_REGEX = /^\d+$/;

class CheckoutController {
    constructor({ db, userModel, courseModel, enrollmentModel, paymentModel, auditLogModel, paymentService, passwordService, cache }) {
        Object.assign(this, { db, userModel, courseModel, enrollmentModel, paymentModel, auditLogModel, paymentService, passwordService, cache });
    }

    static validate({ name, email, courseId, card }) {
        if (!name || !email || !courseId || !card) throw new ValidationError('Bad Request');
        if (!EMAIL_REGEX.test(email)) throw new ValidationError('Email inválido');
        if (!CARD_REGEX.test(String(card))) throw new ValidationError('Cartão inválido');
    }

    async findOrCreateUser({ name, email, password }) {
        const existing = await this.userModel.findByEmail(email);
        if (existing) return existing.id;
        const rawPassword = password || this.passwordService.generateRandomPassword();
        return this.userModel.create({ name, email, passwordHash: this.passwordService.hashPassword(rawPassword) });
    }

    async checkout(input) {
        CheckoutController.validate(input);

        const course = await this.courseModel.findActiveById(input.courseId);
        if (!course) throw new NotFoundError('Curso não encontrado');

        const status = this.paymentService.charge(String(input.card), course.price);
        if (status !== PAYMENT_STATUS.PAID) throw new PaymentDeclinedError();

        const { userId, enrollmentId } = await this.db.transaction(async () => {
            const userId = await this.findOrCreateUser(input);
            const enrollmentId = await this.enrollmentModel.create(userId, course.id);
            await this.paymentModel.create(enrollmentId, course.price, status);
            await this.auditLogModel.create(`Checkout curso ${course.id} por ${userId}`);
            return { userId, enrollmentId };
        });

        this.cache.set(`last_checkout_${userId}`, course.title);
        return { msg: 'Sucesso', enrollment_id: enrollmentId };
    }
}

module.exports = CheckoutController;
