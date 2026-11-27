/**
 * Shared URL state for UrlParam / UrlCommit.
 *
 * Writes are batched per tick and only real changes reach the history, so a
 * value that already matches the URL never causes a navigation. dcc.Location
 * instances (e.g. the router's `dash-router-location`) pick up the change
 * through `_dashprivate_pushstate`, the same event dcc.Link uses.
 *
 * Lists are comma separated in the URL (`?tags=a,b`).
 */
export function deepEqual(a: any, b: any): boolean {
    if (Object.is(a, b)) return true;
    if (a == null || b == null || typeof a !== 'object' || typeof b !== 'object') {
        return false;
    }
    const arrayA = Array.isArray(a);
    if (arrayA !== Array.isArray(b)) return false;
    if (arrayA) {
        if (a.length !== b.length) return false;
        for (let i = 0; i < a.length; i++) {
            if (!deepEqual(a[i], b[i])) return false;
        }
        return true;
    }
    if (Object.getPrototypeOf(a) !== Object.getPrototypeOf(b)) return false;
    const keysA = Object.keys(a);
    if (keysA.length !== Object.keys(b).length) return false;
    for (let i = 0; i < keysA.length; i++) {
        const k = keysA[i];
        if (!Object.prototype.hasOwnProperty.call(b, k) || !deepEqual(a[k], b[k])) {
            return false;
        }
    }
    return true;
}

export type Format = 'auto' | 'string' | 'list' | 'number' | 'boolean' | 'json';
export type ResolvedFormat = Exclude<Format, 'auto'>;
export type HistoryMode = 'push' | 'replace';

const PUSH_EVENT = '_dashprivate_pushstate';

// --- values -------------------------------------------------------------------

/** Whitespace-only text counts as empty (pasted or space-only search terms) */
const isBlank = (v: any) =>
    v === null || v === undefined || (typeof v === 'string' && v.trim() === '');

/** Text is trimmed before it is written or compared */
const clean = (v: any) => (typeof v === 'string' ? v.trim() : v);

export const isEmptyValue = (v: any) =>
    isBlank(v) || (Array.isArray(v) && v.every(isBlank));

/** A range with only one end picked, e.g. a half-selected date range */
export const isPartialValue = (v: any) =>
    Array.isArray(v) && v.length > 1 && v.some(isBlank) && !v.every(isBlank);

export const inferFormat = (v: any): ResolvedFormat => {
    if (Array.isArray(v)) return 'list';
    if (typeof v === 'number') return 'number';
    if (typeof v === 'boolean') return 'boolean';
    if (v !== null && typeof v === 'object') return 'json';
    return 'string';
};

export const emptyFor = (fmt: ResolvedFormat) => (fmt === 'list' ? [] : null);

export function encode(v: any, fmt: ResolvedFormat): string | null {
    if (isEmptyValue(v)) return null;
    if (fmt === 'json') return JSON.stringify(v);
    if (Array.isArray(v)) return v.map(clean).join(',');
    return String(clean(v));
}

export function decode(raw: string, fmt: ResolvedFormat): any {
    switch (fmt) {
        case 'list':
            return raw === '' ? [] : raw.split(',').map((x) => x.trim());
        case 'number': {
            const n = Number(raw);
            return raw === '' || Number.isNaN(n) ? null : n;
        }
        case 'boolean':
            return raw === 'true';
        case 'json':
            try {
                return JSON.parse(raw);
            } catch {
                return null;
            }
        default:
            return raw;
    }
}

const setOf = (a: any[]) =>
    new Set(a.filter((x) => !isBlank(x)).map((x) => String(clean(x))));

/** Lists compare as sets (order and duplicates don't matter) */
export function valuesEqual(a: any, b: any, fmt: ResolvedFormat): boolean {
    if (isEmptyValue(a) && isEmptyValue(b)) return true;
    if (fmt === 'list' && Array.isArray(a) && Array.isArray(b)) {
        const sa = setOf(a);
        const sb = setOf(b);
        return sa.size === sb.size && Array.from(sa).every((x) => sb.has(x));
    }
    return deepEqual(clean(a), clean(b));
}

