/**
 * Backend URL Configuration
 *
 * For local development: the backend at localhost:8000 is used automatically.
 * For production: replace PRODUCTION_BACKEND_URL with your deployed backend URL.
 *
 * Example (Render):  'https://sdos-backend.onrender.com'
 * Example (Railway): 'https://sdos-backend.up.railway.app'
 */
(function () {
    const PRODUCTION_BACKEND_URL = 'https://YOUR-BACKEND-URL.onrender.com'; // <-- update after deploying backend

    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
        window.BACKEND_URL = 'http://localhost:8000';
    } else {
        window.BACKEND_URL = PRODUCTION_BACKEND_URL;
    }
})();
