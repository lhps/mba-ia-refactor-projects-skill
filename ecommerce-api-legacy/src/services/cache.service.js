class CacheService {
    constructor({ logger, maxEntries = 1000 }) {
        this.logger = logger;
        this.maxEntries = maxEntries;
        this.store = new Map();
    }

    set(key, value) {
        if (this.store.size >= this.maxEntries) {
            this.store.delete(this.store.keys().next().value);
        }
        this.store.set(key, value);
        this.logger.debug('Cache atualizado', { key });
    }

    get(key) {
        return this.store.get(key);
    }
}

module.exports = CacheService;
