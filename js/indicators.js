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

function emaArr(data, period) {
    const k = 2 / (period + 1);
    const r = [data[0].close];
    for (let i = 1; i < data.length; i++) r.push(data[i].close * k + r[i - 1] * (1 - k));
    return r;
}
