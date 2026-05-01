import os
import mysql.connector
from flask import Flask, jsonify, request, render_template, send_file, send_from_directory, redirect, url_for, flash, session
from mysql.connector import pooling
from datetime import datetime
import pandas as pd
import pymysql.cursors
import bcrypt # Direkte Verwendung von bcrypt
from functools import wraps # Für Decorator-Basierte Zugriffskontrolle

# import openpyxl # Nicht direkt verwendet, kann entfernt werden, wenn nicht für andere Zwecke benötigt
# import xlsxwriter # Nicht direkt verwendet, kann entfernt werden, wenn nicht für andere Zwecke benötigt

##############################################################
# ---  Hier beginnt der Code für Grundlegende Funktionen --- #
##############################################################

app = Flask(__name__)

dbconfig = {
    "host": os.getenv('DB_HOST', 'db'),
    "user": os.getenv('DB_USER', 'pythonUser'),
    "password": os.getenv('DB_PASSWORD', ''),
    "database": os.getenv('DB_NAME', 'wettkampfDB')
}

app.config['SECRET_KEY'] = 'G5TdDKm110yk6SGxgAsy7TL35NvqXsy6UhFRfDjKxHymGHCbwOwyQg2kYIwyW9o0NFVp1WfyfYUkOF1KQyt0EB9BiEdPtpc4jvvT' # ERSETZE DIES DURCH EINEN LANGEN, ZUFÄLLIGEN STRING!

connection_pool = pooling.MySQLConnectionPool(
    pool_name="mypool",
    pool_size=10,           # Anzahl gleichzeitig offener Verbindungen
    pool_reset_session=True,
    **dbconfig
)

def get_db_connection():
    return connection_pool.get_connection()

def lade_gesamt_ergebnisse_df(tag_id):
    conn = get_db_connection()
    query = """
        SELECT
            w.Name AS WettkampfName,
            RANK() OVER (PARTITION BY ge.Wettkampf_idWettkampf ORDER BY ge.GesamtScore DESC) AS Platz,
            p.Vorname,
            p.Nachname,
            p.Verein,
            ge.GesamtScore
        FROM Gesamt_Ergebnisse ge
        JOIN Personen p ON ge.Personen_idPersonen = p.idPersonen
        JOIN Wettkampf w ON ge.Wettkampf_idWettkampf = w.idWettkampf
        WHERE w.Wettkampf_Tag_idWettkampf_Tag = %s
        ORDER BY w.Name, Platz;
    """
    try:
        df = pd.read_sql(query, conn, params=(tag_id,))
    finally:
        if conn:
            conn.close()
    return df

def lade_gesamt_ergebnisse_wettkampf(wettkampf_id):
    conn = get_db_connection()
    query = """
        SELECT
            w.Name AS WettkampfName,
            RANK() OVER (ORDER BY ge.GesamtScore DESC) AS Platz,
            p.Vorname,
            p.Nachname,
            p.Verein,
            ge.GesamtScore
        FROM Gesamt_Ergebnisse ge
        JOIN Personen p ON ge.Personen_idPersonen = p.idPersonen
        JOIN Wettkampf w ON ge.Wettkampf_idWettkampf = w.idWettkampf
        WHERE w.idWettkampf = %s
        ORDER BY Platz;
    """
    try:
        df = pd.read_sql(query, conn, params=(wettkampf_id,))
    finally:
        conn.close()
    return df

@app.route('/get_user_status', methods=['GET'])
def get_user_status():
    """
    Stellt den Anmeldestatus und Benutzerinformationen als JSON bereit.
    """
    if 'user_id' in session:
        return jsonify({
            'logged_in': True,
            'username': session.get('username'),
            'role': session.get('role')
        })
    else:
        return jsonify({
            'logged_in': False
        })
##############################################
# ---  Hier beginnt der Code für das Login --- #   
##############################################

# --- Hilfs-Decorators für Zugriffskontrolle ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Bitte melden Sie sich an, um auf diese Seite zuzugreifen.', 'warning')
            return redirect(url_for('wettkampfManager'))
        return f(*args, **kwargs)
    return decorated_function

