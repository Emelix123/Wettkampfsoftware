let isModalOpen = false;

document.addEventListener('DOMContentLoaded', () => {
    // API Basispfad (anpassen, falls notwendig)
    const API_BASE_URL = '/api'; // Beispiel: '/api' oder 'http://localhost:5000/api'

    // --- HTML Elemente selektieren ---
    // Globale Selektoren
    const wettkampfTagSelect = document.getElementById('wettkampfTagSelect');
    const wettkampfSelect = document.getElementById('wettkampfSelect');
    const geraetSelect = document.getElementById('geraetSelect');
    const ansichtTypSelect = document.getElementById('ansichtTypSelect');
    const resetViewBtn = document.getElementById('resetViewBtn');

    // Suchbereiche & Eingabefelder
    const riegeSucheBereich = document.getElementById('riegeSucheBereich');
    const personSucheBereich = document.getElementById('personSucheBereich');
    const riegeInput = document.getElementById('riegeInput');
    const riegeSuchenBtn = document.getElementById('riegeSuchenBtn');
    const personSuchbegriffInput = document.getElementById('personSuchbegriffInput');
    const personSuchenBtn = document.getElementById('personSuchenBtn');

    // Teilnehmer Tabelle
    const teilnehmerTabelleBody = document.getElementById('teilnehmerTabelleBody');
    const keineTeilnehmerInfo = document.getElementById('keineTeilnehmerInfo');

    // Modal Elemente
    const wertungModal = document.getElementById('wertungModal');
    const wertungModalTitle = document.getElementById('wertungModalTitle'); // Wird aktuell nicht dynamisch genutzt, ggf. später?
    const personNameModal = document.getElementById('personNameModal');
    const wertungForm = document.getElementById('wertungForm');
    const wertungsVariablenContainer = document.getElementById('wertungsVariablenContainer');
    const personIdInputModal = document.getElementById('personIdInputModal');
    const geraeteWettkampfIdInputModal = document.getElementById('geraeteWettkampfIdInputModal');
    const existierendesErgebnisIdInputModal = document.getElementById('existierendesErgebnisIdInputModal');
    const versuchNrInputModal = document.getElementById('versuchNrInputModal');
    const closeModalButton = document.querySelector('.close-button'); // Eindeutiger Selektor, falls mehrere existieren
    const loeschButton = document.getElementById('loeschButton');
    const speichernButton = document.getElementById('speichernButton'); // Annahme, dass du diese Variable definieren musst



    // --- Globale Zustandsvariablen ---
    let aktuelleGeraeteDetails = {}; // Speichert Details zum aktuellen Gerät (z.B. Anzahl_Var, idGeraeteWettkampf, Anzahl_Versuche)
    let aktuelleTeilnehmerListe = []; // Dient als Cache für die aktuell angezeigten Teilnehmer
    let einzelErgebnisse = []; // Speichert die geladenen Einzelergebnisse für die aktuelle Auswahl


    // --- Hilfsfunktionen ---

    /**
     * Führt einen GET-Request an die API aus.
     * @param {string} endpoint - Der API-Endpunkt (z.B. '/wettkampftage').
     * @returns {Promise<Object|null>} - Die JSON-Antwort oder null bei einem Fehler.
     */
    async function fetchData(endpoint) {
        try {
            const response = await fetch(`${API_BASE_URL}${endpoint}`);
            if (!response.ok) {
                // Versuche, eine detailliertere Fehlermeldung vom Server zu bekommen
                let errorText = response.statusText;
                try {
                    const errorData = await response.json();
                    errorText = errorData.message || errorText;
                } catch (e) {
                    // Ignoriere, falls Body keine JSON-Fehlermeldung ist
                }
                throw new Error(`API-Fehler (${response.status}): ${errorText}`);
            }
            return await response.json();
        } catch (error) {
            console.error(`Fehler beim Laden von Daten (${endpoint}):`, error);
            alert(`Fehler beim Laden von Daten: ${error.message}`);
            return null;
        }
    }

    /**
     * Führt einen POST-Request an die API aus.
     * @param {string} endpoint - Der API-Endpunkt.
     * @param {Object} data - Die zu sendenden Daten.
     * @returns {Promise<Object|null>} - Die JSON-Antwort oder null bei einem Fehler.
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
            if (!response.ok) {
                let errorText = response.statusText;
                try {
                    const errorData = await response.json();
                    errorText = errorData.message || errorText; // Bevorzuge Server-Message
                } catch (e) {
                    // Ignoriere, falls Body keine JSON-Fehlermeldung ist
                }
                throw new Error(`API-Fehler (${response.status}): ${errorText}`);
            }
            return await response.json();
        } catch (error) {
            console.error(`Fehler beim Senden von Daten (${endpoint}):`, error);
            alert(`Fehler beim Senden von Daten: ${error.message}`);
            return null;
        }
    }

    /**
     * Befüllt ein Select-Element mit Optionen.
     * @param {HTMLSelectElement} selectElement - Das zu befüllende Select-Element.
     * @param {Array<Object>} data - Array von Objekten für die Optionen.
     * @param {string} valueField - Name des Feldes für den `value` der Option.
     * @param {string} textField - Name des Feldes für den angezeigten Text der Option.
     * @param {string} [defaultOptionText="-- Bitte wählen --"] - Text für die Standardoption.
     */
    function populateSelect(selectElement, data, valueField, textField, defaultOptionText = "-- Bitte wählen --") {
        selectElement.innerHTML = `<option value="">${defaultOptionText}</option>`;
        if (data && Array.isArray(data)) {
            data.forEach(item => {
                const option = document.createElement('option');
                option.value = item[valueField];
                option.textContent = item[textField];
                selectElement.appendChild(option);
            });
        }
        selectElement.disabled = !data || data.length === 0;
    }

    /**
     * Erstellt einen Button mit Standardklassen und Event-Handler.
     * @param {string} text - Der Text des Buttons.
     * @param {Function} handler - Die Funktion, die bei Klick ausgeführt wird.
     * @returns {HTMLButtonElement} Der erstellte Button.
     */
    function createActionButton(text, handler) {
        const btn = document.createElement('button');
        btn.textContent = text;
        btn.classList.add('btn', 'btn-small'); // Ggf. spezifischere Klassen hinzufügen
        btn.onclick = handler;
        return btn;
    }

    // --- Ladefunktionen für Dropdowns ---

    async function ladeWettkampfTage() {
        const data = await fetchData('/wettkampftage');
        populateSelect(wettkampfTagSelect, data, 'idWettkampf_Tag', 'Name', '-- Wettkampftag wählen --');
    }

    async function ladeWettkaempfe(tagId) {
        if (!tagId) {
            populateSelect(wettkampfSelect, [], 'idWettkampf', 'Name');
            geraetSelect.innerHTML = '<option value="">-- Bitte wählen --</option>';
            geraetSelect.disabled = true;
            ansichtTypSelect.value = 'alle';
            ansichtTypSelect.disabled = true;
            resetTeilnehmerTabelle();
            return;
        }
        const data = await fetchData(`/wettkaempfe?tag_id=${tagId}`);
        populateSelect(wettkampfSelect, data, 'idWettkampf', 'Name', '-- Wettkampf wählen --');
        // Reset für abhängige Elemente
        geraetSelect.innerHTML = '<option value="">-- Bitte wählen --</option>';
        geraetSelect.disabled = true;
        ansichtTypSelect.value = 'alle';
        ansichtTypSelect.disabled = true;
        resetTeilnehmerTabelle();
    }

    async function ladeGeraete(wettkampfId) {
        aktuelleGeraeteDetails = {}; // Zurücksetzen vor Neuladen
        if (!wettkampfId) {
            populateSelect(geraetSelect, [], 'idGeraete', 'Name');
            ansichtTypSelect.value = 'alle';
            ansichtTypSelect.disabled = true;
            resetTeilnehmerTabelle();
            return;
        }
        // Annahme: API liefert {idGeraete, Name, Anzahl_Var, idGeraete_Wettkampf, Berechnung_Variante, Anzahl_Versuche}
        const data = await fetchData(`/geraete_fuer_wettkampf?wettkampf_id=${wettkampfId}`);
        populateSelect(geraetSelect, data, 'idGeraete', 'Name', '-- Gerät wählen --');
        if (data) {
            data.forEach(g => {
                aktuelleGeraeteDetails[g.idGeraete] = {
                    anzahlVar: g.Anzahl_Var,
                    idGeraeteWettkampf: g.idGeraete_Wettkampf,
                    berechnungVariante: g.Berechnung_Variante,
                    anzahlVersuche: g.Anzahl_Durchfuehrungen || 1 // Default auf 1 Versuch, falls nicht von API geliefert
                };
            });
        }
        ansichtTypSelect.value = 'alle';
        ansichtTypSelect.disabled = !data || data.length === 0;
        resetTeilnehmerTabelle();
    }

    // --- Teilnehmer und Ergebnisse laden und anzeigen ---

    async function ladeEinzelErgebnisse() {
        try {
            const res = await fetch('/api/einzel_ergebnisse');
            einzelErgebnisse = await res.json();
            console.log("Einzel-Ergebnisse geladen:", einzelErgebnisse);
        } catch (error) {
            console.error("Fehler beim Laden der Einzel-Ergebnisse:", error);
        }
    }

    async function ladeTeilnehmer() {
        const wettkampfId = wettkampfSelect.value;
        const geraetId = geraetSelect.value; // ID des ausgewählten Geräts
        const ansichtTyp = ansichtTypSelect.value;

        resetTeilnehmerTabelle(); // Immer zuerst Tabelle leeren

        if (!wettkampfId || !geraetId) {
            keineTeilnehmerInfo.textContent = "Bitte zuerst Wettkampf und Gerät auswählen.";
            keineTeilnehmerInfo.style.display = 'block';
            aktuelleTeilnehmerListe = []; // Liste auch leeren
            return;
        }
        keineTeilnehmerInfo.style.display = 'none';

        // Vor dem Laden der Teilnehmer sollten die dazugehörigen Ergebnisse geladen sein
        // Dies wird nun im Event Listener von geraetSelect erledigt oder nach dem Speichern.

        let queryParams = `wettkampf_id=${wettkampfId}&geraet_id=${geraetId}`;

        if (ansichtTyp === 'riege') {
            const riegeNr = riegeInput.value.trim();
            if (!riegeNr) {
                alert("Bitte eine Riegen-Nummer eingeben.");
                aktuelleTeilnehmerListe = [];
                return;
            }
            queryParams += `&filter_typ=riege&filter_wert=${encodeURIComponent(riegeNr)}`;
        } else if (ansichtTyp === 'person') {
            const suchbegriff = personSuchbegriffInput.value.trim();
            if (!suchbegriff) {
                alert("Bitte einen Suchbegriff (Name/ID) eingeben.");
                aktuelleTeilnehmerListe = [];
                return;
            }
            queryParams += `&filter_typ=person&filter_wert=${encodeURIComponent(suchbegriff)}`;
        }
        // Für "alle" ist kein weiterer Parameter nötig

        const teilnehmerDaten = await fetchData(`/teilnehmer_fuer_eingabe?${queryParams}`);
        aktuelleTeilnehmerListe = teilnehmerDaten || [];

        renderTeilnehmerTabelle(aktuelleTeilnehmerListe); // Tabelle neu aufbauen mit aktualisierten Ergebnissen

    }

    /**
     * Rendert die Teilnehmer-Tabelle.
     * Lädt vorher die aktuellen Einzelergebnisse für den gewählten Kontext.
     * @param {Array<Object>} teilnehmer - Array von Teilnehmerobjekten.
     */
    async function renderTeilnehmerTabelle(teilnehmer) {
        // 1. Ergebnisse laden, bevor die Tabelle gerendert wird.
        //    Dies stellt sicher, dass `einzelErgebnisse` die aktuellsten Daten enthält.
        //    Diese Zeile geht davon aus, dass `ladeEinzelErgebnisse` so implementiert ist,
        //    dass es die Ergebnisse für den aktuell im UI ausgewählten Wettkampf und Gerät lädt.
        await ladeEinzelErgebnisse();

        teilnehmerTabelleBody.innerHTML = ''; // Tabelle leeren

        if (!teilnehmer || teilnehmer.length === 0) {
            keineTeilnehmerInfo.textContent = "Keine Teilnehmer für die aktuelle Auswahl gefunden.";
            keineTeilnehmerInfo.style.display = 'block';
            return;
        }
        keineTeilnehmerInfo.style.display = 'none';

        teilnehmer.forEach(p => {
            const row = teilnehmerTabelleBody.insertRow();
            row.dataset.personId = p.id; // Für Drag & Drop und Identifikation

            // Basisdaten der Person
            row.insertCell().textContent = p.id;
            row.insertCell().textContent = p.vorname;
            row.insertCell().textContent = p.nachname;
            row.insertCell().textContent = p.verein || '–';
            row.insertCell().textContent = p.riege || '–';

            // Ergebnisse für diesen Teilnehmer und dieses Gerät filtern
            // p.geraete_wettkampf_id ist die spezifische ID für die Kombination Teilnehmer-Wettkampf-Gerät
            // p.geraete_id ist die ID des ausgewählten Geräts (z.B. Barren)

            const passendeErgebnisse = einzelErgebnisse.filter(e =>
                e.Personen_idPersonen === p.id &&
                e.Geraete_Wettkampf_idGeraete_Wettkampf === p.geraete_wettkampf_id
            );
            
            // Sortiere Ergebnisse nach Versuch_Nr, falls mehrere vorhanden
            passendeErgebnisse.sort((a, b) => (a.Versuch_Nr || 0) - (b.Versuch_Nr || 0));

            // Max. Versuche für das Gerät holen
            // p.geraete_id MUSS von der API im Teilnehmerobjekt mitgeliefert werden.
            const geraetDetail = aktuelleGeraeteDetails[p.geraete_id];
            console.log("Gerätedetails für ID:", p.geraete_id, geraetDetail, aktuelleGeraeteDetails);
            if (!geraetDetail) {
                console.warn(`Gerätedetails für geraete_id ${p.geraete_id} nicht gefunden. Teilnehmer:`, p);
            }
            const maxVersuche = geraetDetail?.anzahlVersuche || 1;
            console.log("Maximale Versuche für Gerät:", maxVersuche, geraetDetail);
            // Ergebnis-Zelle füllen
            const ergebnisCell = row.insertCell();
            if (passendeErgebnisse.length > 0) {
                // Zeige alle Scores, getrennt durch " | "
                // Stelle sicher, dass e.Score das Feld ist, das den finalen Wert des Versuchs enthält.
                ergebnisCell.textContent = passendeErgebnisse.map(e => e.Score ?? 'N/A').join(' | ');
            } else {
                ergebnisCell.textContent = '–';
            }

            // Aktions-Zelle füllen
            const aktionCell = row.insertCell();
            aktionCell.classList.add('action-cell'); // Für eventuelles Styling

            // Logik für Eintragen- und Bearbeiten-Buttons
            const anzahlErfassterVersuche = passendeErgebnisse.length;
            const naechsterVersuchNr = anzahlErfassterVersuche + 1;

            // Eintragen-Button für den nächsten Versuch
            const btnEintragen = createActionButton(`Versuch ${naechsterVersuchNr} Eintragen`, () =>
                oeffneWertungModal(p, naechsterVersuchNr, false) // false für istBearbeiten
            );
            if (anzahlErfassterVersuche >= maxVersuche) {
                btnEintragen.disabled = true; // Alle Versuche ausgeschöpft
                btnEintragen.title = "Maximale Anzahl an Versuchen erreicht.";
            } else {
                btnEintragen.disabled = false;
            }
            aktionCell.appendChild(btnEintragen);

            // Bearbeiten-Button (immer letzter vorhandener Versuch)
            const letzterErfassterVersuch = passendeErgebnisse[anzahlErfassterVersuche - 1]; // undefined, wenn keine Ergebnisse

            const btnBearbeiten = createActionButton(
                letzterErfassterVersuch ? `Versuch ${letzterErfassterVersuch.Versuch_Nr} Bearbeiten` : 'Bearbeiten',
                () => oeffneWertungModal(p, letzterErfassterVersuch?.Versuch_Nr || 1, true) // true für istBearbeiten
            );

            if (!letzterErfassterVersuch) { // Kein Versuch zum Bearbeiten vorhanden
                btnBearbeiten.disabled = true;
                btnBearbeiten.title = "Kein Versuch zum Bearbeiten vorhanden.";
            }
            aktionCell.appendChild(btnBearbeiten);
        });

        // 2. Gespeicherte Reihenfolge anwenden, nachdem alle Zeilen im DOM sind.
        wendeGespeicherteReihenfolgeAn();
    }

    function createActionButton(label, onClick) {
        const button = document.createElement('button');
        button.classList.add('btn', 'btn-small');
        button.textContent = label;

        // Klick- und Touch-Events binden
        button.addEventListener('click', onClick);
        button.addEventListener('touchstart', onClick); // Wichtig für Mobile

        return button;
    }


    function resetTeilnehmerTabelle() {
        teilnehmerTabelleBody.innerHTML = '';
        keineTeilnehmerInfo.textContent = '';
        keineTeilnehmerInfo.style.display = 'none';
        aktuelleTeilnehmerListe = []; // Auch die interne Liste leeren
        // console.log("Teilnehmer-Tabelle wurde zurückgesetzt.");
    }

/**
 * Speichert die Wertung (oder aktualisiert sie).
 * Diese Funktion wird nun direkt vom "Wertung speichern"-Button aufgerufen.
 */
async function handleWertungSpeichern(event) {
    event.preventDefault(); // Verhindert das Standard-Formular-Submit

    // Zusätzliche Prüfungen (optional, aber gut für Robustheit)
    if (!geraetSelect.value || !wettkampfSelect.value) {
        alert("Bitte wählen Sie zuerst einen Wettkampf und ein Gerät aus.");
        return;
    }
    if (isModalOpen === false) { // Sollte nicht passieren, wenn der Click-Listener am Button hängt
        console.warn("handleWertungSpeichern wurde aufgerufen, obwohl das Modal als geschlossen markiert ist.");
        // Optional: Modal erneut öffnen oder Fehler melden
        return;
    }


    const formData = new FormData(wertungForm);
    const ausgewaehlteGeraetId = geraetSelect.value;
    const geraetDetail = aktuelleGeraeteDetails[ausgewaehlteGeraetId];

    if (!geraetDetail) {
        alert("Fehler: Gerätedetails nicht gefunden. Speichern nicht möglich.");
        return;
    }

    const wertung = {
        personen_id: parseInt(personIdInputModal.value),
        geraete_wettkampf_id: parseInt(geraeteWettkampfIdInputModal.value),
        versuch_nr: parseInt(versuchNrInputModal.value) || 1,
    };

    let formValid = true;
    for (let i = 1; i <= geraetDetail.anzahlVar; i++) {
        const wert = formData.get(`var${i}`);
        if (wert === null || wert.trim() === '') {
            wertung[`var${i}`] = null;
        } else {
            wertung[`var${i}`] = parseFloat(wert);
            if (isNaN(wertung[`var${i}`])) {
                alert(`Ungültiger Wert für Variable ${i}.`);
                formValid = false;
                break;
            }
        }
    }

    if (!formValid) {
        return;
    }

    console.log("Sende Wertung:", wertung);

    const result = await postData('/einzelwertung_speichern', wertung);
    if (result) {
        alert(result.message || "Wertung erfolgreich gespeichert!");
        schliesseWertungModal();
        await ladeEinzelErgebnisse();
        await ladeTeilnehmer();
    }
}

/**
 * Löscht einen einzelnen Wertungseintrag.
 * Diese Funktion wird vom "Löschen"-Button aufgerufen.
 */
async function handleWertungLoeschen() {
    if (confirm("Diesen einzelnen Versuch wirklich löschen?")) {
        const personen_id = parseInt(personIdInputModal.value);
        const geraete_wettkampf_id = parseInt(geraeteWettkampfIdInputModal.value);
        const versuch_nr = parseInt(versuchNrInputModal.value);
        
        console.log("Lösche Versuch:", personen_id, geraete_wettkampf_id, versuch_nr);

        if (isNaN(versuch_nr) || versuch_nr <= 0) {
            alert("Bitte geben Sie eine gültige Versuch-Nummer ein.");
            return;
        }
        
        const dataZumLoeschen = {
            personen_id: personen_id,
            geraete_wettkampf_id: geraete_wettkampf_id,
            versuch_nr: versuch_nr
        };

        console.log("Sende Löschanfrage für:", dataZumLoeschen);

        const result = await postData('/einzelwertung_loeschen', dataZumLoeschen);

        if (result && result.success) {
            alert(result.message || "Eintrag erfolgreich gelöscht.");
            schliesseWertungModal(); // Modal schließen
            await ladeEinzelErgebnisse();
            await ladeTeilnehmer();
        } else {
            alert(result.message || "Fehler beim Löschen.");
        }
    }
}

/**
 * Öffnet das Modal zur Eingabe oder Bearbeitung einer Wertung.
 */
async function oeffneWertungModal(person, versuchNr = 1) {
    isModalOpen = true; // Modal ist jetzt offen

    const ausgewaehlteGeraetId = geraetSelect.value;
    const geraetDetail = aktuelleGeraeteDetails[ausgewaehlteGeraetId];

    if (!geraetDetail) {
        alert("Gerätedetails nicht gefunden. Bitte Gerät korrekt auswählen.");
        return;
    }
    if (!person.geraete_wettkampf_id) {
        alert("Fehler: geraete_wettkampf_id für Person nicht gefunden. Daten unvollständig?");
        console.error("Personenobjekt:", person);
        return;
    }

    wertungForm.reset();
    wertungsVariablenContainer.innerHTML = '';
    existierendesErgebnisIdInputModal.value = '';

    personNameModal.textContent = `${person.vorname} ${person.nachname} - Versuch ${versuchNr}`;
    personIdInputModal.value = person.id;
    geraeteWettkampfIdInputModal.value = person.geraete_wettkampf_id;
    versuchNrInputModal.value = versuchNr;

    const vorhandenesErgebnis = einzelErgebnisse.find(e =>
        e.Personen_idPersonen === person.id &&
        e.Geraete_Wettkampf_idGeraete_Wettkampf === person.geraete_wettkampf_id &&
        e.Versuch_Nr === versuchNr
    );

    wertungModalTitle.textContent = vorhandenesErgebnis ? `Wertung Bearbeiten (Versuch ${versuchNr} ${person.vorname} ${person.nachname})` : `Wertung Eintragen (Versuch ${versuchNr} ${person.vorname} ${person.nachname})`;

    for (let i = 1; i <= geraetDetail.anzahlVar; i++) {
        const div = document.createElement('div');
        div.classList.add('form-group');

        const label = document.createElement('label');
        label.setAttribute('for', `var${i}_modalInput`);
        label.textContent = `Variable ${i}:`;

        const input = document.createElement('input');
        input.type = 'number';
        input.step = 'any';
        input.name = `var${i}`;
        input.id = `var${i}_modalInput`;
        input.classList.add('form-control');
        input.required = true;

        if (vorhandenesErgebnis && vorhandenesErgebnis[`Var${i}`] !== undefined && vorhandenesErgebnis[`Var${i}`] !== null) {
            input.value = vorhandenesErgebnis[`Var${i}`];
        }

        div.appendChild(label);
        div.appendChild(input);
        wertungsVariablenContainer.appendChild(div);
    }

    // Lösch-Button Logik: Jetzt außerhalb der Schleife, da er einmalig gesetzt wird
    if (vorhandenesErgebnis) {
        loeschButton.style.display = 'inline-block';
        loeschButton.onclick = handleWertungLoeschen; // Direkt die Funktion zuweisen
    } else {
        loeschButton.style.display = 'none';
        loeschButton.onclick = null;
    }

    wertungModal.style.display = 'block';
}


/**
 * Schließt das Wertungs-Modal.
 */
function schliesseWertungModal() {
    wertungModal.style.display = 'none';
    isModalOpen = false; // Modal ist jetzt geschlossen
}


    // --- Drag & Drop für Tabellenreihenfolge (SortableJS) ---
    let sortable = null; // Hält die Sortable Instanz

    function initSortable() {
        if (typeof Sortable !== 'undefined') {
            if (sortable) {
                sortable.destroy(); // Zerstöre alte Instanz, falls vorhanden
            }
            sortable = new Sortable(teilnehmerTabelleBody, {
                animation: 150,
                ghostClass: 'sortable-ghost', // Eigene Klasse für das "Geister"-Element
                chosenClass: 'sortable-chosen', // Eigene Klasse für das gewählte Element
                dragClass: 'sortable-drag',   // Eigene Klasse für das gezogene Element
                onEnd: function () {
                    speichereAktuelleReihenfolge();
                }
            });
        } else {
            console.warn("SortableJS nicht geladen. Drag & Drop für Tabelle nicht verfügbar.");
        }
    }

    function speichereAktuelleReihenfolge() {
        const wettkampfId = wettkampfSelect.value;
        const geraetId = geraetSelect.value;
        if (!wettkampfId || !geraetId) return; // Nur speichern, wenn Kontext klar ist

        const key = `teilnehmerReihenfolge_${wettkampfId}_${geraetId}`;
        const ids = Array.from(teilnehmerTabelleBody.children)
            .map(row => row.dataset.personId)
            .filter(id => id); // Nur gültige IDs
        localStorage.setItem(key, JSON.stringify(ids));
        // console.log(`Reihenfolge für ${key} gespeichert:`, ids);
    }

    // --- Gespeicherte Reihenfolge anwenden ---
    function wendeGespeicherteReihenfolgeAn() {
        const wettkampfId = wettkampfSelect.value;
        const geraetId = geraetSelect.value;
        if (!wettkampfId || !geraetId || teilnehmerTabelleBody.children.length === 0) return;

        const key = `teilnehmerReihenfolge_${wettkampfId}_${geraetId}`;
        const gespeicherteReihenfolgeJSON = localStorage.getItem(key);

        if (!gespeicherteReihenfolgeJSON) return;

        try {
            const gespeicherteReihenfolge = JSON.parse(gespeicherteReihenfolgeJSON);
            if (!Array.isArray(gespeicherteReihenfolge) || gespeicherteReihenfolge.length === 0) return;

            const rows = Array.from(teilnehmerTabelleBody.children);
            const reihenfolgeMap = new Map(gespeicherteReihenfolge.map((id, index) => [id, index]));

            rows.sort((a, b) => {
                const posA = reihenfolgeMap.get(a.dataset.personId);
                const posB = reihenfolgeMap.get(b.dataset.personId);
                // Elemente nicht in gespeicherter Reihenfolge ans Ende
                return (posA === undefined ? Infinity : posA) - (posB === undefined ? Infinity : posB);
            });

            // Nur neu anfügen, wenn sich die Reihenfolge tatsächlich ändert, um unnötige DOM-Operationen zu vermeiden
            let reihenfolgeGeaendert = false;
            for (let i = 0; i < rows.length; i++) {
                if (teilnehmerTabelleBody.children[i] !== rows[i]) {
                    reihenfolgeGeaendert = true;
                    break;
                }
            }

            if (reihenfolgeGeaendert) {
                rows.forEach(row => teilnehmerTabelleBody.appendChild(row));
                // console.log(`Gespeicherte Reihenfolge für ${key} angewendet.`);
            }
        } catch (e) {
            console.error("Fehler beim Parsen oder Anwenden der gespeicherten Reihenfolge:", e);
            localStorage.removeItem(key); // Fehlerhafte Daten entfernen
        }
    }


    // --- Event Listener ---
    wettkampfTagSelect.addEventListener('change', (e) => {
        if (isModalOpen) return; // Event Listener wird nicht ausgeführt, wenn Modal offen ist
        ladeWettkaempfe(e.target.value);
        // Weitere Resets werden in ladeWettkaempfe() gehandhabt
    });

    wettkampfSelect.addEventListener('change', (e) => {
        if (isModalOpen) return; // Event Listener wird nicht ausgeführt, wenn Modal offen ist
        ladeGeraete(e.target.value);
        // Weitere Resets werden in ladeGeraete() gehandhabt
    });

    geraetSelect.addEventListener('change', async (e) => {
        if (isModalOpen) return; // Event Listener wird nicht ausgeführt, wenn Modal offen ist
        if (wettkampfSelect.value && e.target.value) {
            // Wichtig: Erst Ergebnisse laden, dann Teilnehmer, da renderTeilnehmerTabelle die Ergebnisse braucht.
            await ladeEinzelErgebnisse();
            await ladeTeilnehmer(); // Dies ruft auch renderTeilnehmerTabelle und wendeGespeicherteReihenfolgeAn auf
        } else {
            resetTeilnehmerTabelle();
            einzelErgebnisse = []; // Ergebnisse leeren, wenn kein Gerät gewählt
        }
    });

    ansichtTypSelect.addEventListener('change', (e) => {
        if (isModalOpen) return; // Event Listener wird nicht ausgeführt, wenn Modal offen ist
        const typ = e.target.value;
        riegeSucheBereich.style.display = typ === 'riege' ? 'block' : 'none';
        personSucheBereich.style.display = typ === 'person' ? 'block' : 'none';

        // Riege- und Personensuche leeren, wenn auf "alle" gewechselt wird
        if (typ === 'alle') {
            riegeInput.value = '';
            personSuchbegriffInput.value = '';
        }

        // Teilnehmer nur laden, wenn alle Voraussetzungen erfüllt sind
        if (wettkampfSelect.value && geraetSelect.value) {
            if (typ === 'alle') {
                ladeTeilnehmer();
            } else if (typ === 'riege' && riegeInput.value.trim()) {
                ladeTeilnehmer();
            } else if (typ === 'person' && personSuchbegriffInput.value.trim()) {
                ladeTeilnehmer();
            } else if (typ !== 'alle') { // Für Riege/Person, aber Input noch leer
                resetTeilnehmerTabelle();
                keineTeilnehmerInfo.textContent = typ === 'riege' ? "Bitte Riegen-Nummer eingeben und suchen." : "Bitte Suchbegriff eingeben und suchen.";
                keineTeilnehmerInfo.style.display = 'block';
            }
        } else {
            resetTeilnehmerTabelle();
        }
    });

    riegeSuchenBtn.addEventListener('click', () => {
        if (isModalOpen) return; // Event Listener wird nicht ausgeführt, wenn Modal offen ist
        ladeTeilnehmer();
    });

    personSuchenBtn.addEventListener('click', () => {
        if (isModalOpen) return; // Event Listener wird nicht ausgeführt, wenn Modal offen ist
        ladeTeilnehmer();
    });

    // Enter in Suchfeldern soll auch Suche auslösen
    riegeInput.addEventListener('keypress', (e) => {
        if (isModalOpen) return; // Event Listener wird nicht ausgeführt, wenn Modal offen ist
        if (e.key === 'Enter') {
            e.preventDefault(); // Verhindert ggf. Formular-Submit, falls vorhanden
            ladeTeilnehmer();
        }
    });

    personSuchbegriffInput.addEventListener('keypress', (e) => {
        if (isModalOpen) return; // Event Listener wird nicht ausgeführt, wenn Modal offen ist
        if (e.key === 'Enter') {
            e.preventDefault();
            ladeTeilnehmer();
        }
    });

    resetViewBtn.addEventListener('click', () => {
        if (isModalOpen) return; // Event Listener wird nicht ausgeführt, wenn Modal offen ist
        wettkampfTagSelect.value = '';
        // populateSelect leert und deaktiviert die abhängigen Selects
        populateSelect(wettkampfSelect, [], 'idWettkampf', 'Name');
        populateSelect(geraetSelect, [], 'idGeraete', 'Name');
        ansichtTypSelect.value = 'alle';
        ansichtTypSelect.disabled = true;
        riegeSucheBereich.style.display = 'none';
        personSucheBereich.style.display = 'none';
        riegeInput.value = '';
        personSuchbegriffInput.value = '';
        resetTeilnehmerTabelle();
        einzelErgebnisse = [];
        aktuelleGeraeteDetails = {};
        keineTeilnehmerInfo.textContent = "Bitte Grundeinstellungen vornehmen, um Teilnehmer anzuzeigen.";
        keineTeilnehmerInfo.style.display = 'block';
    });

    window.addEventListener('click', (event) => {
        // Dieser Listener sollte ausgeführt werden, um das Modal zu schließen, wenn außerhalb geklickt wird
        // Daher hier keine if-Abfrage
        if (event.target === wertungModal) {
            schliesseWertungModal();
        }
    });

    closeModalButton.addEventListener('click', schliesseWertungModal);
    window.addEventListener('click', (event) => {
        if (event.target === wertungModal) {
            schliesseWertungModal();
        }
    });
    wertungForm.addEventListener('submit', handleWertungSpeichern);
    // ----- Initialisierung -----
    async function init() {
        await ladeWettkampfTage();
        // Initial keine Teilnehmer laden, da Auswahl fehlt
        resetTeilnehmerTabelle();
        keineTeilnehmerInfo.textContent = "Bitte Grundeinstellungen vornehmen, um Teilnehmer anzuzeigen.";
        keineTeilnehmerInfo.style.display = 'block';

        // Suchbereiche initial ausblenden
        riegeSucheBereich.style.display = 'none';
        personSucheBereich.style.display = 'none';
        ansichtTypSelect.disabled = true; // Initial deaktiviert

        initSortable(); // SortableJS initialisieren

    }

    init();
});