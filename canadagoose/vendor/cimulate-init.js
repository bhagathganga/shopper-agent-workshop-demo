/* eslint-disable */
(function () {
    function initWidget() {
        var el = document.getElementById('cimulate-messaging-widget');
        if (!el) return;

        function getBoolAttr(name, fallback) {
            var val = el.getAttribute(name);
            if (val === 'true') return true;
            if (val === 'false') return false;
            return fallback;
        }

        function getJsonAttr(name) {
            var val = el.getAttribute(name);
            if (!val) return {};
            try {
                return JSON.parse(val);
            } catch (e) {
                return {};
            }
        }

        var isOpen = getBoolAttr('data-is-open', false);
        var brandingConfig = getJsonAttr('data-branding-config');
        var hasBranding = brandingConfig && Object.keys(brandingConfig).length > 0;
        var headerConfig = getJsonAttr('data-header-config');
        var hasHeaderConfig = headerConfig && Object.keys(headerConfig).length > 0;
        var entryMessage = el.getAttribute('data-entry-message');

        var widgetConfig = {
            elementId: 'cimulate-messaging-widget',
            mode: 'messaging',
            layoutPreset: el.getAttribute('data-preset') || 'standard',
            isDevelopment: getBoolAttr('data-is-dev', false),
            componentConfig: {
                isOpen: isOpen,
                isMinimized: !isOpen,
                options: {
                    dialogPosition: el.getAttribute('data-position') || 'bottom-left',
                    dialogFullHeight: getBoolAttr('data-dialog-full-height', true)
                }
            },
            messagingConfig: {
                scrt2Url: el.getAttribute('data-scrt2-url') || '',
                orgId: el.getAttribute('data-org-id') || '',
                esDeveloperName: el.getAttribute('data-es-developer-name') || '',
                capabilitiesVersion: el.getAttribute('data-capabilities-version') || '65',
                enablePageContext: getBoolAttr('data-enable-page-context', false),
                enableImageUpload: getBoolAttr('data-enable-image-upload', false),
                enableEscalationToAgent: getBoolAttr('data-enable-escalation', false),
                progressStepsLimit: parseInt(el.getAttribute('data-progress-steps-limit') || '3', 10),
                routingAttributes: getJsonAttr('data-routing-attributes')
            },
            conversationHistory: { limit: parseInt(el.getAttribute('data-conversation-history-limit') || '200', 10) },
            theme: getJsonAttr('data-theme'),
            headerText: el.getAttribute('data-header-text') || '',
            disclaimerMarkdown: el.getAttribute('data-disclaimer-markdown') || '',
            searchConfig: getJsonAttr('data-search-config'),
            overridesUrl: el.getAttribute('data-overrides-url') || '',
            prechatConfigUrl: el.getAttribute('data-prechat-url') || '',
            prechatCsrfName: el.getAttribute('data-prechat-csrf-name') || '',
            prechatCsrfToken: el.getAttribute('data-prechat-csrf-token') || '',
            updateEcomSessionUrl: el.getAttribute('data-update-ecom-session-url') || ''
        };

        if (hasBranding) {
            widgetConfig.brandingConfig = brandingConfig;
        }
        if (hasHeaderConfig) {
            widgetConfig.headerConfig = headerConfig;
        }
        if (entryMessage) {
            widgetConfig.entryMessage = entryMessage;
        }

        // Override isOpen/isMinimized from session state if this is a same-site
        // navigation (link click). This makes the widget open immediately with
        // the correct state, avoiding the flash of FAB → open transition.
        (function () {
            try {
                var navEntry =
                    performance && performance.getEntriesByType && performance.getEntriesByType('navigation')[0];
                if (navEntry && navEntry.type === 'navigate') {
                    var raw = sessionStorage.getItem('cc_panel');
                    if (raw) {
                        var saved = JSON.parse(raw);
                        if (saved.open) {
                            widgetConfig.componentConfig.isOpen = true;
                            widgetConfig.componentConfig.isMinimized = false;
                        }
                    }
                }
            } catch (e) {}
        })();

        var mod = window.CimulateMessaging;
        if (!mod || !mod.injectMessagingWidget) {
            console.error('[CommerceClient] CimulateMessaging.injectMessagingWidget not available.');
            return;
        }

        function synchronizePdpPageContext(messagingModule, isPdp, productId) {
            var pageContext = messagingModule.eventHandlers && messagingModule.eventHandlers.pageContext;
            var normalizedProductId = typeof productId === 'string' ? productId.replace(/^\s+|\s+$/g, '') : '';
            if (!pageContext) {
                return;
            }

            try {
                if (isPdp && normalizedProductId && typeof pageContext.set === 'function') {
                    pageContext.set({ type: 'pdp', id: normalizedProductId });
                    return;
                }
                if (typeof pageContext.clear === 'function') {
                    pageContext.clear();
                }
            } catch (e) {
                // A rejected PDP value must not leave an older product active.
                try {
                    if (typeof pageContext.clear === 'function') {
                        pageContext.clear();
                    }
                } catch (clearError) {}
            }
        }
        synchronizePdpPageContext(mod, getBoolAttr('data-is-pdp', false), el.getAttribute('data-pdp-product-id'));

        // Add prechat handshake
        (function () {
            var PRECHAT_URL = widgetConfig.prechatConfigUrl;
            var CSRF_NAME = widgetConfig.prechatCsrfName;
            var csrfToken = widgetConfig.prechatCsrfToken;

            if (!PRECHAT_URL) {
                return;
            }

            function body() {
                var p = new URLSearchParams();
                if (CSRF_NAME && csrfToken) {
                    p.append(CSRF_NAME, csrfToken);
                }
                return p.toString();
            }

            function fetchOnce() {
                return fetch(PRECHAT_URL, {
                    method: 'POST',
                    credentials: 'include',
                    redirect: 'manual',
                    headers: { 'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8' },
                    body: body()
                })
                    .then(function (resp) {
                        if (resp.type === 'opaqueredirect') {
                            return { status: 302, config: null };
                        }
                        var status = resp.status;
                        return resp
                            .json()
                            .catch(function () {
                                return null;
                            })
                            .then(function (cfg) {
                                return { status: status, config: cfg };
                            });
                    })
                    .catch(function () {
                        return { status: 0, config: null };
                    });
            }

            function refreshCsrf(cfg) {
                if (cfg && cfg.csrfToken) {
                    csrfToken = cfg.csrfToken;
                }
            }

            function fetchConfig() {
                return fetchOnce()
                    .then(function (r) {
                        if (r.status === 302) {
                            return fetchOnce();
                        }
                        if (r.status === 403) {
                            refreshCsrf(r.config);
                            return fetchOnce();
                        }
                        return r;
                    })
                    .then(function (r) {
                        if (r.status === 403) {
                            refreshCsrf(r.config);
                            return fetchOnce();
                        }
                        return r;
                    });
            }

            window.addEventListener('onCimulateWidgetReady', function (e) {
                if (!e || !e.detail || typeof e.detail.setHiddenPrechatFields !== 'function') {
                    return;
                }
                e.preventDefault();
                try {
                    fetchConfig()
                        .then(function (r) {
                            try {
                                if (r && r.status === 200 && r.config && !r.config.error) {
                                    delete r.config.CsrfTokenName;
                                    e.detail.setHiddenPrechatFields(r.config);
                                } else {
                                    console.warn(
                                        '[CommerceClient] prechat fetch failed — HTTP',
                                        r ? r.status : 'unknown'
                                    );
                                }
                            } catch (innerErr) {
                                console.warn('[CommerceClient] inner prechat config application error', innerErr);
                            }
                        })
                        .catch(function (err) {
                            console.warn('[CommerceClient] prechat fetch error', err);
                        })
                        .then(function () {
                            try {
                                e.detail.done();
                            } catch (doneErr) {
                                console.warn('[CommerceClient] error calling e.detail.done()', doneErr);
                            }
                        });
                } catch (outerErr) {
                    console.warn('[CommerceClient] outer prechat handshake error', outerErr);
                    try {
                        e.detail.done();
                    } catch (dErr) {}
                }
            });
        })();

        // Product Result session linking. The widget invokes
        // messagingConfig.onProductResult (detail: { agentSessionId, ... }) when an
        // agent response returns product results; link the MessagingSession id to
        // this ECOM session so downstream analytics can attribute it. The CSRF
        // retry mirrors the prechat handshake: the controller answers an invalid /
        // absent token with a retryable 403 carrying a fresh session-bound token
        // (see CommerceClient.rejectCsrf), and a 302 rotates an expired guest dwsid.
        (function () {
            var UPDATE_ECOM_SESSION_URL = widgetConfig.updateEcomSessionUrl;
            var CSRF_NAME = widgetConfig.prechatCsrfName;
            // Shares the prechat token cache: the handshake usually runs and
            // learns a session-bound token before any product result arrives.
            var csrfToken = widgetConfig.prechatCsrfToken;

            if (!UPDATE_ECOM_SESSION_URL) {
                return;
            }

            function postOnce(agentSessionId) {
                var postBody = new URLSearchParams();
                postBody.append('agentSessionId', agentSessionId);
                if (CSRF_NAME && csrfToken) {
                    postBody.append(CSRF_NAME, csrfToken);
                }
                return fetch(UPDATE_ECOM_SESSION_URL, {
                    method: 'POST',
                    credentials: 'include',
                    redirect: 'manual',
                    headers: { 'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8' },
                    body: postBody.toString()
                })
                    .then(function (resp) {
                        if (resp.type === 'opaqueredirect') {
                            return { status: 302, body: null };
                        }
                        var status = resp.status;
                        return resp
                            .json()
                            .catch(function () {
                                return null;
                            })
                            .then(function (json) {
                                return { status: status, body: json };
                            });
                    })
                    .catch(function () {
                        return { status: 0, body: null };
                    });
            }

            function refreshCsrf(r) {
                if (r && r.body && r.body.csrfToken) {
                    csrfToken = r.body.csrfToken;
                }
            }

            function updateEcomSession(agentSessionId) {
                return postOnce(agentSessionId)
                    .then(function (r) {
                        if (r.status === 302) {
                            return postOnce(agentSessionId);
                        }
                        if (r.status === 403) {
                            refreshCsrf(r);
                            return postOnce(agentSessionId);
                        }
                        return r;
                    })
                    .then(function (r) {
                        if (r.status === 403) {
                            refreshCsrf(r);
                            return postOnce(agentSessionId);
                        }
                        return r;
                    })
                    .then(function (r) {
                        if (!r || r.status !== 200) {
                            console.warn('[CommerceClient] UpdateECOMSession failed — HTTP', r && r.status);
                        }
                    });
            }

            widgetConfig.messagingConfig.onProductResult = function (detail) {
                try {
                    if (!detail || !detail.agentSessionId) {
                        return;
                    }
                    updateEcomSession(detail.agentSessionId);
                } catch (err) {
                    console.error('[CommerceClient] Error handling onProductResult callback', err);
                }
            };
        })();

        var FAB_LABEL = (hasBranding && brandingConfig.fabLabel) || 'gear up for adventure';
        function clearFabTimers(button) {
            var timers = button._ccFabTimers || [];
            timers.forEach(function (timer) {
                window.clearTimeout(timer);
            });
            button._ccFabTimers = [];
        }
        function addFabTimer(button, callback, delay) {
            button._ccFabTimers.push(window.setTimeout(callback, delay));
        }
        function prefersReducedMotion() {
            return window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
        }
        function holdFabOpen(button) {
            clearFabTimers(button);
            button.classList.remove('cc-fab-sheen');
            button.classList.add('cc-fab-expanded');
        }
        function startFabLoop(button) {
            holdFabOpen(button);
            if (!prefersReducedMotion()) {
                addFabTimer(
                    button,
                    function () {
                        startFabClosedCycle(button);
                    },
                    1000
                );
            }
        }
        function startFabClosedCycle(button) {
            clearFabTimers(button);
            button.classList.remove('cc-fab-sheen');
            if (prefersReducedMotion()) {
                button.classList.add('cc-fab-expanded');
                return;
            }
            button.classList.remove('cc-fab-expanded');
            addFabTimer(
                button,
                function () {
                    button.classList.add('cc-fab-expanded');
                },
                5200
            );
            addFabTimer(
                button,
                function () {
                    button.classList.add('cc-fab-sheen');
                },
                6000
            );
            addFabTimer(
                button,
                function () {
                    startFabLoop(button);
                },
                7100
            );
        }
        function initializeFab(button) {
            if (button._ccFabInitialized) return;
            button._ccFabInitialized = true;
            button._ccFabTimers = [];
            button._ccFabHovered = false;
            button._ccFabFocused = false;
            button.addEventListener('mouseenter', function () {
                button._ccFabHovered = true;
                holdFabOpen(button);
            });
            button.addEventListener('mouseleave', function () {
                button._ccFabHovered = false;
                if (!button._ccFabFocused) startFabClosedCycle(button);
            });
            button.addEventListener('focus', function () {
                button._ccFabFocused = true;
                holdFabOpen(button);
            });
            button.addEventListener('blur', function () {
                button._ccFabFocused = false;
                if (!button._ccFabHovered) startFabClosedCycle(button);
            });
            startFabLoop(button);
        }
        function applyFabBranding() {
            var button = document.querySelector('.cim-widget-minimized-button');
            if (!button) return false;
            button.setAttribute('data-label', FAB_LABEL);
            button.setAttribute('aria-label', FAB_LABEL);
            button.setAttribute('title', FAB_LABEL);
            initializeFab(button);
            return true;
        }
        function observeFab() {
            if (applyFabBranding()) return;
            if (!window.MutationObserver) return;
            var observer = new MutationObserver(function () {
                if (applyFabBranding()) observer.disconnect();
            });
            observer.observe(document.body, { childList: true, subtree: true });
        }

        var showFab = el.getAttribute('data-show-fab') !== 'false';
        if (!showFab) {
            document.body.classList.add('cc-hide-fab');
        }

        // State tracks
        var CC_KEY = 'cc_panel';
        var _ccOpen = widgetConfig.componentConfig.isOpen || false;
        var _ccPos = widgetConfig.componentConfig.options.dialogPosition || 'bottom-left';
        var _ccFullHeight = widgetConfig.componentConfig.options.dialogFullHeight !== false;
        var reinjectTimer = null;

        // Page push
        var _ccPagePush = getBoolAttr('data-page-push', widgetConfig.layoutPreset === 'commerce');
        var header =
            document.querySelector('.page header.site-header') ||
            document.querySelector('header') ||
            document.querySelector('.site-header');
        var lastTop;
        var lastHeight;
        var settleUntil = 0;
        var layoutFrame = null;

        function setBodyClass(name, enabled) {
            if (document.body.classList.contains(name) !== enabled) {
                document.body.classList.toggle(name, enabled);
            }
        }
        function _ccPush() {
            var push = _ccPagePush && _ccOpen && window.innerWidth >= 992;
            setBodyClass('cc-panel-open', push);
            setBodyClass('cc-panel-left', push && _ccPos !== 'bottom-right');
            setBodyClass('cc-panel-right', push && _ccPos === 'bottom-right');
            var top = 0;
            if (push && _ccFullHeight && header) {
                var style = window.getComputedStyle(header);
                var rect = header.getBoundingClientRect();
                if (
                    style.display !== 'none' &&
                    style.visibility !== 'hidden' &&
                    rect.bottom > 0 &&
                    rect.top < window.innerHeight
                ) {
                    top = Math.min(rect.bottom, window.innerHeight);
                }
            }
            var topValue = top + 'px';
            var heightValue = top ? 'calc(100dvh - ' + top + 'px)' : '100dvh';
            if (lastTop !== topValue) {
                document.documentElement.style.setProperty('--cc-panel-top', topValue);
                lastTop = topValue;
            }
            if (lastHeight !== heightValue) {
                document.documentElement.style.setProperty('--cc-panel-height', heightValue);
                lastHeight = heightValue;
            }
        }
        function settleLayout() {
            settleUntil = Date.now() + 300;
            if (layoutFrame !== null) return;
            if (!window.requestAnimationFrame) {
                _ccPush();
                return;
            }
            function frame() {
                layoutFrame = null;
                _ccPush();
                // NTO's transform keeps moving after the class mutation and resize notification.
                if (Date.now() < settleUntil) layoutFrame = window.requestAnimationFrame(frame);
            }
            layoutFrame = window.requestAnimationFrame(frame);
        }
        _ccPush();
        window.addEventListener('scroll', settleLayout, { passive: true });
        window.addEventListener('resize', settleLayout);
        if (window.ResizeObserver && header) {
            // Observe only the header itself: the panel offset is derived from the
            // header's own getBoundingClientRect().bottom, and an auto-height header
            // resizes whenever a descendant reflows, so it already captures child
            // size changes. The settleLayout RAF loop and the class MutationObserver
            // below cover transient transforms. Observing every descendant added
            // observer overhead on complex headers without changing the measurement.
            var resizeObserver = new window.ResizeObserver(settleLayout);
            resizeObserver.observe(header);
        }
        if (window.MutationObserver) {
            var layoutObserver = new window.MutationObserver(settleLayout);
            layoutObserver.observe(document.body, { attributes: true, attributeFilter: ['class'] });
            if (header) layoutObserver.observe(header, { attributes: true, attributeFilter: ['class'], subtree: true });
        }

        function _ccSave() {
            try {
                sessionStorage.setItem(CC_KEY, JSON.stringify({ open: _ccOpen, pos: _ccPos }));
            } catch (e) {}
        }

        function _ccRestore() {
            try {
                var raw = sessionStorage.getItem(CC_KEY);
                if (!raw) return;
                var s = JSON.parse(raw);
                if (!s.open) return;
                var ns = window.CimulateMessaging || {};
                var c = ns.eventHandlers && ns.eventHandlers.components;
                if (!c) return;
                if (s.pos && s.pos !== widgetConfig.componentConfig.options.dialogPosition) {
                    c.setWidgetDialogPosition(s.pos);
                }
                setTimeout(function () {
                    c.toggleWidgetOpen(true);
                }, 50);
            } catch (e) {}
        }

        // Listen for widget events
        window.addEventListener('cimulate:ui-state-update', function (e) {
            var d = e && e.detail;
            if (!d) return;
            if (d.property === 'isOpen') {
                if (Boolean(d.value) === _ccOpen) {
                    return;
                }
                var _ccPrev = _ccOpen;
                _ccOpen = Boolean(d.value);
                _ccPush();
                _ccSave();
                if (_ccOpen && reinjectTimer !== null) {
                    window.clearTimeout(reinjectTimer);
                    reinjectTimer = null;
                }
                if (showFab && reinjectTimer === null) {
                    if (_ccPrev === true && _ccOpen === false) {
                        reinjectTimer = window.setTimeout(function () {
                            reinjectTimer = null;
                            if (_ccOpen) return;
                            var el = document.getElementById('cimulate-messaging-widget');
                            if (!el) {
                                el = document.createElement('div');
                                el.id = 'cimulate-messaging-widget';
                                document.body.appendChild(el);
                            }
                            var cfg = JSON.parse(JSON.stringify(widgetConfig));
                            cfg.componentConfig.isOpen = false;
                            cfg.componentConfig.isMinimized = true;
                            cfg.componentConfig.options.dialogPosition = _ccPos;
                            cfg.componentConfig.options.dialogFullHeight = _ccFullHeight;
                            mod.injectMessagingWidget(cfg);
                            observeFab();
                        }, 300);
                    }
                }
            }
            if (d.property === 'position') {
                _ccPos = d.value;
                _ccPush();
                _ccSave();
            }
            if (d.property === 'isFullHeight') {
                _ccFullHeight = Boolean(d.value);
                _ccPush();
            }
        });

        mod.injectMessagingWidget(widgetConfig);
        observeFab();

        // Restore on SFRA navigation
        (function () {
            var navType =
                performance &&
                performance.getEntriesByType &&
                performance.getEntriesByType('navigation')[0] &&
                performance.getEntriesByType('navigation')[0].type;
            if (navType === 'navigate') {
                _ccRestore();
            }
        })();
    }

    if (document.readyState === 'complete') {
        initWidget();
    } else {
        window.addEventListener('load', initWidget);
    }
})();