export const readParam = (param: string) =>
    new URLSearchParams(window.location.search).get(param);

/** Value the URL currently stands for (`fallback` when the param is missing) */
export const urlValue = (param: string, fmt: ResolvedFormat, fallback: any) => {
    const raw = readParam(param);
    return raw === null ? fallback : decode(raw, fmt);
};

/** True if the URL already represents `value` for this param */
export const urlMatches = (
    param: string,
    value: any,
    fmt: ResolvedFormat,
    fallback: any
) => valuesEqual(urlValue(param, fmt, fallback), value, fmt);

// --- batched writes -------------------------------------------------------------

const pending = new Map<string, string | null>();
let pendingMode: HistoryMode = 'replace';
let scheduled = false;

function schedule(mode: HistoryMode) {
    if (mode === 'push') pendingMode = 'push';
    if (!scheduled) {
        scheduled = true;
        queueMicrotask(flush);
    }
}

/** Set (or remove with `null`) a param. Overrides anything queued before. */
export function queueSet(param: string, encoded: string | null, mode: HistoryMode) {
    pending.set(param, encoded);
    schedule(mode);
}

/** Remove params, unless a value was queued for them in the same tick */
export function queueClear(params: string[], mode: HistoryMode) {
    params.forEach((p) => {
        if (!pending.has(p)) pending.set(p, null);
    });
    if (params.length) schedule(mode);
}

function flush() {
    scheduled = false;
    const params = new URLSearchParams(window.location.search);
    let changed = false;

    pending.forEach((v, k) => {
        // get() decodes, so "%2C" vs "," never counts as a change
        if (params.get(k) === v) return;
        if (v === null) params.delete(k);
        else params.set(k, v);
        changed = true;
    });

    const mode = pendingMode;
    pending.clear();
    pendingMode = 'replace';
    if (!changed) return;

    const search = params.toString().replace(/%2C/gi, ',');
    pushUrl(
        window.location.pathname + (search ? '?' + search : '') + window.location.hash,
        mode
    );
}

/** Single write path for URL changes. Skips the write when the URL already matches. */
export function pushUrl(url: string, mode: HistoryMode) {
    const current = window.location.pathname + window.location.search + window.location.hash;
    if (url === current) return;
    if (mode === 'push') window.history.pushState({}, '', url);
    else window.history.replaceState({}, '', url);
    window.dispatchEvent(new CustomEvent(PUSH_EVENT));
}

export function subscribeUrl(cb: () => void) {
    window.addEventListener('popstate', cb);
    window.addEventListener(PUSH_EVENT, cb);
    return () => {
        window.removeEventListener('popstate', cb);
        window.removeEventListener(PUSH_EVENT, cb);
    };
}

// --- deferred groups --------------------------------------------------------------

export type GroupEntry = {
    param: string;
    /** Current value of the child, read at commit time */
    read: () => { value: any; encoded: string | null } | null;
};

const groups = new Map<string, Set<GroupEntry>>();

export function registerGroupEntry(group: string, entry: GroupEntry) {
    let entries = groups.get(group);
    if (!entries) {
        entries = new Set();
        groups.set(group, entries);
    }
    entries.add(entry);
    return () => {
        entries.delete(entry);
        if (!entries.size) groups.delete(group);
    };
}

/**
 * Write all params of a group. `setParams` are written only if at least one
 * param of the group has a value, otherwise they are removed. Without a group
 * only `setParams` and `clear` are applied.
 */
export function commitGroup(
    group: string | undefined,
    clear: string[],
    setParams: Record<string, string>,
    mode: HistoryMode
) {
    // without a group, setParams are always written
    let anyValue = !group;
    ((group && groups.get(group)) || new Set<GroupEntry>()).forEach((entry) => {
        const current = entry.read();
        if (!current) return;
        if (!isEmptyValue(current.value)) anyValue = true;
        queueSet(entry.param, current.encoded, mode);
    });
    Object.keys(setParams).forEach((k) =>
        queueSet(k, anyValue ? setParams[k] : null, mode)
    );
    queueClear(clear, mode);
}
