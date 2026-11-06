/* Canada Goose "Customer Support" contact menu (same options as canadagoose.com's chat launcher).
   "Chat with us" opens the Shopper Agent widget; the other rows are plain links rendered by the block.
   With the pre-chat form on, a new chat first asks for name, email, phone and marketing consent; the
   values are handed to the widget as hidden pre-chat fields when it creates the conversation. */
(function () {
    var root = document.getElementById('cg-contact');
    if (!root) return;
    var launcher = root.querySelector('.cg-contact-launcher');
    var menu = root.querySelector('.cg-contact-menu');
    var welcome = root.querySelector('.cg-contact-welcome');
    var list = root.querySelector('.cg-contact-list');
    var form = root.querySelector('.cg-prechat');
    var widgetEl = document.getElementById('cimulate-messaging-widget');
    var PRECHAT_KEY = 'cg_prechat';

    function showForm(show) {
        welcome.hidden = show;
        list.hidden = show;
        if (form) form.hidden = !show;
    }

    function setOpen(open, withForm) {
        menu.hidden = !open;
        launcher.setAttribute('aria-expanded', String(open));
        if (!open) return;
        showForm(!!withForm);
        var first = withForm ? form.querySelector('input') : menu.querySelector('.cg-contact-option');
        if (first) first.focus();
    }

    function components() {
        var ns = window.CimulateMessaging || {};
        return ns.eventHandlers && ns.eventHandlers.components;
    }

    // The widget bundle loads deferred; retry briefly if the shopper is faster than it.
    function openWidget(triesLeft) {
        var c = components();
        if (c) {
            c.toggleWidgetOpen(true);
        } else if (triesLeft > 0) {
            window.setTimeout(function () {
                openWidget(triesLeft - 1);
            }, 250);
        }
    }

    function storedPrechat() {
        try {
            return JSON.parse(sessionStorage.getItem(PRECHAT_KEY));
        } catch (e) {
            return null;
        }
    }

    // The widget keeps the open conversation in localStorage (cim_af_conv_<org>_<deployment>) and removes it
    // when the chat ends; while one exists the chat resumes and pre-chat values would be ignored anyway.
    function hasConversation() {
        var es = widgetEl ? widgetEl.getAttribute('data-es-developer-name') : '';
        try {
            for (var i = 0; i < localStorage.length; i++) {
                var k = localStorage.key(i);
                if (k && k.indexOf('cim_af_conv_') === 0 && (!es || k.indexOf(es) > -1)) return true;
            }
        } catch (e) {}
        return false;
    }

    function startChat() {
        if (form && !storedPrechat() && !hasConversation()) {
            setOpen(true, true);
            return;
        }
        setOpen(false);
        openWidget(40);
    }

    launcher.addEventListener('click', function () {
        setOpen(menu.hidden);
    });
    root.querySelector('.cg-contact-minimize').addEventListener('click', function () {
        setOpen(false);
        launcher.focus();
    });
    root.querySelector('[data-cg-action="chat"]').addEventListener('click', startChat);
    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape' && !menu.hidden) {
            setOpen(false);
            launcher.focus();
        }
    });

    if (!form) return;

    var pending = null; // values submitted on this page, used if sessionStorage is unavailable
    var EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;

    // Keep a leading + and digits only: Phone_Number is capped at 15 characters on the messaging channel.
    function normalizePhone(v) {
        return v.replace(/[^\d+]/g, '').replace(/(?!^)\+/g, '');
    }

    function setError(input, msg) {
        var err = document.getElementById(input.getAttribute('aria-describedby'));
        input.setAttribute('aria-invalid', msg ? 'true' : 'false');
        input.parentNode.classList.toggle('cg-field--error', !!msg);
        err.textContent = msg || '';
        err.hidden = !msg;
    }

    function validate(input) {
        var v = input.value.trim();
        var msg = '';
        if (!v) {
            if (input.required) msg = form.getAttribute('data-msg-required');
        } else if (input.type === 'email' && !EMAIL_RE.test(v)) {
            msg = form.getAttribute('data-msg-email');
        } else if (input.type === 'tel') {
            var p = normalizePhone(v);
            if (p.replace('+', '').length < 7 || p.length > 15) msg = form.getAttribute('data-msg-phone');
        }
        setError(input, msg);
        return !msg;
    }

    var fields = Array.prototype.slice.call(form.querySelectorAll('.cg-field input'));
    fields.forEach(function (input) {
        input.addEventListener('blur', function () {
            if (input.value.trim() || input.getAttribute('aria-invalid') === 'true') validate(input);
        });
    });

    form.addEventListener('submit', function (e) {
        e.preventDefault();
        var firstBad = null;
        fields.forEach(function (input) {
            if (!validate(input) && !firstBad) firstBad = input;
        });
        if (firstBad) {
            firstBad.focus();
            return;
        }
        var values = {};
        fields.forEach(function (input) {
            var v = input.value.trim();
            if (input.type === 'tel') v = normalizePhone(v);
            if (v) values[input.name] = v;
        });
        values.Consent_Checkbox = form.elements.Consent_Checkbox.checked ? 'Yes' : 'No';
        try {
            sessionStorage.setItem(PRECHAT_KEY, JSON.stringify(values));
        } catch (err) {}
        pending = values;
        setOpen(false);
        openWidget(40);
    });

    // Fired by the widget right before it creates a conversation (first open, or "new chat" after one ends).
    // It only waits ~5s for done(), so the form must be filled in before the widget opens: with values, hand
    // them over; without (the widget was opened some other way), cancel and show the form instead.
    window.addEventListener('onCimulateWidgetReady', function (e) {
        var d = e && e.detail;
        if (!d || typeof d.setHiddenPrechatFields !== 'function' || typeof d.done !== 'function') return;
        var values = pending || storedPrechat();
        e.preventDefault();
        if (values) {
            d.setHiddenPrechatFields(values);
            d.done();
            return;
        }
        if (typeof d.abort === 'function') {
            d.abort();
            var c = components();
            if (c) c.toggleWidgetOpen(false);
            setOpen(true, true);
        } else {
            d.done();
        }
    });
})();
