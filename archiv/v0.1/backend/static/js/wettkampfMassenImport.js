document.addEventListener('DOMContentLoaded', () => {
    const API_BASE_URL = '/api'; // Anpassen falls notwendig

    const wettkampfTagImportSelect = document.getElementById('wettkampfTagImportSelect');
    const wettkampfImportSelect = document.getElementById('wettkampfImportSelect');
    const teilnehmerDateiInput = document.getElementById('teilnehmerDateiInput');
    const vorschauBereich = document.getElementById('vorschauBereich');
    const vorschauTabelleBody = document.getElementById('vorschauTabelleBody');
    const datenHochladenBtn = document.getElementById('datenHochladenBtn');
    const validierungsInfo = document.getElementById('validierungsInfo');
    const importErgebnisBereich = document.getElementById('importErgebnisBereich');


    let geparsteTeilnehmer = []; // Enthält { rawData: [...], validatedData: {...}, isValid: true/false, errors: [] }

    // ----- Hilfsfunktionen (teilweise aus app.js übernommen) -----
    async function fetchData(endpoint) {
        try {
            const response = await fetch(`${API_BASE_URL}${endpoint}`);
            if (!response.ok) throw new Error(`API-Fehler: ${response.status}`);
            return await response.json();
        } catch (error) {
            console.error(`Fehler beim Laden von Daten (${endpoint}):`, error);
            importErgebnisBereich.innerHTML = `<p class="error">Fehler beim Laden von Daten: ${error.message}</p>`;
            return null;
        }
    }

    async function postData(endpoint, data) {
        try {
            const response = await fetch(`${API_BASE_URL}${endpoint}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data),
            });
            const responseData = await response.json();
            if (!response.ok) {
                throw new Error(responseData.error || responseData.message || `API-Fehler: ${response.status}`);
            }
            return responseData;
        } catch (error) {
            console.error(`Fehler beim Senden von Daten (${endpoint}):`, error);
            importErgebnisBereich.innerHTML = `<p class="error">Fehler beim Senden von Daten: ${error.message}</p>`;
            return null;
        }
    }

    function populateSelect(selectElement, data, valueField, textField, defaultOptionText = "-- Bitte wählen --") {
        selectElement.innerHTML = `<option value="">${defaultOptionText}</option>`;
        if (data) {
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

    // ----- Wettkampf Auswahl -----
    async function ladeWettkampfTageImport() {
        const data = await fetchData('/wettkampftage');
        populateSelect(wettkampfTagImportSelect, data, 'idWettkampf_Tag', 'Name');
    }

    async function ladeWettkaempfeImport(tagId) {
        if (!tagId) {
            populateSelect(wettkampfImportSelect, [], 'idWettkampf', 'Name');
            wettkampfImportSelect.disabled = true;
            return;
        }

        const data = await fetchData(`/wettkaempfe?tag_id=${tagId}`);

        // Dynamisch Name + Nummer anzeigen
        populateSelect(
            wettkampfImportSelect,
            data,
            'idWettkampf',
            item => `${item.Name} (Nr. ${item.Wettkampf_Nr})`
        );
    }
    
    // ----- Datei verarbeiten -----
    teilnehmerDateiInput.addEventListener('change', (event) => {
        const file = event.target.files[0];
        if (!file) return;

        if (!wettkampfImportSelect.value) {
            alert("Bitte wählen Sie zuerst einen Wettkampf aus, dem die Teilnehmer zugeordnet werden sollen.");
            teilnehmerDateiInput.value = ""; // Input zurücksetzen
            return;
        }

        const reader = new FileReader();
        reader.onload = (e) => {
            try {
                const data = new Uint8Array(e.target.result);
                const workbook = XLSX.read(data, { type: 'array', cellDates: true }); // cellDates:true versucht Daten als Datum zu parsen
                const firstSheetName = workbook.SheetNames[0];
                const worksheet = workbook.Sheets[firstSheetName];
                const jsonData = XLSX.utils.sheet_to_json(worksheet, { header: 1, raw: false, dateNF:'dd/mm/yyyy' }); // raw:false für formatierte Werte

                verarbeiteGeparsteDaten(jsonData);
            } catch (error) {
                console.error("Fehler beim Parsen der Excel-Datei:", error);
                alert("Die Datei konnte nicht verarbeitet werden. Stellen Sie sicher, dass es eine gültige .xlsx Datei ist.");
                importErgebnisBereich.innerHTML = `<p class="error">Fehler beim Parsen der Datei: ${error.message}</p>`;
            }
        };
        reader.onerror = (error) => {
             console.error("Fehler beim Lesen der Datei:", error);
             alert("Die Datei konnte nicht gelesen werden.");
             importErgebnisBereich.innerHTML = `<p class="error">Fehler beim Lesen der Datei.</p>`;
        }
        reader.readAsArrayBuffer(file);
    });

    function verarbeiteGeparsteDaten(excelData) {
        geparsteTeilnehmer = [];
        vorschauTabelleBody.innerHTML = '';
        importErgebnisBereich.innerHTML = '';

        if (excelData.length < 2) { // Mindestens eine Header-Zeile und eine Datenzeile
            validierungsInfo.textContent = "Die Datei enthält keine Teilnehmerdaten (oder nur eine Header-Zeile).";
            vorschauBereich.style.display = 'block';
            datenHochladenBtn.disabled = true;
            return;
        }

        // Annahme: Erste Zeile ist der Header, wird ignoriert oder für Mapping genutzt
        const datenZeilen = excelData.slice(1);

        datenZeilen.forEach((row, index) => {
            if (row.filter(cell => cell !== null && cell !== undefined && cell !== "").length === 0) return; // Leere Zeile überspringen

            const teilnehmer = {
                rohDaten: row, // Original Excel-Zeile
                validiertesObjekt: {},
                isValid: true,
                fehler: []
            };

            // Validierung und Mapping (Beispiel)
            const vorname = row[0] ? String(row[0]).trim() : null;
            const nachname = row[1] ? String(row[1]).trim() : null;
            const geburtsdatumrow = row[2] ? String(row[2]).trim() : null;
            const verein = row[3] ? String(row[3]).trim() : null;
            const geschlecht = row[4] ? String(row[4]).toLowerCase().trim() : null;
            let geburtsdatum;

            if (!vorname) {
                teilnehmer.isValid = false;
                teilnehmer.fehler.push("Vorname fehlt.");
            }
            if (!nachname) {
                teilnehmer.isValid = false;
                teilnehmer.fehler.push("Nachname fehlt.");
            }

            if (geburtsdatumrow instanceof Date) {
                // Wenn Excel es als Datum gespeichert hat
                geburtsdatum = geburtsdatumrow.toISOString().split('T')[0]; // → YYYY-MM-DD
            } else if (typeof geburtsdatumrow === 'string') {
                const parts = geburtsdatumrow.trim().split('.');
                if (parts.length === 3 && parts[2].length === 4) {
                    geburtsdatum = `${parts[0]}-${parts[1]}-${parts[2]}`;
                } else {
                    teilnehmer.fehler.push("Fehler bei Datums Konvertierung.");

                }
            }
            if (geschlecht && !['m', 'w', 'd'].includes(geschlecht)) {
                teilnehmer.isValid = false;
                teilnehmer.fehler.push("Geschlecht ungültig (erlaubt: m, w, d).");
            }


            teilnehmer.validiertesObjekt.Vorname = vorname;
            teilnehmer.validiertesObjekt.Nachname = nachname;
            teilnehmer.validiertesObjekt.Geburtsdatum = geburtsdatum;
            teilnehmer.validiertesObjekt.Verein = verein;
            teilnehmer.validiertesObjekt.Geschlecht = geschlecht;
            
            geparsteTeilnehmer.push(teilnehmer);

            // Zeile zur Vorschau-Tabelle hinzufügen
            const tr = vorschauTabelleBody.insertRow();
            tr.insertCell().textContent = index + 1;
            tr.insertCell().textContent = vorname || '---';
            tr.insertCell().textContent = nachname || '---';
            tr.insertCell().textContent = geburtsdatum || '---';
            tr.insertCell().textContent = verein || '---';
            tr.insertCell().textContent = geschlecht || '---';
            const statusCell = tr.insertCell();
            if (teilnehmer.isValid) {
                statusCell.textContent = 'OK';
                statusCell.style.color = 'green';
            } else {
                statusCell.textContent = 'Fehler';
                statusCell.style.color = 'red';
                statusCell.title = teilnehmer.fehler.join('\n');
                tr.style.backgroundColor = '#ffe0e0';
            }
        });

        vorschauBereich.style.display = 'block';
        const anzahlValide = geparsteTeilnehmer.filter(t => t.isValid).length;
        validierungsInfo.textContent = `Es wurden ${geparsteTeilnehmer.length} Teilnehmerdatensätze gefunden. Davon sind ${anzahlValide} valide.`;
        datenHochladenBtn.disabled = anzahlValide === 0;
    }

    // ----- Daten hochladen -----
    datenHochladenBtn.addEventListener('click', async () => {
        const wettkampfId = wettkampfImportSelect.value;
        if (!wettkampfId) {
            alert("Kein Wettkampf für den Import ausgewählt!");
            return;
        }

        const valideTeilnehmerZumHochladen = geparsteTeilnehmer
            .filter(t => t.isValid)
            .map(t => t.validiertesObjekt);

        if (valideTeilnehmerZumHochladen.length === 0) {
            alert("Keine validen Teilnehmerdaten zum Hochladen vorhanden.");
            return;
        }

        datenHochladenBtn.disabled = true;
        datenHochladenBtn.textContent = 'Lade hoch...';
        importErgebnisBereich.innerHTML = `<p>Daten werden verarbeitet...</p>`;

        const payload = {
            wettkampf_id: wettkampfId,
            teilnehmer: valideTeilnehmerZumHochladen
        };

        const ergebnis = await postData('/teilnehmer/massenimport', payload);

        if (ergebnis) {
            let feedbackHtml = `<h3>Import Ergebnis:</h3>
                               <p>Erfolgreich importiert: ${ergebnis.erfolgreich || 0}</p>
                               <p>Fehlgeschlagen: ${ergebnis.fehlerhaft || 0}</p>`;
            if (ergebnis.fehler_details && ergebnis.fehler_details.length > 0) {
                feedbackHtml += '<h4>Fehlerdetails:</h4><ul>';
                ergebnis.fehler_details.forEach(detail => {
                    feedbackHtml += `<li>Zeile (ca.): ${detail.index + 1} (${detail.name || 'Unbekannt'}) - Grund: ${detail.fehler}</li>`;
                });
                feedbackHtml += '</ul>';
            }
            importErgebnisBereich.innerHTML = feedbackHtml;
            // Optional: Tabelle neu laden oder Status der Zeilen aktualisieren
        } else {
            // Fehler wurde schon im postData angezeigt
            importErgebnisBereich.innerHTML = `<p class="error">Import fehlgeschlagen. Details siehe Konsole oder vorherige Meldung.</p>`;
        }

        datenHochladenBtn.textContent = 'Ausgewählte Teilnehmer zum Wettkampf anmelden';
        // Nicht automatisch re-enablen, Nutzer soll Ergebnis prüfen
        // datenHochladenBtn.disabled = geparsteTeilnehmer.filter(t => t.isValid).length === 0;
    });


    // ----- Event Listener für Dropdowns -----
    wettkampfTagImportSelect.addEventListener('change', (e) => {
        ladeWettkaempfeImport(e.target.value);
        // Reset für Dateiupload und Vorschau
        teilnehmerDateiInput.value = "";
        vorschauBereich.style.display = 'none';
        geparsteTeilnehmer = [];
        datenHochladenBtn.disabled = true;
        importErgebnisBereich.innerHTML = '';
    });
     wettkampfImportSelect.addEventListener('change', (e) => {
        // Reset für Dateiupload und Vorschau, wenn Wettkampf geändert wird
        teilnehmerDateiInput.value = "";
        vorschauBereich.style.display = 'none';
        geparsteTeilnehmer = [];
        datenHochladenBtn.disabled = true;
        importErgebnisBereich.innerHTML = '';
    });

    // ----- Initialisierung -----
    ladeWettkampfTageImport();
});