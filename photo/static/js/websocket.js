class WSManager {
    constructor() {
        this.socket = null;
        this.listeners = new Map();
        this.reconnectTimeout = null;
        this.isConnected = false;
    }

    connect() {
        if (this.socket && (this.socket.readyState === WebSocket.CONNECTING || this.socket.readyState === WebSocket.OPEN)) {
            return;
        }

        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws`;

        try {
            this.socket = new WebSocket(wsUrl);
        } catch (e) {
            console.warn('WS Init error:', e);
            this._scheduleReconnect();
            return;
        }

        this.socket.onopen = () => {
            console.log('WS Connected');
            this.isConnected = true;
            if (this.reconnectTimeout) {
                clearTimeout(this.reconnectTimeout);
                this.reconnectTimeout = null;
            }
            const openListeners = this.listeners.get('open') || [];
            openListeners.forEach(cb => cb());
        };

        this.socket.onmessage = (event) => {
            try {
                const message = JSON.parse(event.data);
                const typeListeners = this.listeners.get(message.type) || [];
                typeListeners.forEach(cb => cb(message.data !== undefined ? message.data : message));

                // Listener global
                const globalListeners = this.listeners.get('*') || [];
                globalListeners.forEach(cb => cb(message));
            } catch (e) {
                console.error("Erro ao processar WS message:", e);
            }
        };

        this.socket.onclose = () => {
            this.isConnected = false;
            const closeListeners = this.listeners.get('close') || [];
            closeListeners.forEach(cb => cb());
            this._scheduleReconnect();
        };

        this.socket.onerror = (err) => {
            console.warn('WS Socket warning:', err);
        };
    }

    _scheduleReconnect() {
        if (this.reconnectTimeout) return;
        this.reconnectTimeout = setTimeout(() => {
            this.reconnectTimeout = null;
            this.connect();
        }, 2000);
    }

    on(type, callback) {
        if (!this.listeners.has(type)) {
            this.listeners.set(type, []);
        }
        this.listeners.get(type).push(callback);
    }

    off(type, callback) {
        if (!this.listeners.has(type)) return;
        if (!callback) {
            this.listeners.delete(type);
        } else {
            const arr = this.listeners.get(type).filter(cb => cb !== callback);
            this.listeners.set(type, arr);
        }
    }
}

const WS = new WSManager();
