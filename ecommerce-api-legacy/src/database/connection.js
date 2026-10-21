const sqlite3 = require('sqlite3');

/** Wrapper Promise sobre o driver sqlite3 (callbacks) com suporte a transações serializadas. */
class Database {
    constructor(path) {
        this.db = new sqlite3.Database(path);
        this.txQueue = Promise.resolve();
    }

    run(sql, params = []) {
        return new Promise((resolve, reject) => {
            this.db.run(sql, params, function onRun(err) {
                if (err) return reject(err);
                resolve({ lastID: this.lastID, changes: this.changes });
            });
        });
    }

    get(sql, params = []) {
        return new Promise((resolve, reject) => {
            this.db.get(sql, params, (err, row) => (err ? reject(err) : resolve(row)));
        });
    }

    all(sql, params = []) {
        return new Promise((resolve, reject) => {
            this.db.all(sql, params, (err, rows) => (err ? reject(err) : resolve(rows)));
        });
    }

    exec(sql) {
        return new Promise((resolve, reject) => {
            this.db.exec(sql, (err) => (err ? reject(err) : resolve()));
        });
    }

    /** Executa `work` entre BEGIN/COMMIT; transações concorrentes são enfileiradas (conexão única). */
    transaction(work) {
        const result = this.txQueue.then(async () => {
            await this.run('BEGIN');
            try {
                const value = await work();
                await this.run('COMMIT');
                return value;
            } catch (err) {
                await this.run('ROLLBACK');
                throw err;
            }
        });
        this.txQueue = result.catch(() => {});
        return result;
    }

    close() {
        return new Promise((resolve, reject) => this.db.close((err) => (err ? reject(err) : resolve())));
    }
}

module.exports = Database;
