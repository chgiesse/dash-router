import { useMemo, useRef } from 'react';
import { deepEqual } from './urlState';

function getAtPath(keys: (string | number)[], obj: any): any {
    let cur = obj;
    for (let i = 0; i < keys.length; i++) {
        if (cur == null) return undefined;
        cur = cur[keys[i]];
    }
    return cur;
}

/**
 * `isDirectUpdate(name)` is true when the child was updated directly (user
 * input, callback output, set_props) since the last check for `name`, false
 * when its value only changed because a parent rendered a new layout.
 */
export function useDirectUpdate(readUpdateEntry: () => any) {
    const seen = useRef(new Map<string, any>());
    return (name: string) => {
        const entry = readUpdateEntry();
        const first = !seen.current.has(name);
        const last = seen.current.get(name);
        seen.current.set(name, entry);
        return !first && entry !== undefined && entry !== last;
    };
}

/**
 * Read a prop of the (single) Dash child from the renderer store and re-render
 * when it changes. Works for children with and without an id.
 */
export function useChildProp(children: any, prop: string | undefined) {
    const api = (window as any).dash_component_api;
    const ctx = api.useDashContext();
    const store = ctx.useStore();

    const child = (Array.isArray(children) ? children[0] : children) as any;
    const childPath: (string | number)[] | undefined = child?.props?.componentPath;
    const pathKey = childPath ? JSON.stringify(childPath) : '';

    const valuePath = useMemo(
        () => (childPath && prop ? [...childPath, 'props', prop] : null),
        [pathKey, prop]
    );

    const value = ctx.useSelector(
        (state: any) => (valuePath ? getAtPath(valuePath, state.layout) : undefined),
        deepEqual
    );

    const readProp = (name: string) =>
        childPath ? getAtPath([...childPath, 'props', name], store.getState().layout) : undefined;

    /** Update the child like a user interaction would (fires its callbacks) */
    const setChildProps = (props: Record<string, any>) => {
        if (!childPath) return;
        const id = readProp('id');
        (window as any).dash_clientside.set_props(id ?? childPath, props);
    };

    /**
     * The renderer records every update aimed at a component (user input,
     * callback output, set_props) in `layoutHashes` under its path. A new
     * layout from a parent (e.g. the page re-rendered after a URL change)
     * replaces the child without touching that entry.
     */
    const readUpdateEntry = () =>
        childPath ? store.getState().layoutHashes?.[childPath.join(',')] : undefined;

    return {
        value,
        pathKey,
        hasChild: !!childPath,
        readProp,
        setChildProps,
        readUpdateEntry,
    };
}
