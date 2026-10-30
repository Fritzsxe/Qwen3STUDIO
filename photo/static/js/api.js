const API = {
    async _fetch(url, options = {}) {
        try {
            const res = await fetch(url, options);
            if (!res.ok) {
                let errorData;
                try {
                    errorData = await res.json();
                } catch {
                    errorData = { detail: res.statusText };
                }
                throw new Error(errorData.detail || `Erro HTTP ${res.status}`);
            }
            return await res.json();
        } catch (err) {
            console.error(`API Error (${url}):`, err);
            throw err;
        }
    },

    async getStatus() {
        return await this._fetch('/api/status');
    },

    async getDiagnostics() {
        return await this._fetch('/api/diagnostics');
    },

    async listModels() {
        return await this._fetch('/api/models');
    },

    async getHistory() {
        return await this._fetch('/api/history');
    },

    async generateCustom(data) {
        return await this._fetch('/api/generate/custom', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
    },

    async convertMp3(wavPath) {
        return await this._fetch(`/api/convert/mp3?wav_path=${encodeURIComponent(wavPath)}`, {
            method: 'POST'
        });
    },

    async cancelJob(jobId) {
        return await this._fetch(`/api/jobs/${jobId}/cancel`, {
            method: 'POST'
        });
    },

    async getJob(jobId) {
        return await this._fetch(`/api/jobs/${jobId}`);
    },

    getAudioUrl(filename) {
        if (!filename) return '';
        const cleanName = filename.split(/[\\/]/).pop();
        return `/api/audio/${encodeURIComponent(cleanName)}`;
    },

    triggerDownload(url, filename) {
        const a = document.createElement('a');
        a.href = url;
        a.download = filename || 'audio.wav';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
    }
};
