// ansicht.js
document.addEventListener('DOMContentLoaded', () => {
    console.log("Ansicht JS geladen.");

    // Beispiel-IDs für HTML-Elemente auf der Ansichtsseite
    const wettkampfTagFilterSelect = document.getElementById('wettkampfTagFilterSelect'); // Annahme
    const wettkampfFilterSelect = document.getElementById('wettkampfFilterSelect');     // Annahme
    const ergebnisAnzeigeBereich = document.getElementById('ergebnisAnzeigeBereich'); // Annahme
    const ladeErgebnisseBtn = document.getElementById('ladeErgebnisseBtn');         // Annahme

    async function initAnsichtFilter() {
        if (wettkampfTagFilterSelect) {
            const wettkampftage = await AppUtils.fetchData('/wettkampftage');
            AppUtils.populateSelect(wettkampfTagFilterSelect, wettkampftage, 'idWettkampf_Tag', 'Name', '-- Alle Wettkampftage --');

            wettkampfTagFilterSelect.addEventListener('change', async (e) => {
                if (wettkampfFilterSelect) {
                    if (e.target.value) {
                        const wettkaempfe = await AppUtils.fetchData(`/wettkaempfe?tag_id=${e.target.value}`);
                        AppUtils.populateSelect(wettkampfFilterSelect, wettkaempfe, 'idWettkampf', 'Name', '-- Alle Wettkämpfe --');
                    } else {
                        AppUtils.populateSelect(wettkampfFilterSelect, [], 'idWettkampf', 'Name', '-- Alle Wettkämpfe --');
                    }
                    wettkampfFilterSelect.disabled = !e.target.value;
                }
            });
        }
        if (wettkampfFilterSelect) {
             AppUtils.populateSelect(wettkampfFilterSelect, [], 'idWettkampf', 'Name', '-- Alle Wettkämpfe --');
             wettkampfFilterSelect.disabled = true;
        }
    }

    async function ladeUndZeigeErgebnisse() {
        if (!ergebnisAnzeigeBereich) return;

        const wettkampfId = wettkampfFilterSelect ? wettkampfFilterSelect.value : null;
        let endpoint = '/gesamtergebnisse_ansicht?'; 
        if (wettkampfId) {
            endpoint += `wettkampf_id=${wettkampfId}`;
        } else {
            // Lade alle oder zeige Meldung
            ergebnisAnzeigeBereich.innerHTML = '<p>Bitte Filter auswählen, um Ergebnisse zu laden.</p>';
            return;
        }

        AppUtils.showGlobalNotification('Lade Ergebnisse...', 'info', 2000);
        const ergebnisse = await AppUtils.fetchData(endpoint);

        if (ergebnisse && ergebnisse.length > 0) {
            let html = '<table class="rangliste-tabelle"><thead><tr><th>Platz</th><th>Name</th><th>Verein</th><th>GesamtScore</th><th>Wettkampf</th></tr></thead><tbody>';
            // Annahme: Ergebnisse sind sortiert und haben eine 'Platz'-Eigenschaft vom Backend
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
        } else if (ergebnisse) { // leeres Array
            ergebnisAnzeigeBereich.innerHTML = '<p>Keine Ergebnisse für die aktuelle Auswahl gefunden.</p>';
        } else { // Fehler beim Laden
            ergebnisAnzeigeBereich.innerHTML = '<p class="error-message">Ergebnisse konnten nicht geladen werden.</p>';
        }
    }

    if(ladeErgebnisseBtn) {
        ladeErgebnisseBtn.addEventListener('click', ladeUndZeigeErgebnisse);
    }

    // Initialisierung für die Ansichtsseite
    initAnsichtFilter();

});