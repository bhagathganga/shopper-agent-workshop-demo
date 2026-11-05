/* Canada Goose "Customer Support" contact menu (same options as canadagoose.com's chat launcher).
   "Chat with us" opens the Shopper Agent widget; the other rows are plain links rendered by the block. */
(function () {
    var root = document.getElementById('cg-contact');
    if (!root) return;
    var launcher = root.querySelector('.cg-contact-launcher');
    var menu = root.querySelector('.cg-contact-menu');

    function setOpen(open) {
        menu.hidden = !open;
        launcher.setAttribute('aria-expanded', String(open));
        if (open) {
            var first = menu.querySelector('.cg-contact-option');
            if (first) first.focus();
        }
    }

    // The widget bundle loads deferred; retry briefly if the shopper is faster than it.
    function openWidget(triesLeft) {
        var ns = window.CimulateMessaging || {};
        if (ns.eventHandlers && ns.eventHandlers.components) {
            ns.eventHandlers.components.toggleWidgetOpen(true);
        } else if (triesLeft > 0) {
            window.setTimeout(function () {
                openWidget(triesLeft - 1);
            }, 250);
        }
    }

    launcher.addEventListener('click', function () {
        setOpen(menu.hidden);
    });
    root.querySelector('.cg-contact-minimize').addEventListener('click', function () {
        setOpen(false);
        launcher.focus();
    });
    root.querySelector('[data-cg-action="chat"]').addEventListener('click', function () {
        setOpen(false);
        openWidget(40);
    });
    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape' && !menu.hidden) {
            setOpen(false);
            launcher.focus();
        }
    });
})();
