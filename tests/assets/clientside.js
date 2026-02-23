const ogFetch = window.fetch

// Split request bo
const dataSplitter = '"dash-router-loading-state-store","property":"data"'

window.fetch = async (...args) => {
    const setProps = window.dash_clientside.set_props
    const path = args[0]
    const r = args[1]
    if (path !== "/_dash-update-component") {
        return await ogFetch(...args)
    }
    const body = r?.body
    if (body.includes('dash-router-dummy-location.id')) {
        const parsed = JSON.parse(body)
        if (parsed.output !== "dash-router-dummy-location.id") {
            return await ogFetch(...args)
        }
        let lssData = parsed.state[0]
        const redirect = lssData.value.is_redirect
        if (redirect === undefined || redirect === false ) {
            return await ogFetch(...args)
        }
        lssData.value.is_redirect = false
        setProps(lssData.id, {data: lssData.value})
        const dummyData = {response: {}, multi: true}
        const dummyResponse = new Response(JSON.stringify(dummyData))
        return dummyResponse
    }

    og_res = await ogFetch(...args)
    return og_res
}
