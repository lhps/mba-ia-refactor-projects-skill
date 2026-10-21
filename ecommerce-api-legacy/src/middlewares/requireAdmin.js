const crypto = require('crypto');
const { ForbiddenError } = require('../errors/AppError');

/** Exige X-Admin-Token quando ADMIN_TOKEN está configurado (ambientes sem token mantêm o comportamento legado). */
function createRequireAdmin(adminToken) {
    return (req, res, next) => {
        if (!adminToken) return next();
        const given = Buffer.from(req.get('X-Admin-Token') || '');
        const expected = Buffer.from(adminToken);
        if (given.length !== expected.length || !crypto.timingSafeEqual(given, expected)) {
            return next(new ForbiddenError());
        }
        return next();
    };
}

module.exports = createRequireAdmin;
