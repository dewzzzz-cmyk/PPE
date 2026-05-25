export function calcSMA(data, period) {
    const result = [];
    for (let i = period - 1; i < data.length; i++) {
        let sum = 0;
        for (let j = i - period + 1; j <= i; j++) sum += data[j].close;
        result.push({ time: data[i].time, value: sum / period });
    }
    return result;
}

export function calcBB(data, period, mult) {
    const upper = [], lower = [];
    for (let i = period - 1; i < data.length; i++) {
        let sum = 0;
        for (let j = i - period + 1; j <= i; j++) sum += data[j].close;
        const mean = sum / period;
        let sqSum = 0;
        for (let j = i - period + 1; j <= i; j++) sqSum += (data[j].close - mean) ** 2;
        const std = Math.sqrt(sqSum / period);
        upper.push({ time: data[i].time, value: mean + mult * std });
        lower.push({ time: data[i].time, value: mean - mult * std });
    }
    return { upper, lower };
}

export function calcRSI(data, period = 14) {
    const result = [];
    if (data.length < period + 1) return result;
    let avgGain = 0, avgLoss = 0;
    for (let i = 1; i <= period; i++) {
        const ch = data[i].close - data[i - 1].close;
        if (ch > 0) avgGain += ch; else avgLoss -= ch;
    }
    avgGain /= period;
    avgLoss /= period;
    result.push({ time: data[period].time, value: avgLoss === 0 ? 100 : 100 - 100 / (1 + avgGain / avgLoss) });
    for (let i = period + 1; i < data.length; i++) {
        const ch = data[i].close - data[i - 1].close;
        avgGain = (avgGain * (period - 1) + (ch > 0 ? ch : 0)) / period;
        avgLoss = (avgLoss * (period - 1) + (ch < 0 ? -ch : 0)) / period;
        result.push({ time: data[i].time, value: avgLoss === 0 ? 100 : 100 - 100 / (1 + avgGain / avgLoss) });
    }
    return result;
}

export function calcMACD(data, fast = 12, slow = 26, sig = 9) {
    if (data.length < slow) return { macd: [], signal: [], histogram: [] };
    const emaF = emaArr(data, fast);
    const emaS = emaArr(data, slow);
    const macdLine = data.map((d, i) => ({ time: d.time, value: emaF[i] - emaS[i] }));
    const k = 2 / (sig + 1);
    const signalLine = [{ time: macdLine[0].time, value: macdLine[0].value }];
    for (let i = 1; i < macdLine.length; i++) {
        signalLine.push({
            time: macdLine[i].time,
            value: macdLine[i].value * k + signalLine[i - 1].value * (1 - k),
        });
    }
    const histogram = macdLine.map((m, i) => {
        const v = m.value - signalLine[i].value;
        return { time: m.time, value: v, color: v >= 0 ? 'rgba(38,166,154,0.5)' : 'rgba(239,83,80,0.5)' };
    });
    return { macd: macdLine, signal: signalLine, histogram };
}

export function calcATR(data, period = 14) {
    const result = [];
    if (data.length < 2) return result;
    const trs = [];
    for (let i = 1; i < data.length; i++) {
        trs.push({
            time: data[i].time,
            value: Math.max(data[i].high - data[i].low, Math.abs(data[i].high - data[i-1].close), Math.abs(data[i].low - data[i-1].close)),
        });
    }
    if (trs.length < period) return result;
    let atr = 0;
    for (let i = 0; i < period; i++) atr += trs[i].value;
    atr /= period;
    result.push({ time: trs[period - 1].time, value: atr });
    for (let i = period; i < trs.length; i++) {
        atr = (atr * (period - 1) + trs[i].value) / period;
        result.push({ time: trs[i].time, value: atr });
    }
    return result;
}

