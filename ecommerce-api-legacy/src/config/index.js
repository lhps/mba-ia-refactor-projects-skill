const config = Object.freeze({
    port: Number(process.env.PORT) || 3000,
    dbPath: process.env.DB_PATH || ':memory:',
    paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY || '',
    smtpUser: process.env.SMTP_USER || '',
    // Quando definido, rotas administrativas/destrutivas exigem o header X-Admin-Token.
    adminToken: process.env.ADMIN_TOKEN || '',
    logLevel: process.env.LOG_LEVEL || 'info',
});

module.exports = config;