def role_required(required_roles): # <-- Parameter ist jetzt eine Liste von Rollen
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash('Bitte melden Sie sich an, um auf diese Seite zuzugreifen.', 'warning')
                return redirect(url_for('login'))
            
            user_role = session.get('role') 

            # Prüfe, ob die Rolle des Benutzers in der Liste der erforderlichen Rollen ist
            if user_role not in required_roles: # <-- WICHTIGE ÄNDERUNG HIER!
                flash(f'Sie haben nicht die erforderliche Berechtigung für diese Seite.', 'danger')
                return redirect(url_for('wettkampfManager')) # Umleiten zu einer Standardseite nach Fehler
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Route zum VERARBEITEN der Registrierungs-Daten (POST-Anfrage)
@app.route('/registerCheck', methods=['POST'])
def registerCheck(): # Endpoint-Name: 'registerCheck'
    # ***************************************************************
    # HIER IST DIE WICHTIGSTE ÄNDERUNG, UM JSON-DATEN ZU EMPFANGEN
    # ***************************************************************
    if request.is_json:
        data = request.get_json()
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        confirm_password = data.get('confirm_password')
    else:
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

    if not username or not email or not password or not confirm_password:
        return jsonify(message='Bitte füllen Sie alle Felder aus.', category='danger'), 400

    if password != confirm_password:
        return jsonify(message='Passwörter stimmen nicht überein.', category='danger'), 400

    conn = get_db_connection()
    if not conn:
        return jsonify(message='Datenbankverbindung fehlgeschlagen.', category='danger'), 500

    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id FROM user WHERE username = %s OR email = %s", (username, email))
            existing_user = cursor.fetchone()

            if existing_user:
                return jsonify(message='Benutzername oder E-Mail ist bereits vergeben.', category='danger'), 409 # 409 Conflict

            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            default_role = 'user' 
            cursor.execute("INSERT INTO user (username, email, password, role) VALUES (%s, %s, %s, %s)",
                           (username, email, hashed_password, default_role))
            conn.commit()
            
            # Bei Erfolg direkt umleiten lassen
            return redirect(url_for('login'), code=302)
            
    except Exception as e:
        if conn: # Nur rollback, wenn Verbindung existiert
            conn.rollback()
        print(f"Registrierungsfehler: {e}") # Zum Debuggen auf dem Server
        return jsonify(message=f'Ein Fehler ist aufgetreten: {e}', category='danger'), 500
    finally:
        if conn:
            conn.close()

# Route zum VERARBEITEN der Login-Daten (POST-Anfrage)
@app.route('/loginCheck', methods=['POST'])
def loginCheck(): # Endpoint-Name: 'loginCheck'
    # ***************************************************************
    # HIER IST DIE WICHTIGSTE ÄNDERUNG, UM JSON-DATEN ZU EMPFANGEN
    # ***************************************************************
    if request.is_json: # Prüfen, ob die Anfrage JSON ist
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
    else: # Fallback für traditionelle Formular-Einsendungen (wenn du das Formular später wieder ohne JS senden möchtest)
        username = request.form.get('username')
        password = request.form.get('password')
    
    # Standard-Fehlermeldungen und Rückgabewerte für JSON-Anfragen anpassen
    # Statt redirect senden wir jetzt JSON-Antworten
    # Die Umleitung wird vom Client-JS-Code gehandhabt

    if not username or not password:
        return jsonify(message='Bitte geben Sie Benutzername und Passwort ein.', category='danger'), 400

    conn = get_db_connection()
    if not conn:
        return jsonify(message='Datenbankverbindung fehlgeschlagen.', category='danger'), 500

    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, username, password, role FROM user WHERE username = %s", (username,))
            user = cursor.fetchone()
            has = user[3].encode('utf-8') if user else None # Passwort-Hash aus der DB
            if user and bcrypt.checkpw(password.encode('utf-8'), user[2].encode('utf-8')):
                session['user_id'] = user[0]
                session['username'] = user[1]
                session['role'] = user[3]
                
                # Bei Erfolg direkt umleiten lassen (Flash-Nachricht geht dann verloren, außer du hast einen speziellen Weg)
                # Für JS-Clients ist es üblicher, eine Erfolgsmeldung und den Redirect-Pfad zu senden
                return redirect(url_for('wettkampfManager'), code=302) # Flask sendet dann 302 an den JS-Client
                
            else:
                return jsonify(message='Ungültiger Benutzername oder Passwort.', category='danger'), 401
    except Exception as e:
        print(f"Login-Fehler: {e}") # Zum Debuggen auf dem Server
        return jsonify(message=f'Ein Fehler ist aufgetreten: {e}', category='danger'), 500
    finally:
        if conn:
            conn.close()

# --- Logout-Route ---
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    session.pop('role', None) # Rolle auch aus der Session entfernen
    flash('Sie wurden abgemeldet.', 'info')
    return redirect(url_for('wettkampfManager'))

##############################################################
# ---  Hier beginnt der Code für die Websiten erstellung --- #
##############################################################


# --- HTML-Seiten ---
@app.route('/', methods=['GET'])
def inizial():
    return render_template('wettkampfManager.html')

@app.route('/wettkampfManager', methods=['GET'])
def wettkampfManager():
    return render_template('wettkampfManager.html')

