import { DashBaseProps } from 'props/dash';
import React, { useEffect, useLayoutEffect } from 'react';
import { HistoryMode, pushUrl, subscribeUrl } from '../utils/urlState';
import { useChildProp, useDirectUpdate } from '../utils/useChildProp';

interface Props extends DashBaseProps {
    /** A single component whose prop is synced with a URL path segment */
    children: React.ReactNode;
    /** Browser path of the parent, without trailing slash, e.g. "/orders/1003" ("" for the root) */
    base: string;
    /** Prop of the child that is synced. Default "value" */
    prop?: string;
    /** Segment the bare `base` URL stands for; selecting it writes `base` without the segment */
    default?: string;
    /** "push" adds a browser history entry, "replace" does not. Default "push" */
    history?: HistoryMode;
    /** Keep the query string when the segment is written. Default true */
    keepQuery?: boolean;
}

const BARE = 'bare';

const decodeSafe = (s: string) => {
    try {
        return decodeURIComponent(s);
    } catch {
        return s;
    }
};

const samePath = (a: string, b: string) =>
    decodeSafe(a).replace(/\/+$/, '') === decodeSafe(b).replace(/\/+$/, '');

/** The segment after `base` (`BARE` for the bare base path, `null` for other paths) */
const segmentOf = (pathname: string, base: string): string | typeof BARE | null => {
    if (pathname === base || pathname === base + '/') return BARE;
    if (!pathname.startsWith(base + '/')) return null;
    const segment = pathname.slice(base.length + 1).split('/')[0];
    return segment === '' ? BARE : decodeSafe(segment);
};

/** Syncs one prop of its child with a URL path segment, e.g. the active tab of `/orders/1003/<tab>` */
const UrlSegment = (props: Props) => {
    const {
        children,
        base,
        prop = 'value',
        default: defaultSegment,
        history = 'push',
        keepQuery = true,
    } = props;

    const child = useChildProp(children, prop);
    const { value, pathKey, hasChild, readProp, setChildProps } = child;
    const isDirectUpdate = useDirectUpdate(child.readUpdateEntry);

    const pathFor = (v: any) => {
        const empty = v === null || v === undefined || v === '';
        if (empty || v === defaultSegment) return base || '/';
        return `${base}/${encodeURIComponent(String(v))}`;
    };

    // --- child -> URL: a user change of the child's prop -------------------------
    useEffect(() => {
        if (!isDirectUpdate(prop) || !hasChild) return;
        const { pathname, search: currentSearch, hash } = window.location;
        const path = pathFor(value);
        const search = keepQuery ? currentSearch : '';
        // the URL may already show this segment, e.g. after a sync from the URL
        if (samePath(pathname, path) && (!keepQuery || currentSearch === search)) {
            return;
        }
        pushUrl(path + search + hash, history);
    }, [value]);

    // --- URL -> child: on mount and on every URL change --------------------------
    useLayoutEffect(() => {
        if (!hasChild) return undefined;
        const sync = () => {
            const segment = segmentOf(window.location.pathname, base);
            if (segment === null) return;
            let next: any;
            if (segment === BARE) {
                if (defaultSegment === undefined) return;
                next = defaultSegment;
            } else {
                next = segment;
            }
            if (readProp(prop) === next) return;
            setChildProps({ [prop]: next });
        };
        sync();
        return subscribeUrl(sync);
    }, [pathKey, base, prop, defaultSegment]);

    return <>{children}</>;
};

export default UrlSegment;
