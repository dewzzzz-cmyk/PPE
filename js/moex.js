export async function fetchCandles(ticker, interval, days) {
    const end = new Date().toISOString().slice(0, 10);
    const start = new Date(Date.now() - days * 86400000).toISOString().slice(0, 10);
    const base = 'https://iss.moex.com/iss/engines/stock/markets/shares/securities';
    let allRows = [], cursor = 0;

    while (true) {
        const url = `${base}/${ticker}/candles.json?from=${start}&till=${end}&interval=${interval}&start=${cursor}&iss.meta=off`;
        const resp = await fetch(url);
        const data = await resp.json();
        const rows = data.candles.data;
        if (!rows.length) break;
        allRows = allRows.concat(rows);
        cursor += rows.length;
        if (rows.length < 500) break;
    }

    return allRows.map(r => ({
        time: interval === 24 || interval === 7 || interval === 31
            ? r[6].slice(0, 10)
            : Math.floor(new Date(r[6]).getTime() / 1000),
        open: r[0], close: r[1], high: r[2], low: r[3], volume: r[5],
    }));
}

export async function fetchPrices(tickers) {
    const url = `https://iss.moex.com/iss/engines/stock/markets/shares/securities.json?securities=${tickers.join(',')}&iss.meta=off&iss.only=securities,marketdata`;
    const resp = await fetch(url);
    const data = await resp.json();
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
            last,
            change: r[ci(mktCols, 'LASTCHANGEPCT')] ?? null,
            volume: r[ci(mktCols, 'VOLTODAY')],
            time: r[ci(mktCols, 'UPDATETIME')] || '',
        });
    }
    return result;
}
