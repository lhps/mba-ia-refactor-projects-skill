const express = require('express');

const config = require('./config');
const { createLogger } = require('./config/logger');
const Database = require('./database/connection');
const { initDatabase } = require('./database/schema');
const UserModel = require('./models/user.model');
const CourseModel = require('./models/course.model');
const EnrollmentModel = require('./models/enrollment.model');
const { PaymentModel } = require('./models/payment.model');
const AuditLogModel = require('./models/auditLog.model');
const passwordService = require('./services/password.service');
const PaymentService = require('./services/payment.service');
const CacheService = require('./services/cache.service');
const CheckoutController = require('./controllers/checkout.controller');
const ReportController = require('./controllers/report.controller');
const UserController = require('./controllers/user.controller');
const createCheckoutRoutes = require('./routes/checkout.routes');
const createAdminRoutes = require('./routes/admin.routes');
const createUserRoutes = require('./routes/user.routes');
const createRequireAdmin = require('./middlewares/requireAdmin');
const createErrorHandler = require('./middlewares/errorHandler');

/** Composition root: instancia dependências e monta a aplicação Express. */
async function createApp(appConfig = config) {
    const logger = createLogger(appConfig.logLevel);
    const db = new Database(appConfig.dbPath);
    await initDatabase(db, passwordService);

    const userModel = new UserModel(db);
    const courseModel = new CourseModel(db);
    const enrollmentModel = new EnrollmentModel(db);
    const paymentModel = new PaymentModel(db);
    const auditLogModel = new AuditLogModel(db);

    const paymentService = new PaymentService({ gatewayKey: appConfig.paymentGatewayKey, logger });
    const cache = new CacheService({ logger });

    const checkoutController = new CheckoutController({
        db, userModel, courseModel, enrollmentModel, paymentModel, auditLogModel, paymentService, passwordService, cache,
    });
    const reportController = new ReportController({ courseModel });
    const userController = new UserController({ db, userModel, enrollmentModel, paymentModel, logger });

    const requireAdmin = createRequireAdmin(appConfig.adminToken);

    const app = express();
    app.use(express.json());
    app.use(createCheckoutRoutes(checkoutController));
    app.use(createAdminRoutes(reportController, requireAdmin));
    app.use(createUserRoutes(userController, requireAdmin));
    app.use(createErrorHandler(logger));

    return { app, logger };
}

if (require.main === module) {
    createApp()
        .then(({ app, logger }) => {
            app.listen(config.port, () => logger.info(`LMS API rodando na porta ${config.port}`));
        })
        .catch((err) => {
            console.error('Falha ao iniciar a aplicação', err);
            process.exit(1);
        });
}

module.exports = { createApp };
