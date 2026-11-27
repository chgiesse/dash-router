import { DashBaseProps } from 'props/dash';
import React, { useEffect } from 'react';
import { HistoryMode, commitGroup } from '../utils/urlState';
import { useChildProp, useDirectUpdate } from '../utils/useChildProp';

interface Props extends DashBaseProps {
    /** A single component that commits, e.g. an apply button */
    children: React.ReactNode;
    /** Group of UrlParam components (`group=...`) that is written to the URL. Without a group only `setParams` / `clear` are applied */
    group?: string;
    /** Prop of the child that triggers the commit when it changes. Default "n_clicks" */
    prop?: string;
    /** Query parameters removed on commit (e.g. ["page"]) */
    clear?: string[];
    /** Parameters written on commit. With a group only if at least one of its parameters has a value (otherwise they are removed) */
    setParams?: Record<string, string>;
    /** "push" adds a browser history entry, "replace" does not. Default "push" */
    history?: HistoryMode;
}

/** Writes a group of deferred UrlParam values (and/or fixed parameters) to the URL when its child fires */
const UrlCommit = ({
    children,
    group,
    prop = 'n_clicks',
    clear = [],
    setParams = {},
    history = 'push',
}: Props) => {
    const { value, readUpdateEntry } = useChildProp(children, prop);
    const isDirectUpdate = useDirectUpdate(readUpdateEntry);

    useEffect(() => {
        // also skips a new layout from the server resetting n_clicks
        if (!isDirectUpdate(prop) || value === undefined || value === null) return;
        commitGroup(group, clear, setParams, history);
    }, [value]);

    return <>{children}</>;
};

export default UrlCommit;
