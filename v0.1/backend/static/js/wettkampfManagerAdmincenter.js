// admincenter.js
document.addEventListener('DOMContentLoaded', () => {
    console.log("Admincenter JS geladen.");

    // Beispiel-Elemente
    const userListTableBody = document.getElementById('userListTableBody'); // Annahme
    const configForm = document.getElementById('configForm');             // Annahme
    const clearCacheButton = document.getElementById('clearCacheButton');   // Annahme

    // ----- Benutzer auflisten (Beispiel) -----
    async function ladeBenutzer() {
        if (!userListTableBody) return;

        // Annahme: Backend Endpunkt GET /api/admin/users
        const users = await AppUtils.fetchData('/admin/users');
        userListTableBody.innerHTML = '';

        if (users && users.length > 0) {
            users.forEach(user => {
                const row = userListTableBody.insertRow();
                row.insertCell().textContent = user.id;
                row.insertCell().textContent = user.username;
                row.insertCell().textContent = user.email;
                row.insertCell().textContent = user.role;
                row.insertCell().textContent = new Date(user.last_login).toLocaleString();

                const aktionenCell = row.insertCell();
                const editBtn = document.createElement('button');
                editBtn.textContent = 'Rolle ändern';
                editBtn.classList.add('btn', 'btn-small');
                editBtn.onclick = () => changeUserRole(user.id, user.username); // Funktion implementieren
                aktionenCell.appendChild(editBtn);
            });
        } else if (users) {
            const row = userListTableBody.insertRow();
            const cell = row.insertCell();
            cell.colSpan = 5;
            cell.textContent = "Keine Benutzer gefunden.";
            cell.style.textAlign = "center";
        } else {
            // Fehler...
        }
    }

    function changeUserRole(userId, username) {
        const neueRolle = prompt(`Neue Rolle für ${username} eingeben (z.B. admin, manager, user):`);
        if (neueRolle) {
            // POST /api/admin/users/{userId}/role mit { role: neueRolle }
            AppUtils.showGlobalNotification(`Rollenänderung für ${userId} zu ${neueRolle} angefordert (Funktion noch nicht implementiert).`, 'info');
        }
    }

    // ----- Konfiguration speichern (Beispiel) -----
    if (configForm) {
        // Konfiguration zuerst laden
        AppUtils.fetchData('/admin/config').then(config => {
            if (config) {
                for (const key in config) {
                    if (configForm.elements[key]) {
                        if (configForm.elements[key].type === 'checkbox') {
                            configForm.elements[key].checked = config[key];
                        } else {
                            configForm.elements[key].value = config[key];
                        }
                    }
                }
            }
        });

        configForm.addEventListener('submit', async (event) => {
            event.preventDefault();
            const formData = new FormData(configForm);
            const configData = {};
            formData.forEach((value, key) => {
                // Checkboxen korrekt behandeln
                if (configForm.elements[key] && configForm.elements[key].type === 'checkbox') {
                    configData[key] = configForm.elements[key].checked;
                } else {
                    configData[key] = value;
                }
            });

            const result = await AppUtils.postData('/admin/config', configData);
            if (result && result.success) {
                AppUtils.showGlobalNotification('Konfiguration gespeichert!', 'success');
            } else {
                AppUtils.showGlobalNotification(result?.error || 'Fehler beim Speichern der Konfiguration.', 'error');
            }
        });
    }

    // ----- Cache leeren (Beispiel) -----
    if (clearCacheButton) {
        clearCacheButton.addEventListener('click', async () => {
            if (confirm("Möchten Sie den System-Cache wirklich leeren?")) {
                const result = await AppUtils.postData('/admin/clear-cache', {});
                if (result && result.success) {
                    AppUtils.showGlobalNotification('Cache geleert!', 'success');
                } else {
                    AppUtils.showGlobalNotification(result?.error || 'Fehler beim Leeren des Caches.', 'error');
                }
            }
        });
    }


    // Initialisierung für die Admincenter-Seite
    ladeBenutzer();

const wettkampfTagFilterSelect = document.getElementById('wettkampfTagFilterSelect');
const ladeErgebnisseBtn = document.getElementById('ladeErgebnisseBtn');
const exportExcelBtn = document.getElementById('exportExcelBtn');
const ergebnisAnzeigeBereich = document.getElementById('ergebnisAnzeigeBereich');

// 👇 1. Dropdown mit Wettkampftagen befüllen
async function ladeWettkampfTage() {
    if (wettkampfTagFilterSelect) {
        const wettkampftage = await AppUtils.fetchData('/wettkampftage');
        AppUtils.populateSelect(wettkampfTagFilterSelect, wettkampftage, 'idWettkampf_Tag', 'Name', '-- Alle Wettkampftage --');
    }
}

// 👇 2. Ergebnisse anzeigen (wie bisher)
async function ladeUndZeigeErgebnisse() {
    const wettkampfTagId = wettkampfTagFilterSelect.value;
    if (!wettkampfTagId) {
        ergebnisAnzeigeBereich.innerHTML = '<p class="text-danger">Bitte einen Wettkampftag wählen.</p>';
        exportExcelBtn.disabled = true;
        return;
    }

    const endpoint = `/gesamtergebnisse_ansicht_Tag?tag_id=${wettkampfTagId}`;
    AppUtils.showGlobalNotification('Lade Ergebnisse...', 'info', 2000);

    const ergebnisse = await AppUtils.fetchData(endpoint);

    if (ergebnisse && ergebnisse.length > 0) {
        let html = '<table class="table table-striped rangliste-tabelle"><thead><tr><th>Platz</th><th>Name</th><th>Verein</th><th>GesamtScore</th><th>Wettkampf</th></tr></thead><tbody>';
        
        ergebnisse.forEach(e => {
            let klasse = '';
            if (e.Platz === 1) klasse = 'platz-1';
            else if (e.Platz === 2) klasse = 'platz-2';
            else if (e.Platz === 3) klasse = 'platz-3';

            html += `<tr class="${klasse}">
                <td>${e.Platz || '-'}</td>
                <td>${e.Vorname || ''} ${e.Nachname || ''}</td>
                <td>${e.Verein || '-'}</td>
                <td>${e.GesamtScore || '-'}</td>
                <td>${e.WettkampfName || '-'}</td>
            </tr>`;
        });

        html += '</tbody></table>';
        ergebnisAnzeigeBereich.innerHTML = html;
        document.getElementById('generateExcelBtn').disabled = false;
    } else {
        ergebnisAnzeigeBereich.innerHTML = '<p>Keine Ergebnisse für den gewählten Tag gefunden.</p>';
        document.getElementById('generateExcelBtn').disabled = true;
    }

}



// 👉 Event Listener
ladeErgebnisseBtn.addEventListener('click', ladeUndZeigeErgebnisse);


// Beim Laden die Tags füllen
ladeWettkampfTage();
});

document.getElementById('generateExcelBtn').addEventListener('click', () => {
    const tagId = document.getElementById('wettkampfTagFilterSelect').value;
    fetch(`/api/erzeuge_excel?tag_id=${tagId}`)
        .then(res => res.json())
        .then(data => {
            if (data.filename) {
                window.generatedFile = data.filename;
                document.getElementById('downloadExcelBtn').disabled = false;
                alert('Excel-Datei erstellt!');
            } else {
                alert('Fehler: ' + data.error);
            }
        });
});

document.getElementById('downloadExcelBtn').addEventListener('click', () => {
    if (!window.generatedFile) {
        alert("Bitte zuerst Datei erzeugen!");
        return;
    }
    window.location.href = `/api/download_excel?filename=${window.generatedFile}`;
});