export function detectPatterns(data) {
    const patterns = [];
    for (let i = 2; i < data.length; i++) {
        const c = data[i], p = data[i-1], p2 = data[i-2];
        const body = Math.abs(c.close - c.open);
        const range = c.high - c.low;
        if (range === 0) continue;
        const upper = c.high - Math.max(c.open, c.close);
        const lower = Math.min(c.open, c.close) - c.low;

        if (body / range < 0.1)
            patterns.push({ time: c.time, idx: i, name: 'Doji', dir: 'neutral', conf: 60 });

        if (lower > body * 2 && upper < body * 0.3 && body > 0)
            patterns.push({ time: c.time, idx: i, name: 'Молот', dir: 'bull', conf: 70 });

        if (upper > body * 2 && lower < body * 0.3 && body > 0)
            patterns.push({ time: c.time, idx: i, name: 'Падающая звезда', dir: 'bear', conf: 70 });

        if (p.close < p.open && c.close > c.open && c.open <= p.close && c.close >= p.open)
            patterns.push({ time: c.time, idx: i, name: 'Бычье поглощение', dir: 'bull', conf: 80 });

        if (p.close > p.open && c.close < c.open && c.open >= p.close && c.close <= p.open)
            patterns.push({ time: c.time, idx: i, name: 'Медвежье поглощение', dir: 'bear', conf: 80 });

        const p2body = Math.abs(p2.close - p2.open);
        const p1body = Math.abs(p.close - p.open);
        if (p2.close < p2.open && p2body > 0 && p1body < p2body * 0.3 && c.close > c.open && c.close > (p2.open + p2.close) / 2)
            patterns.push({ time: c.time, idx: i, name: 'Утренняя звезда', dir: 'bull', conf: 85 });

        if (p2.close > p2.open && p2body > 0 && p1body < p2body * 0.3 && c.close < c.open && c.close < (p2.open + p2.close) / 2)
            patterns.push({ time: c.time, idx: i, name: 'Вечерняя звезда', dir: 'bear', conf: 85 });

        if (p2.close > p2.open && p.close > p.open && c.close > c.open &&
            p.open > p2.open && c.open > p.open && p.close > p2.close && c.close > p.close)
            patterns.push({ time: c.time, idx: i, name: 'Три белых солдата', dir: 'bull', conf: 75 });

        if (p2.close < p2.open && p.close < p.open && c.close < c.open &&
            p.open < p2.open && c.open < p.open && p.close < p2.close && c.close < p.close)
            patterns.push({ time: c.time, idx: i, name: 'Три чёрных вороны', dir: 'bear', conf: 75 });

        if (p.close < p.open && c.close > c.open && c.open > p.close && c.close < p.open)
            patterns.push({ time: c.time, idx: i, name: 'Бычий харами', dir: 'bull', conf: 60 });

        if (p.close > p.open && c.close < c.open && c.open < p.close && c.close > p.open)
            patterns.push({ time: c.time, idx: i, name: 'Медвежий харами', dir: 'bear', conf: 60 });
    }
    return patterns;
}

export function findSR(data, win = 5, threshold = 0.01) {
    const levels = [];
    for (let i = win; i < data.length - win; i++) {
        let isH = true, isL = true;
        for (let j = i - win; j <= i + win; j++) {
            if (j === i) continue;
            if (data[j].high >= data[i].high) isH = false;
            if (data[j].low <= data[i].low) isL = false;
        }
        if (isH) levels.push({ price: data[i].high, type: 'resistance', touches: 1 });
        if (isL) levels.push({ price: data[i].low, type: 'support', touches: 1 });
    }
    levels.sort((a, b) => a.price - b.price);
    const clustered = [];
    for (const lv of levels) {
        const ex = clustered.find(c => Math.abs(c.price - lv.price) / lv.price < threshold);
        if (ex) { ex.touches++; ex.price = (ex.price + lv.price) / 2; }
        else clustered.push({ ...lv });
    }
    return clustered.sort((a, b) => b.touches - a.touches).slice(0, 6);
}

export function calcVolSMA(data, period = 20) {
    const result = [];
    for (let i = period - 1; i < data.length; i++) {
        let sum = 0;
        for (let j = i - period + 1; j <= i; j++) sum += data[j].volume;
        result.push({ time: data[i].time, value: sum / period });
    }
    return result;
}

