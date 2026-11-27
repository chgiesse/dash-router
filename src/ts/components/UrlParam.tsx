import { DashBaseProps } from 'props/dash';
import React, { useEffect, useLayoutEffect, useRef } from 'react';
import {
    Format,
    HistoryMode,
    ResolvedFormat,
    commitGroup,
    decode,
    emptyFor,
    encode,
    inferFormat,
    isEmptyValue,
    isPartialValue,
    queueClear,
    queueSet,
    readParam,
    registerGroupEntry,
    subscribeUrl,
    urlMatches,
    valuesEqual,
} from '../utils/urlState';
import { useChildProp, useDirectUpdate } from '../utils/useChildProp';

interface Props extends DashBaseProps {
    /** A single component whose prop is synced with the URL */
    children: React.ReactNode;
    /** Name of the URL query parameter */
    param: string;
    /** Prop of the child that is synced. Default "value" */
    prop?: string;
    /** How the value is written to the URL: lists comma separated, "json" for objects. "auto" infers it from the child's value. Default "auto" */
    format?: Format;
    /** Query parameters removed whenever this parameter is written (e.g. ["page"]) */
    clear?: string[];
    /** Value the parameter stands for when it is missing from the URL; it is left out of the URL while the child has it. Defaults to the value the layout renders when the URL has no such parameter */
    default?: any;
    /** "push" adds a browser history entry, "replace" does not. Default "push" */
    history?: HistoryMode;
    /** Wait this many milliseconds after the last change before writing the URL. Default 0 */
    debounce?: number;
    /** Also follow later URL changes (back/forward, other parameters clearing this one). Default false */
    twoWay?: boolean;
    /** Defer the write until the group is committed by a UrlCommit (or `commitOn`) */
    group?: string;
    /** Prop of the child that commits the group when it changes, e.g. "n_submit" */
    commitOn?: string;
    /** Parameters written on a commit triggered via `commitOn`, only if the group has a value */
    setParams?: Record<string, string>;
}

/** Syncs one prop of its child with a URL query parameter, without callbacks */
const UrlParam = (props: Props) => {
    const {
        children,
        param,
        prop = 'value',
        format = 'auto',
        clear = [],
        default: defaultValue,
        history = 'push',
        debounce = 0,
        twoWay = false,
        group,
        commitOn,
        setParams = {},
    } = props;

    const child = useChildProp(children, prop);
    const { value, pathKey, hasChild, readProp, setChildProps } = child;
    const { value: commitValue } = useChildProp(children, commitOn);
    const isDirectUpdate = useDirectUpdate(child.readUpdateEntry);

    const effectiveGroup = group ?? (commitOn ? `__url_param:${param}` : undefined);

    // --- format and default ------------------------------------------------------
    // Re-derived whenever a new layout arrives from the server: when the URL has
    // no such param, the value the layout renders is the default.
    const fmt = useRef<ResolvedFormat>('string');
    const fallback = useRef<any>(null);
    const baselined = useRef(false);

    const baseline = (v: any) => {
        if (format !== 'auto') fmt.current = format;
        else if (!baselined.current || !isEmptyValue(v)) fmt.current = inferFormat(v);
        if (defaultValue !== undefined) fallback.current = defaultValue;
        else if (readParam(param) === null) fallback.current = v;
        else if (!baselined.current) fallback.current = emptyFor(fmt.current);
        baselined.current = true;
    };
    if (!baselined.current) baseline(value);

    const encodeValue = (v: any) =>
        valuesEqual(v, fallback.current, fmt.current) ? null : encode(v, fmt.current);

    const latestClear = useRef(clear);
    latestClear.current = clear;

    // --- URL -> child (twoWay): on mount and on every URL change ----------------
    // Without twoWay the layout is built from the URL, and the value Python
    // renders wins (it may normalise the URL value, e.g. clamp a step).
    useLayoutEffect(() => {
        if (!hasChild || !twoWay) return undefined;
        const sync = () => {
            const current = readProp(prop);
            if (urlMatches(param, current, fmt.current, fallback.current)) return;
            const raw = readParam(param);
            const next = raw === null ? fallback.current : decode(raw, fmt.current);
            // leave the child alone when the URL holds something it can't take
            if (raw !== null && raw !== '' && next === null) return;
            setChildProps({ [prop]: next });
        };
        sync();
        return subscribeUrl(sync);
    }, [pathKey, param, prop, twoWay]);

    // --- child -> URL (immediate mode) ------------------------------------------
    useEffect(() => {
        if (!isDirectUpdate(prop)) {
            // replaced by a new layout, not changed by the user or a callback
            baseline(value);
            return undefined;
        }
        if (effectiveGroup || isPartialValue(value)) return undefined;
        if (urlMatches(param, value, fmt.current, fallback.current)) return undefined;

        const write = () => {
            // the URL may have changed while waiting
            if (urlMatches(param, value, fmt.current, fallback.current)) return;
            queueSet(param, encodeValue(value), history);
            queueClear(latestClear.current ?? [], history);
        };
        if (!debounce) {
            write();
            return undefined;
        }
        const timer = setTimeout(write, debounce);
        return () => clearTimeout(timer);
    }, [value]);

    // --- deferred mode: the group reads the current value at commit time --------
    useEffect(() => {
        if (!effectiveGroup || !hasChild) return undefined;
        return registerGroupEntry(effectiveGroup, {
            param,
            read: () => {
                const current = readProp(prop);
                if (isPartialValue(current)) return null;
                return { value: current, encoded: encodeValue(current) };
            },
        });
    }, [effectiveGroup, pathKey, param, prop]);

    // --- commitOn: a prop of the child (e.g. n_submit) commits the group --------
    useEffect(() => {
        if (!commitOn || !effectiveGroup) return;
        if (!isDirectUpdate(commitOn) || commitValue === undefined || commitValue === null) {
            return;
        }
        commitGroup(effectiveGroup, latestClear.current ?? [], setParams, history);
    }, [commitValue]);

    return <>{children}</>;
};

export default UrlParam;
