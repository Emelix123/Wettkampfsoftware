// general.js

// Ein einfacher Namespace, um globale Konflikte zu reduzieren (optional, aber gute Praxis)
const AppUtils = (() => {
    const API_BASE_URL = '/api'; // Globale API-Basis-URL

    /**
     * Führt einen GET-Request an einen API-Endpunkt aus.
     * @param {string} endpoint - Der API-Endpunkt (z.B. '/wettkampftage').
     * @returns {Promise<Object|null>} - Die JSON-Antwort oder null bei Fehler.
     */
    async function fetchData(endpoint) {
        try {
            const response = await fetch(`${API_BASE_URL}${endpoint}`);
            if (!response.ok) {
                const errorText = await response.text();
                console.error(`API-Fehler (${response.status}) für ${endpoint}: ${errorText}`);
                throw new Error(`API-Fehler: ${response.status} ${response.statusText}`);
            }
            return await response.json();
        } catch (error) {
            console.error(`Fehler beim Laden von Daten (${endpoint}):`, error);
            // Hier könnte eine globale Benachrichtigungsfunktion aufgerufen werden
            showGlobalNotification(`Fehler beim Laden von Daten: ${error.message}`, 'error');
            return null;
        }
    }

    /**
     * Führt einen POST-Request mit JSON-Daten an einen API-Endpunkt aus.
     * @param {string} endpoint - Der API-Endpunkt.
     * @param {Object} data - Das zu sendende JavaScript-Objekt.
     * @returns {Promise<Object|null>} - Die JSON-Antwort oder null bei Fehler.
     */
    async function postData(endpoint, data) {
        try {
            const response = await fetch(`${API_BASE_URL}${endpoint}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data),
            });
            const responseData = await response.json().catch(() => null); // Bei leerer Antwort null
            if (!response.ok) {
                const errorMsg = responseData?.error || responseData?.message || response.statusText;
                console.error(`API-Fehler (${response.status}) für ${endpoint}: ${errorMsg}`);
                throw new Error(`API-Fehler: ${response.status} - ${errorMsg}`);
            }
            return responseData;
        } catch (error) {
            console.error(`Fehler beim Senden von Daten (${endpoint}):`, error);
            showGlobalNotification(`Fehler beim Senden von Daten: ${error.message}`, 'error');
            return null;
        }
    }

    /**
     * Füllt ein <select>-Element mit Optionen aus einem Datenarray.
     * @param {HTMLSelectElement} selectElement - Das zu füllende Select-Element.
     * @param {Array<Object>} data - Array von Objekten für die Optionen.
     * @param {string} valueField - Name des Feldes im Objekt für den option.value.
     * @param {string|Function} textField - Name des Feldes für den option.textContent oder eine Funktion, die das Item erhält und den Text zurückgibt.
     * @param {string} [defaultOptionText="-- Bitte wählen --"] - Text für die erste, leere Option.
     */
    function populateSelect(selectElement, data, valueField, textField, defaultOptionText = "-- Bitte wählen --") {
        selectElement.innerHTML = `<option value="">${defaultOptionText}</option>`;
        if (data && Array.isArray(data)) {
            data.forEach(item => {
                const option = document.createElement('option');
                option.value = item[valueField];
                option.textContent = typeof textField === 'function'
                    ? textField(item)
                    : item[textField];
                selectElement.appendChild(option);
            });
        }
        selectElement.disabled = !data || data.length === 0;
    }

    /**
     * Zeigt eine einfache globale Benachrichtigung an (Beispielimplementierung).
     * @param {string} message - Die anzuzeigende Nachricht.
     * @param {'success'|'error'|'info'} type - Typ der Nachricht (beeinflusst Styling).
     * @param {number} duration - Wie lange die Nachricht sichtbar bleibt (in ms).
     */
    function showGlobalNotification(message, type = 'info', duration = 5000) {
        let notificationArea = document.getElementById('globalNotificationArea');
        if (!notificationArea) {
            notificationArea = document.createElement('div');
            notificationArea.id = 'globalNotificationArea';
            // Styling für notificationArea sollte in general.css sein
            // z.B. position: fixed, top: 20px, right: 20px, z-index: 2000
            document.body.appendChild(notificationArea);
        }

        const notification = document.createElement('div');
        notification.classList.add('global-notification', `global-notification-${type}`);
        notification.textContent = message;

        notificationArea.appendChild(notification);

        setTimeout(() => {
            notification.style.opacity = '0'; // Für Fade-Out-Effekt
            setTimeout(() => {
                notification.remove();
                if (notificationArea.childElementCount === 0) {
                    // Optional: notificationArea entfernen, wenn leer, oder einfach lassen
                }
            }, 500); // Zeit für Fade-Out
        }, duration);
    }

    // Öffentliche API des Moduls/Namespaces
    return {
        API_BASE_URL,
        fetchData,
        postData,
        populateSelect,
        showGlobalNotification
    };
})();

// Event Listener für DOMContentLoaded kann hier auch für globale Initialisierungen genutzt werden,
// die auf JEDER Seite ausgeführt werden sollen.
document.addEventListener('DOMContentLoaded', () => {
    console.log("General JS geladen und DOM bereit.");

    // Beispiel: Globale Initialisierung für alle Modals (falls ein gemeinsames Muster existiert)
    // document.querySelectorAll('.meine-globalen-buttons').forEach(button => {
    //     button.addEventListener('click', () => {
    //         AppUtils.showGlobalNotification('Globaler Button geklickt!', 'info');
    //     });
    // });
});

// Funktion zum Laden des Headers mit Navbar
async function loadHeader() { // Funktion zu 'async' machen, da wir 'await' verwenden
    const headerPlaceholder = document.getElementById('header-placeholder');
    if (!headerPlaceholder) {
        console.warn("Element mit ID 'header-placeholder' nicht gefunden.");
        return;
    }

    let userData = { logged_in: false }; // Standardwert: nicht angemeldet

    try {
        // Rufe den neuen Flask-Endpoint ab, um den Benutzerstatus zu erhalten
        const response = await fetch('/get_user_status');
        if (response.ok) {
            userData = await response.json(); // Parse die JSON-Antwort
        } else {
            console.error('Fehler beim Abrufen des Benutzerstatus:', response.status);
            // Optional: Zeige eine Fehlermeldung auf der Konsole oder im UI an
        }
    } catch (error) {
        console.error('Netzwerkfehler beim Abrufen des Benutzerstatus:', error);
        // Optional: Zeige eine Fehlermeldung auf der Konsole oder im UI an
    }

    // Baue den Header-Inhalt basierend auf den abgerufenen Benutzerdaten
    headerPlaceholder.innerHTML = `
        <header>
            <div class="header-content">
                <h1>Wettkampf Manager</h1>
                <nav class="main-nav">
                    <ul>
                        <li><a href="/wettkampfManager">Home</a></li>
                        <li><a href="/wettkampfAnsicht">Ansicht</a></li>
                        ${userData.logged_in ? `
                            <li><a href="/wettkampfDateneingabe">Dateneingabe</a></li>
                            <li><a href="/wettkampfMassenImport">Massenimport</a></li>
                        ` : ''}
                        ${userData.logged_in && userData.role === 'admin' ? `
                            <li><a href="/wettkampfManagerAdmincenter">Admincenter</a></li>
                        ` : ''}
                    </ul>
                </nav>
                <nav class="auth-nav">
                    <ul>
                        ${userData.logged_in ? `
                            <li class="user-info">Hallo, ${userData.username}! (Rolle: ${userData.role})</li>
                            <li><a href="/logout" class="button">Logout</a></li>
                        ` : `
                            <li><a href="/login" class="button">Login</a></li>
                            <li><a href="/register" class="button">Register</a></li>
                        `}
                    </ul>
                </nav>
            </div>
        </header>
    `;
}

// Funktion zum Laden des Footers
function loadFooter() {
    const footerPlaceholder = document.getElementById('footer-placeholder');
    if (footerPlaceholder) {
        const currentYear = new Date().getFullYear();
        footerPlaceholder.innerHTML = `
            <footer>
                <p>&copy; ${currentYear} Wettkampf Manager Mertz. Version 0.1. Alle Rechte vorbehalten.</p>
                <p><a href="/datenschutz">Datenschutz</a> | <a href="/impressum">Impressum</a></p>
            </footer>
        `;
    }
}

// Funktionen aufrufen, sobald das DOM geladen ist
document.addEventListener('DOMContentLoaded', () => {
    loadHeader();
    loadFooter();
});