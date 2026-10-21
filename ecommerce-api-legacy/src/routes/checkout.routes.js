const express = require('express');
const asyncHandler = require('../middlewares/asyncHandler');

// Contrato externo mantido (usr, eml, pwd, c_id, card) e mapeado para nomes internos claros.
const toCheckoutInput = (body = {}) => ({
    name: body.usr,
    email: body.eml,
    password: body.pwd,
    courseId: body.c_id,
    card: body.card,
});

function createCheckoutRoutes(checkoutController) {
    const router = express.Router();

    router.post('/api/checkout', asyncHandler(async (req, res) => {
        const result = await checkoutController.checkout(toCheckoutInput(req.body));
        res.status(200).json(result);
    }));

    return router;
}

module.exports = createCheckoutRoutes;
