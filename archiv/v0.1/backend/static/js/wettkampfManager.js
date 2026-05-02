// manager.js
document.addEventListener('DOMContentLoaded', () => {
    console.log("Manager JS geladen.");

    const neuerWettkampfFormManager = document.getElementById('neuerWettkampfFormManager'); // Annahme
    const wettkampfListeManagerBody = document.getElementById('wettkampfListeManagerBody');   // Annahme: tbody einer Tabelle
    const wettkampfTagSelectManager = document.getElementById('wettkampfTagSelectManager'); // Annahme

    // ----- Wettkampf-Tag Dropdown füllen -----
    async function initManagerSeite() {
        if (wettkampfTagSelectManager) {
            const wettkampftage = await AppUtils.fetchData('/wettkampftage');
            AppUtils.populateSelect(wettkampfTagSelectManager, wettkampftage, 'idWettkampf_Tag', 'Name');
        }
        ladeWettkaempfeManager(); // Initiale Liste laden
    }

    // ----- Neuen Wettkampf anlegen -----
    if (neuerWettkampfFormManager) {
        neuerWettkampfFormManager.addEventListener('submit', async (event) => {
            event.preventDefault();
            const formData = new FormData(neuerWettkampfFormManager);
            const wettkampfData = {};
            formData.forEach((value, key) => {
                wettkampfData[key] = value;
            });

            // Einfache Frontend-Validierung (Beispiel)
            if (!wettkampfData.Wettkampf_Tag_idWettkampf_Tag || !wettkampfData.Name || !wettkampfData.Wettkampf_Nr || !wettkampfData.Altersklasse) {
                AppUtils.showGlobalNotification("Bitte alle Pflichtfelder für den neuen Wettkampf ausfüllen.", "error");
                return;
            }
            // Konvertiere Wettkampf_Nr zu Zahl
            wettkampfData.Wettkampf_Nr = parseInt(wettkampfData.Wettkampf_Nr);


            AppUtils.showGlobalNotification("Speichere Wettkampf...", "info", 2000);
            const result = await AppUtils.postData('/wettkampf', wettkampfData); // Annahme: Backend Endpunkt POST /api/wettkampf

            if (result && result.idWettkampf) { // Annahme: Backend gibt den erstellten Wettkampf mit ID zurück
                AppUtils.showGlobalNotification(`Wettkampf "${result.Name}" erfolgreich erstellt!`, 'success');
                neuerWettkampfFormManager.reset();
                ladeWettkaempfeManager(); // Liste aktualisieren
            } else {
                AppUtils.showGlobalNotification(result?.error || result?.message || "Fehler beim Erstellen des Wettkampfs.", 'error');
            }
        });
    }

    // ----- Wettkämpfe auflisten -----
    async function ladeWettkaempfeManager() {
        if (!wettkampfListeManagerBody) return;

        // Annahme: Backend Endpunkt GET /api/wettkaempfe_details (liefert mehr Infos als nur für Select)
        const alleWettkaempfe = await AppUtils.fetchData('/wettkaempfe_mit_details');
        wettkampfListeManagerBody.innerHTML = ''; // Liste leeren

        if (alleWettkaempfe && alleWettkaempfe.length > 0) {
            alleWettkaempfe.forEach(wk => {
                const row = wettkampfListeManagerBody.insertRow();
                row.insertCell().textContent = wk.idWettkampf;
                row.insertCell().textContent = wk.Wettkampf_Nr;
                row.insertCell().textContent = wk.Name;
                row.insertCell().textContent = wk.Altersklasse;
                row.insertCell().textContent = wk.WettkampfTag_Name || (wk.Wettkampf_Tag ? wk.Wettkampf_Tag.Name : '-'); // Annahme: WettkampfTag_Name wird mitgeliefert
                row.insertCell().textContent = wk.Wettkampf_Datum ? new Date(wk.Wettkampf_Datum).toLocaleDateString() : '-';


                const aktionenCell = row.insertCell();
                const bearbeitenBtn = document.createElement('button');
                bearbeitenBtn.classList.add('btn', 'btn-small');
                bearbeitenBtn.textContent = 'Bearbeiten';
                bearbeitenBtn.onclick = () => bearbeiteWettkampf(wk.idWettkampf); // Funktion muss implementiert werden
                aktionenCell.appendChild(bearbeitenBtn);

                const loeschenBtn = document.createElement('button');
                loeschenBtn.classList.add('btn', 'btn-small', 'btn-danger');
                loeschenBtn.textContent = 'Löschen';
                loeschenBtn.onclick = () => loescheWettkampf(wk.idWettkampf, wk.Name); // Funktion muss implementiert werden
                aktionenCell.appendChild(loeschenBtn);
            });
        } else if (alleWettkaempfe) {
            const row = wettkampfListeManagerBody.insertRow();
            const cell = row.insertCell();
            cell.colSpan = 7; // Anzahl der Spalten
            cell.textContent = "Keine Wettkämpfe gefunden.";
            cell.style.textAlign = "center";
        } else {
            // Fehler beim Laden wurde schon von fetchData behandelt
             const row = wettkampfListeManagerBody.insertRow();
            const cell = row.insertCell();
            cell.colSpan = 7;
            cell.textContent = "Fehler beim Laden der Wettkämpfe.";
            cell.style.textAlign = "center";
        }
    }

    function bearbeiteWettkampf(id) {
        // Hier Logik zum Öffnen eines Bearbeiten-Modals oder einer separaten Seite
        AppUtils.showGlobalNotification(`Bearbeite Wettkampf ID: ${id} (Funktion noch nicht implementiert)`, 'info');
        // Modal füllen mit Daten von GET /api/wettkampf/{id}
        // Beim Speichern PUT /api/wettkampf/{id}
    }

    async function loescheWettkampf(id, name) {
        if (confirm(`Möchten Sie den Wettkampf "${name}" (ID: ${id}) wirklich löschen? Dies kann ggf. abhängige Daten beeinflussen.`)) {
            AppUtils.showGlobalNotification("Lösche Wettkampf...", "info", 2000);
            // Annahme: Backend Endpunkt DELETE /api/wettkampf/{id}
            const result = await AppUtils.postData(`/wettkampf/${id}`, {_method: 'DELETE'}); // Oder echten DELETE Request nutzen
            // Manche Server/Frameworks mögen DELETE nicht direkt im Formular/JS, dann POST mit _method

            // Besser:
            // const response = await fetch(`${AppUtils.API_BASE_URL}/wettkampf/${id}`, { method: 'DELETE' });
            // const result = await response.json(); // oder .text() wenn keine JSON-Antwort
            // if (response.ok) { ... }


            if (result && result.success) { // Annahme: Backend gibt {success: true} zurück
                AppUtils.showGlobalNotification(`Wettkampf "${name}" gelöscht.`, 'success');
                ladeWettkaempfeManager(); // Liste aktualisieren
            } else {
                AppUtils.showGlobalNotification(result?.error || result?.message || "Fehler beim Löschen des Wettkampfs.", 'error');
            }
        }
    }

    // Initialisierung für die Managerseite
    initManagerSeite();
});