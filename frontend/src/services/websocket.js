class PharmaIQWebSocket {
  constructor() {
    this.ws = null;
    this.listeners = {};
    this.reconnectTimer = null;
    this.connected = false;
    this.pingTimer = null;
  }

  connect() {
    try {
      this.ws = new WebSocket('ws://localhost:8001/ws');

      this.ws.onopen = () => {
        this.connected = true;
        this._emit('connected', {});
        this._startPing();
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this._emit(data.type, data);
          this._emit('any', data);
        } catch (e) {
          console.error('WS parse error:', e);
        }
      };

      this.ws.onclose = () => {
        this.connected = false;
        this._emit('disconnected', {});
        if (this.pingTimer) clearInterval(this.pingTimer);
        this.reconnectTimer = setTimeout(() => this.connect(), 3000);
      };

      this.ws.onerror = () => {
        this.connected = false;
      };
    } catch (e) {
      this.reconnectTimer = setTimeout(() => this.connect(), 3000);
    }
  }

  on(event, callback) {
    if (!this.listeners[event]) this.listeners[event] = [];
    this.listeners[event].push(callback);
    return () => this.off(event, callback);
  }

  off(event, callback) {
    if (this.listeners[event]) {
      this.listeners[event] = this.listeners[event].filter(
        (cb) => cb !== callback
      );
    }
  }

  _emit(event, data) {
    (this.listeners[event] || []).forEach((cb) => {
      try {
        cb(data);
      } catch (e) {
        console.error('WS listener error:', e);
      }
    });
  }

  _startPing() {
    this.pingTimer = setInterval(() => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({ type: 'ping' }));
      }
    }, 30000);
  }

  disconnect() {
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer);
    if (this.pingTimer) clearInterval(this.pingTimer);
    if (this.ws) this.ws.close();
  }
}

export const wsClient = new PharmaIQWebSocket();