export function generateSignals(data, rsi, macdData, sma20, sma50, bbData) {
    const signals = [];
    const rMap = new Map(), mMap = new Map(), s20 = new Map(), s50 = new Map(), bU = new Map(), bL = new Map();
    for (const r of rsi) rMap.set(tk(r.time), r.value);
    for (let i = 0; i < macdData.macd.length; i++)
        mMap.set(tk(macdData.macd[i].time), { m: macdData.macd[i].value, s: macdData.signal[i].value, h: macdData.histogram[i].value });
    for (const s of sma20) s20.set(tk(s.time), s.value);
    for (const s of sma50) s50.set(tk(s.time), s.value);
    for (const b of bbData.upper) bU.set(tk(b.time), b.value);
    for (const b of bbData.lower) bL.set(tk(b.time), b.value);

    const volSma = calcVolSMA(data, 20);
    const vMap = new Map();
    for (const v of volSma) vMap.set(tk(v.time), v.value);

    for (let i = 1; i < data.length - 1; i++) {
        const key = tk(data[i].time), pkey = tk(data[i-1].time);
        let buy = 0, sell = 0;
        const reasons = [];
        const a = s20.get(key), b = s50.get(key), pa = s20.get(pkey), pb = s50.get(pkey);
        if (a && b && pa && pb) {
            if (pa <= pb && a > b) { buy += 2; reasons.push('Золотой крест SMA'); }
            if (pa >= pb && a < b) { sell += 2; reasons.push('Мёртвый крест SMA'); }
        }
        const r = rMap.get(key);
        if (r !== undefined) {
            if (r < 35) { buy++; reasons.push('RSI перепродан'); }
            if (r > 65) { sell++; reasons.push('RSI перекуплен'); }
        }
        const mc = mMap.get(key), pm = mMap.get(pkey);
        if (mc && pm) {
            if (pm.m <= pm.s && mc.m > mc.s) { buy++; reasons.push('MACD бычий'); }
            if (pm.m >= pm.s && mc.m < mc.s) { sell++; reasons.push('MACD медвежий'); }
        }
        const bl = bL.get(key), bu = bU.get(key);
        if (bl !== undefined && data[i].close <= bl) { buy++; reasons.push('Цена у нижней BB'); }
        if (bu !== undefined && data[i].close >= bu) { sell++; reasons.push('Цена у верхней BB'); }

        const avgVol = vMap.get(key);
        if (avgVol && data[i].volume > avgVol * 1.5) {
            buy++; sell++;
            reasons.push('Всплеск объёма');
        }

        if (buy >= 2) signals.push({ time: data[i].time, type: 'BUY', score: buy, price: data[i].close, low: data[i].low, reasons });
        else if (sell >= 2) signals.push({ time: data[i].time, type: 'SELL', score: sell, price: data[i].close, high: data[i].high, reasons });
    }
    return signals;
}

export function detectRegime(data, sma20, bb, atr) {
    if (data.length < 50 || !sma20.length || !bb.upper.length || !atr.length) return { regime: 'unknown', label: '—' };
    const last = data[data.length - 1];
    const curSma = sma20[sma20.length - 1].value;
    const prevSma = sma20.length > 10 ? sma20[sma20.length - 11].value : curSma;
    const smaSlope = (curSma - prevSma) / prevSma * 100;
    const bbWidth = (bb.upper[bb.upper.length - 1].value - bb.lower[bb.lower.length - 1].value) / curSma * 100;
    const bbWidths = [];
    for (let i = Math.max(0, bb.upper.length - 20); i < bb.upper.length; i++) {
        bbWidths.push((bb.upper[i].value - bb.lower[i].value) / (sma20[Math.min(i, sma20.length - 1)]?.value || curSma) * 100);
    }
    const avgBBW = bbWidths.reduce((a, b) => a + b, 0) / bbWidths.length;
    const curATR = atr[atr.length - 1].value;
    const avgATRs = [];
    for (let i = Math.max(0, atr.length - 20); i < atr.length; i++) avgATRs.push(atr[i].value);
    const avgATR = avgATRs.reduce((a, b) => a + b, 0) / avgATRs.length;
    const volRatio = curATR / avgATR;

    if (volRatio > 1.5 || bbWidth > avgBBW * 1.5) return { regime: 'volatile', label: 'Высокая волатильность', color: '#ff9800', smaSlope, bbWidth, volRatio };
    if (Math.abs(smaSlope) > 1.5) return { regime: smaSlope > 0 ? 'uptrend' : 'downtrend', label: smaSlope > 0 ? 'Восходящий тренд' : 'Нисходящий тренд', color: smaSlope > 0 ? '#26a69a' : '#ef5350', smaSlope, bbWidth, volRatio };
    return { regime: 'flat', label: 'Боковик (флэт)', color: '#787b86', smaSlope, bbWidth, volRatio };
}

export function timeKey(t) {
    if (typeof t === 'string') return t;
    if (typeof t === 'number') return t;
    if (t && t.year !== undefined) return `${t.year}-${String(t.month).padStart(2, '0')}-${String(t.day).padStart(2, '0')}`;
    return '';
}

function tk(t) { return timeKey(t); }
function emaArr(data, period) {
    const k = 2 / (period + 1);
    const r = [data[0].close];
    for (let i = 1; i < data.length; i++) r.push(data[i].close * k + r[i - 1] * (1 - k));
    return r;
}
