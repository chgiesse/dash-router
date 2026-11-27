/**
 * Links push history entries on click, before the router has answered. If a
 * navigation is overtaken, its URL would stay in history. While a navigation
 * is in flight (the committed store names another address than the browser
 * shows AND the router callback is still pending/running in Dash's store),
 * pushes are replaced instead, so only committed URLs get an entry. Once the
 * router callback finishes (even on error or PreventUpdate), pushes resume
 * normally so failed navigations don't get overwritten by subsequent links.
 */
const GUARD = '__dashRouterHistoryGuard';
const COMMITTED_STORE = 'dash-router-committed-store';
const ACTIVE_BUCKETS = ['requested', 'prioritized', 'blocked', 'executing', 'watched', 'executed'] as const;

const isNavigationCallbackActive = (): boolean => {
    const stores = (window as any).dash_stores;
    if (!Array.isArray(stores)) return false;
    return stores.some((store: any) => {
        const callbacks = store?.getState?.()?.callbacks;
        if (!callbacks) return false;
        return ACTIVE_BUCKETS.some(
            (bucket) =>
                Array.isArray(callbacks[bucket]) &&
                callbacks[bucket].some((cb: any) =>
                    cb?.callback?.outputs?.some((out: any) => out?.id === COMMITTED_STORE)
                )
        );
    });
};

const navigationInFlight = (): boolean => {
    try {
        const api = (window as any).dash_component_api;
        const href = api?.getLayout?.(COMMITTED_STORE)?.props?.data?.href;
        return (
            typeof href === 'string' &&
            href !== window.location.pathname + window.location.search &&
            isNavigationCallbackActive()
        );
    } catch {
        return false;
    }
};

const w = window as any;
if (!w[GUARD]) {
    w[GUARD] = true;
    const originalPush = window.history.pushState;
    const originalReplace = window.history.replaceState;

    window.history.pushState = function (...args: Parameters<History['pushState']>) {
        const method = navigationInFlight() ? originalReplace : originalPush;
        return method.apply(window.history, args);
    };
}
