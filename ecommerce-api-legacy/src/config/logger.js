const LEVELS = { error: 0, warn: 1, info: 2, debug: 3 };

function createLogger(level = 'info') {
    const threshold = LEVELS[level] ?? LEVELS.info;
    const log = (name) => (message, meta) => {
        if (LEVELS[name] > threshold) return;
        const line = `[${new Date().toISOString()}] ${name.toUpperCase()} ${message}`;
        (name === 'error' ? console.error : console.log)(meta ? `${line} ${JSON.stringify(meta)}` : line);
    };
    return { error: log('error'), warn: log('warn'), info: log('info'), debug: log('debug') };
}

module.exports = { createLogger };