@app.route('/wettkampfManagerAdmincenter', methods=['GET'])
@role_required('admin')
def wettkampfManagerAdmincenter():
    conn = get_db_connection()
    users = []
    if conn:
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT id, username, email, role FROM user ORDER BY username")
                users = cursor.fetchall()
        except Exception as e:
            flash(f'Fehler beim Laden der Benutzer: {e}', 'danger')
        finally:
            conn.close()
    return render_template('wettkampfManagerAdmincenter.html')

@app.route('/wettkampfAnsicht', methods=['GET'])
def wettkampfAnsicht():
    return render_template('wettkampfAnsicht.html')

@app.route('/wettkampfDateneingabe', methods=['GET'])
@role_required(['kampfrichter', 'admin'])
def wettkampfDateneingabe():
    return render_template('wettkampfDateneingabe.html')

@app.route('/wettkampfMassenImport', methods=['GET'])
@role_required(['kampfrichter', 'admin', 'user']) 
def wettkampfMassenImport():
    return render_template('wettkampfMassenImport.html')

@app.route('/login', methods=['GET'])
def wettkampfLogin():
    return render_template('wettkampfLogin.html')

@app.route('/register', methods=['GET'])
def wettkampfRegister():
    return render_template('wettkampfRegister.html')

# --- CSS-Seiten ---

@app.route('/css/wettkampfManager', methods=['GET'])
def wettkampfManagerCSS():
    return app.send_static_file('css/wettkampfManager.css')

@app.route('/css/wettkampfAnsicht', methods=['GET'])
def wettkampfAnsichtCSS():
    return app.send_static_file('css/wettkampfAnsicht.css')

@app.route('/css/wettkampfDateneingabe', methods=['GET'])
def wettkampfDateneingabeCSS():
    return app.send_static_file('css/wettkampfDateneingabe.css')

@app.route('/css/wettkampfManagerAdmincenter', methods=['GET'])
def wettkampfManagerAdmincenterCSS():
    return app.send_static_file('css/wettkampfManagerAdmincenter.css')

@app.route('/css/wettkampfManagerStyle', methods=['GET'])
def wettkampfManagerStyleCSS():
    return app.send_static_file('css/wettkampfManagerStyle.css')

@app.route('/css/wettkampfMassenImport', methods=['GET'])
def wettkampfMassenImportCSS():
    return app.send_static_file('css/wettkampfMassenImport.css')

# --- JS-Seiten ---

@app.route('/js/wettkampfManager', methods=['GET'])
def wettkampfManagerJS():
    return app.send_static_file('js/wettkampfManager.js')

@app.route('/js/wettkampfAnsicht', methods=['GET'])
def wettkampfAnsichtJS():
    return app.send_static_file('js/wettkampfAnsicht.js')

@app.route('/js/wettkampfDateneingabe', methods=['GET'])
def wettkampfDateneingabeJS():
    return app.send_static_file('js/wettkampfDateneingabe.js')

@app.route('/js/wettkampfManagerAdmincenter', methods=['GET'])
def wettkampfManagerAdmincenterJS():
    return app.send_static_file('js/wettkampfManagerAdmincenter.js')

@app.route('/js/wettkampfManagerJS', methods=['GET'])
def wettkampfManagerJSJS():
    return app.send_static_file('js/wettkampfManagerJS.js')

@app.route('/js/wettkampfMassenImport', methods=['GET'])
def wettkampfMassenImportJS():
    return app.send_static_file('js/wettkampfMassenImport.js')

# --- Media ---

@app.route('/media/excel_Vorlage', methods=['GET'])
def send_media():
 return app.send_static_file('media/excel_Vorlage.xlsx')


##############################################
# ---  Hier beginnt der Code für die API --- #
##############################################

# NEUER ENDPOINT: Gibt die Benutzerliste als JSON zurück
@app.route('/get_users_for_admin', methods=['GET'])
@role_required(['admin']) # Auch dieser Endpoint muss geschützt sein!
def get_users_for_admin():
    conn = get_db_connection()
    if not conn:
        return jsonify(message='Datenbankverbindung fehlgeschlagen.', category='danger'), 500

    users_list = []
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor: # Stelle sicher, dass DictCursor verwendet wird!
            cursor.execute("SELECT id, username, email, role FROM user")
            users_raw = cursor.fetchall()
            for user in users_raw:
                users_list.append({
                    'id': user[0],
                    'username': user[1],
                    'email': user[2],
                    'role': user[3]
                })
        return jsonify(users=users_list), 200
    except Exception as e:
        print(f"Fehler beim Abrufen der Benutzerliste: {e}")
        return jsonify(message=f'Ein Fehler ist aufgetreten: {e}', category='danger'), 500
    finally:
        if conn:
            conn.close()
            
