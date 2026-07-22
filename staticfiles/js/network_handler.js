/**
 * HMS ENTERPRISE - GLOBAL NETWORK CONNECTION HANDLER
 * Supports Offline Detection, Server Unreachability Handling, PWA SW & Auto-Restoration
 */
(function () {
  'use strict';

  let overlayEl,
    caseNoInternetEl,
    caseServerDownEl,
    statusBadgeEl,
    statusTextEl,
    retryBtn,
    retrySpinner,
    retryIcon,
    retryBtnText;

  let isChecking = false;
  let autoRetryInterval = null;

  // Initialize script on DOM ready
  document.addEventListener('DOMContentLoaded', function () {
    initElements();
    initLastVisitedUrlTracker();
    registerServiceWorker();

    // Initial silent check
    checkConnection(false);

    // Auto retry every 10 seconds
    autoRetryInterval = setInterval(function () {
      checkConnection(false);
    }, 10000);

    // Event listeners
    window.addEventListener('online', function () {
      checkConnection(false);
    });

    window.addEventListener('offline', function () {
      showCaseNoInternet();
    });

    if (retryBtn) {
      retryBtn.addEventListener('click', function () {
        handleManualRetry();
      });
    }

    // Intercept failed fetches to trigger connection check
    interceptFetchErrors();
  });

  function initElements() {
    overlayEl = document.getElementById('hms-network-overlay');
    caseNoInternetEl = document.getElementById('hms-case-no-internet');
    caseServerDownEl = document.getElementById('hms-case-server-down');
    statusBadgeEl = document.getElementById('hms-status-badge');
    statusTextEl = document.getElementById('hms-status-text');
    retryBtn = document.getElementById('hms-retry-btn');
    retrySpinner = document.getElementById('hms-retry-spinner');
    retryIcon = document.getElementById('hms-retry-icon');
    retryBtnText = document.getElementById('hms-retry-btn-text');
  }

  function initLastVisitedUrlTracker() {
    const currentUrl = window.location.href;
    const currentPath = window.location.pathname;

    // Do not save offline fallback page as last visited URL
    if (currentPath !== '/offline/' && !currentPath.includes('/offline')) {
      try {
        localStorage.setItem('hms_last_visited_url', currentUrl);
      } catch (e) {
        console.warn('HMS: Unable to save last visited URL to localStorage', e);
      }
    }
  }

  function registerServiceWorker() {
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker
        .register('/static/service-worker.js', { scope: '/' })
        .then(function (reg) {
          console.log('HMS Service Worker registered successfully:', reg.scope);
        })
        .catch(function (err) {
          console.warn('HMS Service Worker registration skipped or failed:', err);
        });
    }
  }

  /**
   * Primary Connection Checker
   */
  async function checkConnection(isManual) {
    if (isChecking && !isManual) return;
    isChecking = true;

    // CASE 1: No Internet Connection
    if (navigator.onLine === false) {
      showCaseNoInternet();
      isChecking = false;
      return 'offline';
    }

    // CASE 2: Internet is Available, check if Django server is reachable
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 4000);

    try {
      const response = await fetch('/ping/?t=' + Date.now(), {
        method: 'GET',
        cache: 'no-store',
        signal: controller.signal,
        headers: {
          'Accept': 'text/plain, */*'
        }
      });

      clearTimeout(timeoutId);

      if (response.ok) {
        // SERVER IS REACHABLE & ONLINE
        restoreConnectionState();
        isChecking = false;
        return 'online';
      } else {
        // Server returned 5xx or error code
        showCaseServerDown();
        isChecking = false;
        return 'server_down';
      }
    } catch (error) {
      clearTimeout(timeoutId);
      // Fetch failed or timed out -> Server is Unreachable
      showCaseServerDown();
      isChecking = false;
      return 'server_down';
    }
  }

  function showCaseNoInternet() {
    if (!overlayEl) return;
    overlayEl.classList.remove('d-none');
    
    if (caseNoInternetEl) caseNoInternetEl.classList.remove('d-none');
    if (caseServerDownEl) caseServerDownEl.classList.add('d-none');

    if (statusBadgeEl && statusTextEl) {
      statusBadgeEl.className = 'badge rounded-pill bg-danger-subtle text-danger px-3 py-2 border border-danger-subtle';
      statusBadgeEl.innerHTML = '<i class="bi bi-wifi-off me-1"></i> <span>Network Connection Lost</span>';
    }
  }

  function showCaseServerDown() {
    if (!overlayEl) return;
    overlayEl.classList.remove('d-none');

    if (caseNoInternetEl) caseNoInternetEl.classList.add('d-none');
    if (caseServerDownEl) caseServerDownEl.classList.remove('d-none');

    if (statusBadgeEl && statusTextEl) {
      statusBadgeEl.className = 'badge rounded-pill bg-warning-subtle text-warning-emphasis px-3 py-2 border border-warning-subtle';
      statusBadgeEl.innerHTML = '<i class="bi bi-hdd-network-fill me-1"></i> <span>Hospital Server Unavailable</span>';
    }
  }

  function restoreConnectionState() {
    if (!overlayEl) return;

    const wasOverlayVisible = !overlayEl.classList.contains('d-none');
    overlayEl.classList.add('d-none');

    const currentPath = window.location.pathname;

    // If connection restored while user is stuck on /offline/ page, redirect back to last visited page
    if (currentPath === '/offline/' || currentPath.includes('/offline')) {
      let lastUrl = '/';
      try {
        lastUrl = localStorage.getItem('hms_last_visited_url') || '/';
      } catch (e) {}

      if (lastUrl && lastUrl !== window.location.href) {
        window.location.href = lastUrl;
      }
    }
  }

  async function handleManualRetry() {
    if (!retryBtn) return;

    retryBtn.disabled = true;
    if (retrySpinner) retrySpinner.classList.remove('d-none');
    if (retryIcon) retryIcon.classList.add('d-none');
    if (retryBtnText) retryBtnText.textContent = 'Checking...';

    await checkConnection(true);

    setTimeout(function () {
      if (retryBtn) retryBtn.disabled = false;
      if (retrySpinner) retrySpinner.classList.add('d-none');
      if (retryIcon) retryIcon.classList.remove('d-none');
      if (retryBtnText) retryBtnText.textContent = 'Retry Connection';
    }, 600);
  }

  function interceptFetchErrors() {
    const originalFetch = window.fetch;
    if (!originalFetch) return;

    window.fetch = async function () {
      try {
        const response = await originalFetch.apply(this, arguments);
        if (response.status >= 502 && response.status <= 504) {
          checkConnection(false);
        }
        return response;
      } catch (error) {
        // If fetch failed due to network error, trigger check
        const requestUrl = arguments[0] ? arguments[0].toString() : '';
        if (!requestUrl.includes('/ping/')) {
          checkConnection(false);
        }
        throw error;
      }
    };
  }

  // Expose global check helper if needed
  window.HMSNetworkHandler = {
    checkConnection: checkConnection
  };
})();
