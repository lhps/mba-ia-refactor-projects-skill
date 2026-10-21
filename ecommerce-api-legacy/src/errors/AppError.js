class AppError extends Error {
    constructor(message, status = 400) {
        super(message);
        this.status = status;
    }
}

class ValidationError extends AppError {
    constructor(message = 'Bad Request') { super(message, 400); }
}

class NotFoundError extends AppError {
    constructor(message) { super(message, 404); }
}

class PaymentDeclinedError extends AppError {
    constructor(message = 'Pagamento recusado') { super(message, 400); }
}

class ForbiddenError extends AppError {
    constructor(message = 'Acesso negado') { super(message, 403); }
}

module.exports = { AppError, ValidationError, NotFoundError, PaymentDeclinedError, ForbiddenError };