@app.route('/admin_manage_roles', methods=['POST'])            
@role_required(['admin']) # Nur Admins dürfen Rollen ändern
def admin_manage_roles():
    if not request.is_json:
        return jsonify(message='Ungültige Anfrage.', category='danger'), 400

    data = request.get_json()
    user_id = data.get('user_id')
    new_role = data.get('new_role')

    if not user_id or not new_role:
        return jsonify(message='Fehlende Daten für Rollenänderung.', category='danger'), 400

    # Optional: Überprüfe, ob die Rolle gültig ist (user, kampfrichter, admin)
    if new_role not in ['user', 'kampfrichter', 'admin']:
        return jsonify(message='Ungültige Rollenzuweisung.', category='danger'), 400

    conn = get_db_connection()
    if not conn:
        return jsonify(message='Datenbankverbindung fehlgeschlagen.', category='danger'), 500

    try:
        with conn.cursor() as cursor:
            cursor.execute("UPDATE user SET role = %s WHERE id = %s", (new_role, user_id))
            conn.commit()
        return jsonify(message=f'Rolle für Benutzer {user_id} erfolgreich aktualisiert.', category='success'), 200
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Fehler bei Rollenänderung: {e}")
        return jsonify(message=f'Fehler beim Aktualisieren der Rolle: {e}', category='danger'), 500
    finally:
        if conn:
            conn.close()

@app.route('/admin_delete_user', methods=['POST']) # Oder DELETE
@role_required(['admin']) # Nur Admins dürfen löschen
def admin_delete_user():
    if not request.is_json:
        return jsonify(message='Ungültige Anfrage.', category='danger'), 400

    data = request.get_json()
    user_id = data.get('user_id')

    if not user_id:
        return jsonify(message='Keine Benutzer-ID zum Löschen angegeben.', category='danger'), 400

    # Optional: Verhindere, dass Admins sich selbst löschen können
    if str(user_id) == str(session.get('user_id')):
        return jsonify(message='Sie können Ihr eigenes Konto nicht löschen.', category='danger'), 403

    conn = get_db_connection()
    if not conn:
        return jsonify(message='Datenbankverbindung fehlgeschlagen.', category='danger'), 500

    try:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM user WHERE id = %s", (user_id,))
            conn.commit()
        return jsonify(message=f'Benutzer {user_id} erfolgreich gelöscht.', category='success'), 200
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Fehler beim Löschen des Benutzers: {e}")
        return jsonify(message=f'Fehler beim Löschen des Benutzers: {e}', category='danger'), 500
    finally:
        if conn:
            conn.close()
            
@app.route('/api/wettkampftage', methods=['GET'])
def get_wettkampftage():
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT idWettkampf_Tag, Name, Wettkampf_Datum FROM Wettkampf_Tag ORDER BY Wettkampf_Datum DESC")
        result = cursor.fetchall()
        return jsonify(result)
    except mysql.connector.Error as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/api/wettkaempfe', methods=['GET'])
def get_wettkaempfe():
    tag_id = request.args.get('tag_id')
    try:
        tag_id = int(tag_id)
    except (ValueError, TypeError):
        return jsonify({"error": "Ungültige tag_id"}), 400

    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT idWettkampf, Wettkampf_Nr, Name, Altersklasse
            FROM Wettkampf
            WHERE Wettkampf_Tag_idWettkampf_Tag = %s
            ORDER BY Name
            """,
            (tag_id,)
        )
        result = cursor.fetchall()
        return jsonify(result)
    except mysql.connector.Error as err:
        return jsonify({"error": "DB Fehler", "details": str(err)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/api/geraete_fuer_wettkampf', methods=['GET'])
def get_geraete_fuer_wettkampf():
    wettkampf_id = request.args.get('wettkampf_id')
    if not wettkampf_id:
        return jsonify({"error": "wettkampf_id fehlt"}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "DB-Verbindung fehlgeschlagen"}), 500

    try:
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT g.idGeraete, g.Name, g.Anzahl_Var, g.Berechnung_Variante, ghw.idGeraete_Wettkampf, ghw.Anzahl_Durchfuehrungen
            FROM Geraete g
            JOIN Geraete_has_Wettkampf ghw ON g.idGeraete = ghw.Geraete_idGeraete
            WHERE ghw.Wettkampf_idWettkampf = %s
            ORDER BY g.Name
        """
        cursor.execute(query, (wettkampf_id,))
        result = cursor.fetchall()
        return jsonify(result)
    finally:
        cursor.close()
        conn.close()

