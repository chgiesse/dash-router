import dash_mantine_components as dmc 

def create_appshell(content):
    return dmc.MantineProvider(
        forceColorScheme='dark',
        children=dmc.AppShell(
            [
                # dmc.AppShellHeader("", h=45),
                dmc.AppShellNavbar(dmc.Stack(
                    [
                        dmc.NavLink(href='/', label='home'),
                        dmc.NavLink(href='/sales', label='Sales'),
                        dmc.NavLink(href='/page-2', label='Page 2'),
                    ]
                )),
                dmc.AppShellMain(children=content, className='animated-card', m=0),
            ],
            padding="xs",    
            navbar={
                "width": 250,
                "breakpoint": "sm",
                "collapsed": {"mobile": True},
            }
        )
    )