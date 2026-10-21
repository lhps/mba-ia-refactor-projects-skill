const { PAYMENT_STATUS } = require('../models/payment.model');

// Gateway simulado: cartões iniciados com este prefixo são aprovados.
const APPROVED_CARD_PREFIX = '4';

class PaymentService {
    constructor({ gatewayKey, logger }) {
        this.gatewayKey = gatewayKey;
        this.logger = logger;
    }

    charge(card, amount) {
        // Nunca registrar número completo do cartão nem a chave do gateway.
        this.logger.info('Processando pagamento', { last4: card.slice(-4), amount });
        return card.startsWith(APPROVED_CARD_PREFIX) ? PAYMENT_STATUS.PAID : PAYMENT_STATUS.DENIED;
    }
}

module.exports = PaymentService;
