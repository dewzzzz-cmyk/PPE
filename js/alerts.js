const KEY = 'moex_alerts';
let audioCtx = null;

export function loadAlerts() {
    try { return JSON.parse(localStorage.getItem(KEY) || '[]'); } catch { return []; }
}

export function saveAlerts(alerts) {
    localStorage.setItem(KEY, JSON.stringify(alerts));
}

export function addAlert(ticker, price, direction) {
    const alerts = loadAlerts();
    alerts.push({ id: Date.now(), ticker, price, direction, active: true, created: new Date().toISOString() });
    saveAlerts(alerts);
    return alerts;
}

export function removeAlert(id) {
    const alerts = loadAlerts().filter(a => a.id !== id);
    saveAlerts(alerts);
    return alerts;
}

export function checkAlerts(ticker, currentPrice) {
    const alerts = loadAlerts();
    const triggered = [];
    for (const a of alerts) {
        if (!a.active || a.ticker !== ticker) continue;
        if ((a.direction === 'above' && currentPrice >= a.price) ||
            (a.direction === 'below' && currentPrice <= a.price)) {
            triggered.push(a);
            a.active = false;
        }
    }
    if (triggered.length) {
        saveAlerts(alerts);
        triggered.forEach(a => { playSound(); showNotif(a); });
    }
    return triggered;
}

function playSound() {
    try {
        if (!audioCtx) audioCtx = new AudioContext();
        const osc = audioCtx.createOscillator();
        const gain = audioCtx.createGain();
        osc.connect(gain); gain.connect(audioCtx.destination);
        osc.frequency.value = 880; osc.type = 'sine'; gain.gain.value = 0.3;
        osc.start();
        gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.5);
        osc.stop(audioCtx.currentTime + 0.5);
    } catch {}
}

function showNotif(alert) {
    if ('Notification' in window && Notification.permission === 'granted') {
        new Notification(`MOEX: ${alert.ticker}`, {
            body: `Цена ${alert.direction === 'above' ? 'выше' : 'ниже'} ${alert.price.toFixed(2)}`,
        });
    }
}

export function requestPermission() {
    if ('Notification' in window && Notification.permission === 'default') Notification.requestPermission();
}
