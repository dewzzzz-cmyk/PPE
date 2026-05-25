const FETCH_TIMEOUT = 10000;
const MAX_RETRIES = 2;

async function fetchWithRetry(url) {
    for (let attempt = 0; attempt <= MAX_RETRIES; attempt++) {
        const ctrl = new AbortController();
        const timer = setTimeout(() => ctrl.abort(), FETCH_TIMEOUT);
        try {
            const resp = await fetch(url, { signal: ctrl.signal });
            clearTimeout(timer);
            if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
            return await resp.json();
        } catch (e) {
            clearTimeout(timer);
            if (attempt === MAX_RETRIES) throw e;
            await new Promise(r => setTimeout(r, 1000 * (attempt + 1)));
        }
    }
}

function parseMoscowTime(dateStr) {
    if (!dateStr) return 0;
    const clean = dateStr.replace(' ', 'T');
    if (/[+-]\d{2}:?\d{2}$/.test(clean) || clean.endsWith('Z')) return Math.floor(new Date(clean).getTime() / 1000);
    return Math.floor(new Date(clean + '+03:00').getTime() / 1000);
}

export async function fetchCandles(ticker, interval, days) {
    const end = new Date().toISOString().slice(0, 10);
    const start = new Date(Date.now() - days * 86400000).toISOString().slice(0, 10);
    const base = 'https://iss.moex.com/iss/engines/stock/markets/shares/securities';
    let allRows = [], cursor = 0;

    while (true) {
        const url = `${base}/${ticker}/candles.json?from=${start}&till=${end}&interval=${interval}&start=${cursor}&iss.meta=off`;
        const data = await fetchWithRetry(url);
        const rows = data.candles.data;
        if (!rows.length) break;
        allRows = allRows.concat(rows);
        cursor += rows.length;
        if (rows.length < 500) break;
    }

    return allRows.map(r => ({
        time: interval === 24 || interval === 7 || interval === 31
            ? r[6].slice(0, 10)
            : parseMoscowTime(r[6]),
        open: r[0], close: r[1], high: r[2], low: r[3], volume: r[5],
    }));
}

export async function fetchPrices(tickers) {
    const url = `https://iss.moex.com/iss/engines/stock/markets/shares/securities.json?securities=${tickers.join(',')}&iss.meta=off&iss.only=securities,marketdata`;
    const data = await fetchWithRetry(url);
    const secCols = data.securities.columns;
    const mktCols = data.marketdata.columns;
    const ci = (cols, name) => cols.indexOf(name);
    const secMap = {};
    for (const r of data.securities.data) {
        const id = r[ci(secCols, 'SECID')];
        if (!secMap[id]) secMap[id] = { shortname: r[ci(secCols, 'SHORTNAME')] };
    }
    const result = [];
    const seen = new Set();
    for (const r of data.marketdata.data) {
        const id = r[ci(mktCols, 'SECID')];
        if (seen.has(id)) continue;
        const last = r[ci(mktCols, 'LAST')];
        if (last == null) continue;
        seen.add(id);
        result.push({
            ticker: id,
            shortname: secMap[id]?.shortname || id,
            last, change: r[ci(mktCols, 'LASTCHANGEPCT')] ?? null,
            volume: r[ci(mktCols, 'VOLTODAY')],
            time: r[ci(mktCols, 'UPDATETIME')] || '',
        });
    }
    return result;
}

export async function fetchOrderBook(ticker) {
    const url = `https://iss.moex.com/iss/engines/stock/markets/shares/boards/TQBR/securities/${ticker}/orderbook.json?iss.meta=off`;
    const data = await fetchWithRetry(url);
    const cols = data.orderbook.columns;
    const ci = (name) => cols.indexOf(name);
    const bids = [], asks = [];
    for (const row of data.orderbook.data) {
        const entry = { price: row[ci('PRICE')], quantity: row[ci('QUANTITY')] };
        if (row[ci('BUYSELL')] === 'B') bids.push(entry);
        else asks.push(entry);
    }
    bids.sort((a, b) => b.price - a.price);
    asks.sort((a, b) => a.price - b.price);
    return { bids: bids.slice(0, 15), asks: asks.slice(0, 15) };
}
