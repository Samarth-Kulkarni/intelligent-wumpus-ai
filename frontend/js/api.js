const API_BASE = '/api';

const wumpusApi = {
    async init(size = 4) {
        const res = await fetch(`${API_BASE}/init`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ size })
        });
        return res.json();
    },

    async step(action) {
        const res = await fetch(`${API_BASE}/step`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action })
        });
        return res.json();
    },

    async getState() {
        const res = await fetch(`${API_BASE}/state`);
        return res.json();
    }
};
