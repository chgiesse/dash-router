export interface DashBaseProps {
    /** Unique ID to identify this component in Dash callbacks. */
    id?: string;
    /** Update props to trigger callbacks. */
    setProps: (props: Record<string, any>) => void;
    /** Wild card data attributes */
    'data-*'?: string;
    /** Wild card aria attributes */
    'aria-*'?: string;
    /** tab-index */
    tabIndex?: number;
    /**  Object that holds the loading state object coming from dash-renderer. For use with dash<3.  */
    loading_state?: {
        /** Determines if the component is loading or not */
        is_loading: boolean;
        /** Holds which property is loading */
        prop_name: string;
        /** Holds the name of the component that is loading */
        component_name: string;
    };
}
