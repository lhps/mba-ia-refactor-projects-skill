const { NotFoundError } = require('../errors/AppError');

class UserController {
    constructor({ db, userModel, enrollmentModel, paymentModel, logger }) {
        Object.assign(this, { db, userModel, enrollmentModel, paymentModel, logger });
    }

    /** Remove usuário com matrículas e pagamentos, sem deixar registros órfãos. */
    async deleteUser(id) {
        const user = await this.userModel.findById(id);
        if (!user) throw new NotFoundError('Usuário não encontrado');

        await this.db.transaction(async () => {
            await this.paymentModel.deleteByUserId(id);
            await this.enrollmentModel.deleteByUserId(id);
            await this.userModel.delete(id);
        });
        this.logger.info('Usuário removido com dependentes', { userId: Number(id) });
    }
}

module.exports = UserController;