@app.route('/api/teilnehmer_fuer_eingabe', methods=['GET'])
def get_teilnehmer_fuer_eingabe():
    wettkampf_id_str = request.args.get('wettkampf_id')
    geraet_id_str = request.args.get('geraet_id') # Das ist die ID des Geräts selbst
    filter_typ = request.args.get('filter_typ')
    filter_wert = request.args.get('filter_wert')

    if not wettkampf_id_str or not geraet_id_str:
        return jsonify({"error": "wettkampf_id und geraet_id sind erforderlich"}), 400
    try:
        wettkampf_id = int(wettkampf_id_str)
        geraet_id = int(geraet_id_str) # Die ID des ausgewählten Geräts
    except ValueError:
        return jsonify({"error": "Ungültige wettkampf_id oder geraet_id"}), 400

    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Bestimme idGeraete_Wettkampf für die gegebene Kombination
        cursor.execute("""
            SELECT idGeraete_Wettkampf 
            FROM Geraete_has_Wettkampf 
            WHERE Wettkampf_idWettkampf = %s AND Geraete_idGeraete = %s
        """, (wettkampf_id, geraet_id))
        ghw_row = cursor.fetchone()
        
        if not ghw_row:
            # Keine Zuordnung für dieses Gerät in diesem Wettkampf gefunden
            return jsonify([]) 
        
        id_geraete_wettkampf_fuer_filter = ghw_row['idGeraete_Wettkampf']
        
        # Hauptquery für Teilnehmer
        # Wir brauchen p.idPersonen, Vorname, Nachname, Verein, Riege
        # und die idGeraete_Wettkampf, die für diese Person+Gerät+Wettkampf Kombination gilt.
        # Da wir nach geraet_id filtern, ist id_geraete_wettkampf_fuer_filter die relevante.
        query_params = [wettkampf_id] # Für WHERE phw.Wettkampf_idWettkampf

        base_query = """
            SELECT 
                p.idPersonen, p.Vorname, p.Nachname, p.Verein, phw.Riege
            FROM Personen p
            JOIN Personen_has_Wettkampf phw ON p.idPersonen = phw.Personen_idPersonen
            WHERE phw.Wettkampf_idWettkampf = %s
        """
        # Filter anwenden
        if filter_typ == 'riege' and filter_wert:
            base_query += " AND phw.Riege = %s"
            query_params.append(filter_wert)
        elif filter_typ == 'person' and filter_wert:
            base_query += " AND (p.Vorname LIKE %s OR p.Nachname LIKE %s OR CAST(p.idPersonen AS CHAR) = %s)"
            like_wert = f"%{filter_wert}%"
            query_params.extend([like_wert, like_wert, filter_wert])

        base_query += " ORDER BY phw.Riege, p.Nachname, p.Vorname"
        
        cursor.execute(base_query, tuple(query_params))
        teilnehmer_roh = cursor.fetchall()

        result = []
        for p_roh in teilnehmer_roh:
            result.append({
                "id": p_roh['idPersonen'],
                "vorname": p_roh['Vorname'],
                "nachname": p_roh['Nachname'],
                "verein": p_roh['Verein'],
                "riege": p_roh['Riege'],
                "geraete_id": geraet_id, # Die ID des ausgewählten Geräts mitsenden
                "geraete_wettkampf_id": id_geraete_wettkampf_fuer_filter # Die ID der Zuordnung G-WK
                # Das Feld "ergebnis_erfasst" wird im JS über die einzelErgebnisse-Liste bestimmt.
            })
        return jsonify(result)

    except mysql.connector.Error as err:
        return jsonify({"error": "Datenbankfehler", "details": str(err)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()


@app.route('/api/einzelwertung_speichern', methods=['POST'])
def einzelwertung_speichern():
    data = request.json

    # 1. Daten aus dem Request validieren
    required_fields = ['personen_id', 'geraete_wettkampf_id', 'versuch_nr']
    missing_fields = [f for f in required_fields if f not in data]
    if missing_fields:
        return jsonify({"message": f"Fehlende Felder: {', '.join(missing_fields)}"}), 400

    personen_id = data['personen_id']
    geraete_wettkampf_id = data['geraete_wettkampf_id']
    versuch_nr = data['versuch_nr']
    
    # Dynamisch alle 'varX'-Felder aus dem Request sammeln
    vars_dict = {key: data[key] for key in data if key.startswith('var') and data[key] is not None}
    
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # NEUE LOGIK: Prüfen, ob bereits ein Eintrag existiert
        # -------------------------------------------------------------
        # Wir suchen nach einem Eintrag mit der gleichen Kombination aus Person, Wettkampf-Gerät und Versuch.
        cursor.execute("""
            SELECT idEinzel_Ergebnis 
            FROM Einzel_Ergebnis
            WHERE Personen_idPersonen = %s 
              AND Geraete_Wettkampf_idGeraete_Wettkampf = %s
              AND Versuch_Nr = %s
        """, (personen_id, geraete_wettkampf_id, versuch_nr))
        
        existing_record = cursor.fetchone()
        id_einzel_ergebnis = existing_record[0] if existing_record else None
        # -------------------------------------------------------------

        # Anzahl der erwarteten Variablen aus der DB holen (für Sicherheit und dynamische Query)
        cursor.execute("""
            SELECT g.Anzahl_Var 
            FROM Geraete g
            JOIN Geraete_has_Wettkampf ghw ON g.idGeraete = ghw.Geraete_idGeraete
            WHERE ghw.idGeraete_Wettkampf = %s
        """, (geraete_wettkampf_id,))
        geraet_info = cursor.fetchone()
        
        if not geraet_info:
            return jsonify({"message": "Geräteinformation nicht gefunden."}), 404
        
        anzahl_var_db = geraet_info[0]

        # 2. Query-Teile dynamisch zusammenbauen
        var_cols = []
        var_placeholders = []
        var_values_for_query = []

        for i in range(1, anzahl_var_db + 1):
            var_name = f'Var{i}'
            var_cols.append(var_name)
            var_placeholders.append("%s")
            # Wert aus dem Request nehmen oder NULL, falls nicht vorhanden
            var_values_for_query.append(vars_dict.get(var_name.lower())) # .lower() für Konsistenz mit JS `varX`

        # 3. Entscheiden: UPDATE oder INSERT?
        if id_einzel_ergebnis:  # Ein Eintrag existiert -> UPDATE
            set_clause = ", ".join([f"{col} = %s" for col in var_cols])
            
            query = f"""
                UPDATE Einzel_Ergebnis 
                SET {set_clause}
                WHERE idEinzel_Ergebnis = %s
            """
            # Parameterliste für UPDATE: Erst die Var-Werte, dann die ID für die WHERE-Klausel
            params = var_values_for_query + [id_einzel_ergebnis]
            operation = "aktualisiert"

        else:  # Kein Eintrag existiert -> INSERT
            cols_for_insert = ", ".join(["Personen_idPersonen", "Geraete_Wettkampf_idGeraete_Wettkampf", "Versuch_Nr"] + var_cols)
            placeholders_for_insert = ", ".join(["%s", "%s", "%s"] + var_placeholders)
            
            query = f"""
                INSERT INTO Einzel_Ergebnis ({cols_for_insert})
                VALUES ({placeholders_for_insert})
            """
            # Parameterliste für INSERT: Erst die IDs/Versuch, dann die Var-Werte
            params = [personen_id, geraete_wettkampf_id, versuch_nr] + var_values_for_query
            operation = "gespeichert"
        
        # 4. Query ausführen und abschließen
        cursor.execute(query, tuple(params))
        conn.commit()
        return jsonify({"message": f"Wertung erfolgreich {operation}."}), 200

    except mysql.connector.Error as err:
        if conn: conn.rollback()
        return jsonify({"message": "Datenbankfehler beim Speichern der Wertung.", "details": str(err)}), 500
    except Exception as e:
        if conn: conn.rollback()
        return jsonify({"message": "Allgemeiner Fehler beim Speichern der Wertung.", "details": str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()


@app.route('/api/einzelwertung_loeschen', methods=['POST'])
def einzelwertung_loeschen():
    data = request.json

    # Die neuen, benötigten Felder aus dem Request holen und validieren
    required_fields = ['personen_id', 'geraete_wettkampf_id', 'versuch_nr']
    missing_fields = [f for f in required_fields if f not in data]
    if missing_fields:
        return jsonify({"message": f"Fehlende Felder für den Löschvorgang: {', '.join(missing_fields)}", "success": False}), 400

    personen_id = data.get('personen_id')
    geraete_wettkampf_id = data.get('geraete_wettkampf_id')
    versuch_nr = data.get('versuch_nr')

    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Den DELETE-Befehl an die neue WHERE-Klausel anpassen
        query = """
            DELETE FROM Einzel_Ergebnis 
            WHERE Personen_idPersonen = %s 
              AND Geraete_Wettkampf_idGeraete_Wettkampf = %s
              AND Versuch_Nr = %s
        """
        params = (personen_id, geraete_wettkampf_id, versuch_nr)
        
        cursor.execute(query, params)
        conn.commit()

        # cursor.rowcount gibt die Anzahl der gelöschten Zeilen zurück.
        # Wenn > 0, war der Löschvorgang erfolgreich.
        if cursor.rowcount > 0:
            return jsonify({"message": f"Versuch Nr. {versuch_nr} erfolgreich gelöscht.", "success": True}), 200
        else:
            # Dies passiert, wenn kein Eintrag mit den Kriterien gefunden wurde
            return jsonify({"message": "Kein Eintrag zum Löschen gefunden. Der Versuch existierte nicht.", "success": False}), 404
            
    except mysql.connector.Error as err:
        if conn: conn.rollback()
        return jsonify({"message": "Datenbankfehler beim Löschen.", "details": str(err), "success": False}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@app.route('/api/einzel_ergebnisse', methods=['GET'])
def get_einzel_ergebnisse():
    person_id = request.args.get('person_id')
    geraete_wk_id = request.args.get('geraete_wk_id')

    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "DB-Verbindung fehlgeschlagen"}), 500

    try:
        cursor = conn.cursor(dictionary=True)

        sql = """
            SELECT
                idEinzel_Ergebnis,
                Geraete_Wettkampf_idGeraete_Wettkampf,
                Personen_idPersonen,
                Versuch_Nr,
                Score,
                Var1, Var2, Var3, Var4, Var5,
                Var6, Var7, Var8, Var9, Var10
            FROM Einzel_Ergebnis
        """

        conditions = []
        values = []

        if person_id:
            conditions.append("Personen_idPersonen = %s")
            values.append(person_id)
        if geraete_wk_id:
            conditions.append("Geraete_Wettkampf_idGeraete_Wettkampf = %s")
            values.append(geraete_wk_id)

        if conditions:
            sql += " WHERE " + " AND ".join(conditions)

        sql += " ORDER BY Personen_idPersonen, Versuch_Nr"

        cursor.execute(sql, values)
        result = cursor.fetchall()
        return jsonify(result)

    finally:
        cursor.close()
        conn.close()


# --- Restliche Endpunkte (Excel, Massenimport etc. vorerst unverändert) ---
@app.route('/api/gesamtergebnisse_ansicht_Tag', methods=['GET'])
def gesamtergebnisse_ansicht_Tag():
    tag_id = request.args.get('tag_id')
    if not tag_id:
        return jsonify({"error": "tag_id fehlt"}), 400
    try:
        df = lade_gesamt_ergebnisse_df(tag_id)
        result = df.to_dict(orient='records')
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/api/gesamtergebnisse_ansicht', methods=['GET'])
def gesamtergebnisse_ansicht():
    wettkampf_id = request.args.get('wettkampf_id')
    if not wettkampf_id:
        return jsonify({"error": "wettkampf_id fehlt"}), 400 # JS erwartet leeres Array bei fehlender Auswahl

    try:
        df = lade_gesamt_ergebnisse_wettkampf(wettkampf_id)
        result = df.to_dict(orient='records')
        return jsonify(result)
    except Exception as e:
        return jsonify(None), 500  # JS erkennt Fehler durch `ergebnisse == null`

@app.route('/api/erzeuge_excel', methods=['GET'])
def erzeuge_excel():
    tag_id = request.args.get('tag_id')
    if not tag_id:
        return jsonify({"error": "tag_id fehlt"}), 400
    try:
        df = lade_gesamt_ergebnisse_df(tag_id)
        # Sicherstellen, dass der media-Ordner im static-Ordner existiert
        media_dir = os.path.join(app.static_folder, "media")
        os.makedirs(media_dir, exist_ok=True)

        filename = f"GesamtErgebnisse_Tag_{tag_id}.xlsx"
        filepath = os.path.join(media_dir, filename)

        df.to_excel(filepath, index=False, sheet_name='GesamtErgebnisse')
        return jsonify({"message": "Datei erfolgreich erstellt", "filename": filename})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/download_excel', methods=['GET'])
def download_excel():
    filename = request.args.get('filename')
    if not filename:
        return jsonify({"error": "Dateiname fehlt"}), 400
    
    # Dateipfad relativ zum 'static/media'-Ordner
    filepath = os.path.join(app.static_folder, "media", filename)

    if not os.path.exists(filepath):
        return jsonify({"error": "Datei nicht gefunden"}), 404
    
    return send_file(filepath,
                     as_attachment=True,
                     download_name=filename, # Name, unter dem die Datei beim Client gespeichert wird
                     mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

@app.route('/api/teilnehmer/massenimport', methods=['POST'])
def massenimport_teilnehmer():
    data = request.get_json()
    wettkampf_id_str = data.get('wettkampf_id')
    teilnehmer_liste = data.get('teilnehmer')

    if not wettkampf_id_str or not teilnehmer_liste:
        return jsonify({"error": "wettkampf_id und teilnehmer-Liste sind erforderlich"}), 400
    try:
        wettkampf_id = int(wettkampf_id_str)
    except ValueError:
         return jsonify({"error": "Ungültige wettkampf_id"}), 400


    conn = None
    cursor = None
    erfolgreich_importiert = 0
    fehlerhaft = 0
    fehler_details = []

    try:
        conn = get_db_connection()
        
        for index, tn_daten in enumerate(teilnehmer_liste):
            cursor = conn.cursor() # Cursor innerhalb der Schleife für bessere Fehlerbehandlung pro Eintrag
            conn.start_transaction()
            try:
                vorname = tn_daten.get('Vorname', '').strip()
                nachname = tn_daten.get('Nachname', '').strip()
                if not vorname or not nachname:
                    fehlerhaft += 1
                    fehler_details.append({"index": index, "name": f"{vorname} {nachname}", "fehler": "Vorname oder Nachname fehlt."})
                    conn.rollback() # Rollback für diesen TN
                    if cursor: cursor.close()
                    continue

                geburtsdatum_str = tn_daten.get('Geburtsdatum')
                try:
                    # Versuche verschiedene Datumsformate zu parsen
                    if isinstance(geburtsdatum_str, int): # Falls Excel-Datum als Zahl kommt
                         # Excel-Datum (Zahl) in Python-Datum umwandeln
                         # Diese Umwandlung (von Excel-Serial-Datum) ist oft komplexer.
                         # pd.to_datetime(geburtsdatum_str, unit='D', origin='1899-12-30') wäre eine Option mit Pandas.
                         # Hier vereinfacht für reine String-Eingabe:
                         raise ValueError("Integer-Datum nicht direkt unterstützt, bitte als TT-MM-JJJJ oder JJJJ-MM-TT.")
                    
                    dt_obj = None
                    for fmt in ("%d.%m.%Y", "%d-%m-%Y", "%Y-%m-%d"):
                        try:
                            dt_obj = datetime.strptime(str(geburtsdatum_str), fmt)
                            break
                        except ValueError:
                            continue
                    if dt_obj is None:
                         raise ValueError("Ungültiges Datumsformat")
                    
                    geburtsdatum_db = dt_obj.strftime("%Y-%m-%d")

                except ValueError as ve:
                    fehlerhaft += 1
                    fehler_details.append({"index": index, "name": f"{vorname} {nachname}", "fehler": f"Geburtsdatum ungültig: {ve}"})
                    conn.rollback()
                    if cursor: cursor.close()
                    continue
                
                verein = tn_daten.get('Verein', None)
                geschlecht = tn_daten.get('Geschlecht', None)
                riege = tn_daten.get('Riege', None)
                if riege is not None:
                    try:
                        riege = int(riege)
                    except ValueError:
                        fehlerhaft +=1
                        fehler_details.append({"index": index, "name": f"{vorname} {nachname}", "fehler": "Riege muss eine Zahl sein."})
                        conn.rollback()
                        if cursor: cursor.close()
                        continue


                cursor.execute("SELECT idPersonen FROM Personen WHERE Vorname = %s AND Nachname = %s AND Geburtsdatum = %s", 
                               (vorname, nachname, geburtsdatum_db))
                result = cursor.fetchone()
                
                if result:
                    personen_id = result[0]
                else:
                    cursor.execute(
                        """
                        INSERT INTO Personen (Vorname, Nachname, Geburtsdatum, Verein, Geschlecht)
                        VALUES (%s, %s, %s, %s, %s)
                        """,
                        (vorname, nachname, geburtsdatum_db, verein, geschlecht)
                    )
                    personen_id = cursor.lastrowid

                # Prüfen, ob Person bereits für diesen Wettkampf gemeldet ist
                cursor.execute(
                    "SELECT * FROM Personen_has_Wettkampf WHERE Personen_idPersonen = %s AND Wettkampf_idWettkampf = %s",
                    (personen_id, wettkampf_id)
                )
                if not cursor.fetchone():
                    cursor.execute(
                        """
                        INSERT INTO Personen_has_Wettkampf (Personen_idPersonen, Wettkampf_idWettkampf, Riege)
                        VALUES (%s, %s, %s)
                        """,
                        (personen_id, wettkampf_id, riege if riege is not None else -1) # -1 als Default für "keine Riege"
                    )
                
                conn.commit()
                erfolgreich_importiert += 1
            
            except mysql.connector.Error as db_err_inner:
                if conn: conn.rollback()
                fehlerhaft += 1
                fehler_details.append({"index": index, "name": f"{tn_daten.get('Vorname')} {tn_daten.get('Nachname')}", "fehler": f"DB Fehler: {db_err_inner}"})
            finally:
                if cursor: cursor.close()

    except mysql.connector.Error as db_err_outer: # Fehler mit der Haupt-Connection
        return jsonify({"error": "Datenbankfehler (äußere Transaktion)", "details": str(db_err_outer)}), 500
    except Exception as e:
        return jsonify({"error": "Allgemeiner Fehler beim Massenimport", "details": str(e)}), 500
    finally:
        if conn: conn.close() # Schließe die Connection, die für die Schleife geholt wurde

    return jsonify({
        "message": "Massenimport abgeschlossen",
        "erfolgreich": erfolgreich_importiert,
        "fehlerhaft": fehlerhaft,
        "fehler_details": fehler_details
    }), 200


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001, use_reloader=False)