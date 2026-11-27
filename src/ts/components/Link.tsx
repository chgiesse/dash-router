import { DashBaseProps } from 'props/dash';
import React, { useSyncExternalStore } from 'react';
import { pushUrl, subscribeUrl } from '../utils/urlState';

interface Props extends DashBaseProps {
    /** Content of the link */
    children?: React.ReactNode;
    /** Target URL. Same-origin targets navigate in-page without a reload */
    href: string;
    /** Replace the current history entry instead of adding one. Default false */
    replace?: boolean;
    /** "exact" matches the pathname, "prefix" also matches sub-paths (href "/" only matches "/"). Default "prefix" */
    match?: 'exact' | 'prefix';
    /** Anchor target, e.g. "_blank". Targets other than "_self" are left to the browser */
    target?: string;
    /** Tooltip text */
    title?: string;
    /** CSS class name */
    className?: string;
    /** Inline CSS style */
    style?: Record<string, string | number>;
}

const isActive = (target: string, current: string, match: 'exact' | 'prefix') => {
    if (match === 'exact') return current === target;
    const base = target.replace(/\/+$/, '');
    if (base === '') return current === '/';
    return current === base || current.startsWith(base + '/');
};

/** Navigation link that updates the URL in-page (no reload) and marks itself active */
const Link = ({
    id,
    children,
    href,
    replace = false,
    match = 'prefix',
    target,
    title,
    className,
    style,
}: Props) => {
    const location = useSyncExternalStore(subscribeUrl, () => window.location.href);
    const active = isActive(new URL(href, location).pathname, window.location.pathname, match);

    const onClick = (e: React.MouseEvent<HTMLAnchorElement>) => {
        if (e.defaultPrevented || e.button !== 0) return;
        if (e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
        if (target && target !== '_self') return;
        const next = new URL(href, window.location.href);
        if (next.origin !== window.location.origin) return;
        e.preventDefault();
        pushUrl(next.pathname + next.search + next.hash, replace ? 'replace' : 'push');
    };

    return (
        <a
            id={id}
            href={href}
            target={target}
            title={title}
            className={className}
            style={style}
            onClick={onClick}
            aria-current={active ? 'page' : undefined}
            data-active={active ? 'true' : undefined}
        >
            {children}
        </a>
    );
};

export default Link;
