Theme selector in ui doesn't work, needs work

Right-click menu: opens alongside the browser's default context menu; also needs visual polish (looks ugly)

- ui-core: fix unreachable code after return in /ui/context-menu route.
- ui-style: expand t-btn variants and unify header/menu markup between _header.html and _user_menu.html.
- ui-style: verify htmx header persistence attributes and OOB title updates across browsers.
- auth: consider optional login endpoint that sets access_token cookie server-side (reduces client JS responsibility).
