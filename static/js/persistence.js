const Persistence = {
    KEY: 'qwen3_studio_state',

    save(data) {
        const current = this.load();
        const updated = { ...current, ...data };
        localStorage.setItem(this.KEY, JSON.stringify(updated));
    },

    load() {
        try {
            return JSON.parse(localStorage.getItem(this.KEY)) || {};
        } catch {
            return {};
        }
    },

    clear() {
        localStorage.removeItem(this.KEY);
    }
};
