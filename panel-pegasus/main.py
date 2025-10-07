from flask import Flask, jsonify, request, render_template, redirect, url_for, session, send_from_directory
from flask_mysqldb import MySQL
from datetime import datetime, timedelta
from flask_login import UserMixin, LoginManager, login_user, logout_user, login_required
import mysql.connector
import random, requests
import hashlib
import os
import cloudinary
import cloudinary.uploader
import cloudinary.api

app = Flask(__name__)

# Configurar la conexión a la base de datos
app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST')
app.config['MYSQL_USER'] = os.getenv('MYSQL_USER')
app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD')
app.config['MYSQL_DB'] = os.getenv('MYSQL_DB')

mysqlProject = MySQL(app)

# Establecer la secret_key
app.secret_key = os.getenv('PEGASUS_AGE')

# Configurar Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)

# Modelo de usuario
class User(UserMixin):
    pass

# Función para cargar un usuario dado su ID
@login_manager.user_loader
def load_user(user_id):
    user = User()
    user.id = user_id
    return user

# Ruta de inicio de sesión
@app.route('/rider_pegasus', methods=['GET', 'POST'])
def validate():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conexion = mysql.connector.connect(
            host = os.getenv('MYSQL_HOST'),
            user = os.getenv('MYSQL_USER'),
            password = os.getenv('MYSQL_PASSWORD'),
            database = os.getenv('MYSQL_DB')
        )

        # Verificar que el usuario y la contraseña sean Admins
        cursor = conexion.cursor(buffered=True)
        query = '''
        SELECT fk_user_id, tipo_suscripcion
        FROM suscripcion
        JOIN usuario ON user_id = fk_user_id
        WHERE username = %s AND password = %s
        '''
        admin = "Admin"
        cursor.execute(query, (username, password))
        user = cursor.fetchone()
        cursor.close()

        if user is not None:
            # Crear un objeto User y llamar a login_user para iniciar sesión
            user_obj = User()
            user_obj.id = user[0]
            user_obj.rol = user[1]

            if admin == user_obj.rol:
                login_user(user_obj)
                return render_template('index.html')
            else:
                return hello()
            #return redirect(url_for('index'))

    return render_template('login.html')

@app.route("/")
def hello():
    message = """
    <style>
    body {
        background-color: black;
        color: white;
        font-family: monospace;
        font-size: 20px;
        text-align: center;
        padding-top: 100px;
    }
    </style>
    <div>
        <h1>API Privada</h1>
        <p>Esta API está protegida. Si necesitas acceso legítimo, contacta con nosotros.</p>
        <pre>
        ********************************************
        *                                          *
        *  Correo: cristiansalda777@gmail.com          *
        *  Teléfono: +123-456-7890                 *
        *  Página web: www.miempresa.com           *
        *                                          *
        ********************************************
        </pre>
        <p>Advertencia: Todas las actividades están bajo vigilancia. Cualquier intento de accesos no autorizados será identificado y desarrollado con las autoridades correspondientes.</p>
    </div>
    """
    return message



@app.route('/login', methods=['POST'])
def login():

    try:

        # Obtener usuario y contraseña desde la solicitud
        username = request.json['username']
        password = request.json['password']

        print('USUARIO:', username, 'establenciendo conexion..')

        # Verificar que el usuario y la contraseña sean correctos
        cursor = mysqlProject.connection.cursor()
        cursor.execute('SELECT * FROM usuario WHERE username = %s AND password = %s', (username, password))
        user = cursor.fetchone()
        cursor.close()

        if user is not None:
            # Obtener los créditos del usuario
            credits = user[4]

            # Obtener token de usuario
            userid = user[0]

            # Obtener hwid de usuario
            global user_hwid
            user_hwid = user[3]

            # Obtener datos de la tabla Token
            cursor = mysqlProject.connection.cursor()
            cursor.execute('SELECT * FROM token WHERE fk_user_id = %s', (userid,))
            token = cursor.fetchone()
            cursor.close()

            if token:
                # Retornar la respuesta de éxito con los créditos del usuario
                response = {
                    'status': 'success',
                    'credits': credits,
                    'token': token[2],
                    'userid': userid,
                    'user_hwid': user_hwid
                }
                return jsonify(response)
        else:
            # Retornar la respuesta de error si el usuario y la contraseña no coinciden
            response = {
                'status': 'error',
                'message': 'Invalid username or password'
            }
            return jsonify(response), 401  # Retorna también el código 401 en caso de error

    except Exception as e:
        print('Error en LOGIN Interfaz', e)

@app.route('/edit', methods=['PUT'])
def edit_user():
    # Obtener los datos del usuario enviados en la solicitud
    username = request.json['username']
    password = request.json['password']
    gate = request.json['gate']

    if gate == 'INFINITY' or gate == 'LEGACY':
        gate_valor = 0
    
    elif gate =='RECHECK':
        gate_valor = 10

    elif gate =='COBRO':
        gate_valor = 1
    
    else:
        gate_valor = 5

    # Crear un cursor para ejecutar consultas SQL
    cursor = mysqlProject.connection.cursor()

    # Consulta para obtener los créditos del usuario
    query = "SELECT creditos FROM usuario WHERE username = %s AND password = %s"
    cursor.execute(query, (username, password))

    # Obtener el resultado de la consulta
    result = cursor.fetchone()

    # Si no se encontró ningún usuario, devolver un mensaje de error
    if not result:
        return jsonify({'error': 'Usuario no encontrado'})

    # Si se encontró el usuario, obtener sus créditos y restar 5
    credits = result[0] - gate_valor

    # Consulta para actualizar los datos del usuario en la base de datos
    query = "UPDATE usuario SET creditos = %s WHERE username = %s AND password = %s"
    cursor.execute(query, (credits, username, password))

    # Confirmar los cambios en la base de datos
    mysqlProject.connection.commit()

    # Devolver una respuesta con los nuevos créditos
    response = {
        'status': 'success',
        'credits': credits
    }
    return jsonify(response)

@app.route('/send', methods=['PUT'])
def send():
    #username = request.json['username']
    fk_user_id = request.json['fk_user_id']
    gate = request.json['gate']
    cc = request.json['cc']
    mes = request.json['mes']
    year = request.json['year']
    ccv = request.json['ccv']
    type = request.json['type']
    bank = request.json['bank']
    data = request.json['data']
    franquicia = request.json['franquicia']
    pais = request.json['pais']
    fecha = request.json['fecha']
    estado = request.json['estado']

    cursor = mysqlProject.connection.cursor()

    query = "INSERT INTO tarjeta (fk_user_id, gate, cc, mes, year, ccv, type, bank, data, franquicia, pais, fecha, estado) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
    values = (fk_user_id, gate, cc, mes, year, ccv, type, bank, data, franquicia, pais, fecha, estado)
    cursor.execute(query, values)
    mysqlProject.connection.commit()

    #msg = f"{username}|{gate}|{tarjeta}|{mes}|{ano}|{cvv}|{banco}"
    #bot_token = '6950735396:AAHjFd9bSxcM1YDFBxtFk1WIKFn8fAOmZOcAAAAAAAAAAAAAAAAAAAAAAA'
    #bot_chatID = '-1001991495157'
    #send_text = 'https://api.telegram.org/bot' + bot_token + '/sendMessage?chat_id=' + bot_chatID + '&parse_mode=Markdown&text=' + msg
    #response = requests.get(send_text)
    return '', 204

from flask import jsonify, request



@app.route('/buscar', methods=['POST'])
def buscar():

    #try:
    #    print('Local HWID:', local_hwid, "Autenticado como: ", user_hwid, "se encuentra BUSCAAANDO..")
    #except Exception as e:
    #    print("FALLO EN buscar", e)

    # Obtener el valor a buscar desde el JSON enviado
    ccData = request.json.get('valor_a_buscar')

    if ccData is not None:

        gate = ccData.split('|')[2]
        cc = ccData.split('|')[3]
        mes = ccData.split('|')[4]
        year = ccData.split('|')[5]

        # Realizar la búsqueda en la base de datos
        cursor = mysqlProject.connection.cursor()

        query = '''
        SELECT cc, mes, year, gate
        FROM tarjeta
        WHERE cc = %s AND mes = %s AND year = %s AND gate = %s
        '''
        cursor.execute(query, (cc, mes, year, gate))
        resultados = cursor.fetchall()

        # Cerrar el cursor
        cursor.close()

        # Comprobar si se encontraron resultados
        if resultados:
            # Convertir los resultados a un formato JSON y retornarlos
            return jsonify({"mensaje": "Verdadero"})
        else:
            # Si no se encontraron resultados, retornar un mensaje apropiado
            return jsonify({"mensaje": "Positivo"}), 404
    else:
        # Si no se proporcionó un valor para buscar, retornar un mensaje de error
        return jsonify({"mensaje": "Se requiere un valor para buscar"}), 400


@app.route("/version", methods=["GET"])
def get_version():
    data_version = '0.5' #ANOTAR VERSION ACTUAL DEL CHECKER!
    download_link ='https://mega.nz/file/zINVSaDQ#LCzKLP4SW5chd77aIrKg0FkLP7pMcw0LIGYOgkanZyY'
    return jsonify({'version': data_version, 'download_link': download_link})

@app.route("/get_geoip/<int:user_id>", methods=["GET"])
def get_geoip(user_id):

    try:

        local_hwid = request.headers.get('hwid')

        print("Local HWID", local_hwid)

        # Crear un cursor para ejecutar consultas SQL
        cursor = mysqlProject.connection.cursor()

        global user_hwid

        query = "SELECT hwid FROM usuario WHERE user_id = %s"
        cursor.execute(query, (user_id,))
        result = cursor.fetchone()
        user_hwid = result[0]

        print("User HWID", user_hwid)

        if user_hwid == None:
                
            query = "UPDATE usuario SET hwid = %s WHERE user_id = %s"
            cursor.execute(query, (local_hwid, user_id))
            mysqlProject.connection.commit()
            print("HWID Actualizado correctamente para el USER: ", user_id, local_hwid)
        
        elif user_hwid != local_hwid:
            return jsonify({"error": "Unauthorized User"}), 403


        # Realizar la búsqueda en la base de datos
        cursor = mysqlProject.connection.cursor()

        # Función para obtener los dias asociado al usuario
        def get_days_for_user(user_id):
            cursor.execute('''
                SELECT DATEDIFF(fecha_fin, CURDATE()) AS dias_restantes
                FROM suscripcion
                JOIN usuario ON user_id = fk_user_id
                WHERE user_id = %s
            ''', (user_id,))
            result = cursor.fetchone()
            dias_restantes = result[0] if result else 0
            return dias_restantes
        
        dias_restantes = get_days_for_user(user_id)

        cursor.close()

        if dias_restantes != None and dias_restantes > 0:

            # Realizar la búsqueda en la base de datos
            cursor = mysqlProject.connection.cursor()

            # Función para obtener el token asociado al usuario
            def get_token_for_user(user_id):
                cursor.execute('''
                    SELECT token FROM token
                    JOIN usuario ON user_id = token.fk_user_id
                    WHERE user_id = %s
                ''', (user_id,))
                token_row = cursor.fetchone()
                return token_row[0] if token_row else None
            
            # Recuperar el token original del usuario
            original_token = get_token_for_user(user_id)
            original_token = "Bearer " + original_token

            print('Token BASE', original_token)

            # Cerrar conexión a la base de datos
            cursor.close()

            # Leer el token de autenticación de la cabecera
            auth_token = request.headers.get('Authorization')

            print('Token LOCAL', auth_token)

            # Tu token original
            tokenGH = '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'

            # Validar si el token coincide
            if not auth_token or not auth_token.startswith('Bearer ') or auth_token != original_token:
                return jsonify({"error": "Unauthorized Bearer"}), 401
            
            # Respuesta exitosa si el token es válido
            return jsonify({'geoip': tokenGH, 'user': 'worldkrory', 'tag': 'Screen'}), 200
        
        else:
            # Respuesta cuando no tiene dias disponibles.
            return jsonify({"error": "Unauthorized User"}), 403

    except Exception as e:
        print("ERROR EN PROCESAR SOLICITUD", e)
        return jsonify({"error": f"Error al procesar la solicitud: {str(e)}"}), 500


@app.route("/support", methods=["GET"])
def get_support():
    support1 = 'https://api.whatsapp.com/send?phone=573023326366'
    support2 = 'https://api.whatsapp.com/send?phone=573026631784'
    support3 = 'https://api.whatsapp.com/send?phone=573236796356'
    return jsonify({'supp1': support1, 'supp2': support2, 'supp3': support3})


@app.route("/mail", methods=["GET"])
def get_correo():
    try:
        with open('correos.txt', 'r') as archivo:
            correos = archivo.read().splitlines()
        
        # Elegir un correo aleatorio de la lista
        correo_original = random.choice(correos)
        
    except FileNotFoundError:
        return jsonify({'message': 'error'})
    
    return jsonify({'correo': correo_original})

@app.route("/link",methods=["GET"])
def get_link():
    cursor = mysqlProject.connection.cursor()
    cursor.execute('SELECT VERSION, LINK FROM VERSIONS')
    LINK = cursor.fetchall()
    for link in LINK:
        data = link[0]     
    donwload_link = link[1]
    return donwload_link

@app.route("/get_userid", methods=["POST"])
def get_userid():

    data = request.get_json()  # Obtener los datos JSON de la solicitud
    if data is None:
        return jsonify({'error': 'No se recibieron datos en la solicitud'}), 400  # Bad Request

    # Obtener los datos del usuario enviados en la solicitud
    username = data['username']
    password = data['password']

    if not username or not password:
        return jsonify({'error': 'Faltan parametros requeridos'}), 401

    # Verificar que el usuario y la contraseña sean correctos
    cursor = mysqlProject.connection.cursor()
    try:
        cursor.execute('SELECT user_id FROM usuario WHERE username = %s AND password = %s', (username, password))
        result = cursor.fetchone()

        if not result:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        userid = result[0]
        minOrbes = 1200

        # Obtener días restantes de suscripción en una única consulta
        cursor.execute('''
            SELECT DATEDIFF(fecha_fin, CURDATE()) AS dias_restantes
            FROM suscripcion
            WHERE fk_user_id = %s AND estado = %s
        ''', (userid, 'Activo'))
        result = cursor.fetchone()

        dias_restantes = result[0] if result else 0

    except Exception as e:
        return jsonify({'GetUserID Exception': str(e)}), 500
    finally:
        cursor.close()

    return jsonify({
        'user_id': userid,
        'minOrbes': minOrbes,
        'dias_restantes': dias_restantes
    }), 200


@app.route("/get_credits", methods=["POST"])
def get_credits():

    data = request.get_json()  # Obtener los datos JSON de la solicitud
    if data is None:
        return jsonify({'error': 'No se recibieron datos en la solicitud'}), 400  # Bad Request
    

    # Obtener los datos del usuario enviados en la solicitud
    username = data['username']
    password = data['password']

    # Crear un cursor para ejecutar consultas SQL
    cursor = mysqlProject.connection.cursor()

    # Consulta para obtener los credits del usuario
    query = "SELECT creditos FROM usuario WHERE username = %s AND password = %s"
    cursor.execute(query, (username, password))

    # Obtener el resultado de la consulta
    result = cursor.fetchone()

    # Si no se encontró ningún usuario, devolver un mensaje de error
    if not result:
        return jsonify({'error': 'Usuario no encontrado'})

    credits = result[0]

    # Devolver el user_id en formato JSON
    return jsonify({'credits': credits}), 200  # Retorna el user_id en una respuesta JSON con código 200

@app.route("/get_lives", methods=["GET"])
def get_lives():
    # Obtener usuario y contraseña desde la solicitud
    username = request.json['username']
    password = request.json['password']

    # Verificar que el usuario y la contraseña sean correctos
    cursor = mysqlProject.connection.cursor()
    cursor.execute('SELECT user_id FROM usuario WHERE username = %s AND password = %s', (username, password))
    result = cursor.fetchone()

    if result is None:
        # Si el usuario y la contraseña no coinciden, devolver un error
        return jsonify({'error': 'Autenticación fallida'}), 401
    
    userid = result[0]

    # Si la autenticación es correcta, recuperar los datos de tarjetas_base
    query = '''
    SELECT cc, mes, year, ccv, type, bank, data, franquicia, pais, fecha, estado, gate
    FROM tarjeta
    WHERE fk_user_id = %s
    '''
    cursor.execute(query, (userid,))
    lives = cursor.fetchall()
    cursor.close()

    if lives:
        # Convertir los resultados a un formato JSON y devolver
        lives_list = [{"GATE": live[11], "CC": live[0], "MES": live[1], "YEAR": live[2], "CCV": live[3], "TYPE": live[4], "BANK": live[5], "DATA": live[6], "FRANQUICIA": live[7], "PAIS":live[8], "FECHA":live[9], "ESTADO":live[10]} for live in lives]
        return jsonify(lives_list)
    else:
        # Si no hay registros, devolver un mensaje apropiado
        return jsonify({'message': 'No se encontraron datos'}), 404

@app.route('/buscar-tarjeta', methods=['POST'])
def buscar_tarjeta():

    try:
        # Extraer los primeros 6 dígitos del número de tarjeta enviado en la petición
        digitos = request.json['numero'][:6]

        # Calcular la fecha de hace una semana
        una_semana_atras = datetime.now() - timedelta(days=15)

        # Realizar la consulta a la base de datos
        cursor = mysqlProject.connection.cursor()
        # Asumiendo que la columna 'number' almacena los números de las tarjetas y 'gate' es lo que queremos retornar
        cursor.execute('SELECT DISTINCT gate FROM tarjetas_base WHERE number LIKE %s AND fecha_subida >= %s AND fecha_subida != "0000-00-00 00:00:00"', (digitos + '%', una_semana_atras))
        gates = cursor.fetchall()
        cursor.close()

        # Preparar y enviar la respuesta
        if gates:
            response = {
                'status': 'success',
                'gates': [gate[0] for gate in gates]  # Extraer solo los valores de 'gate' de la respuesta de la consulta
            }
        else:
            response = {
                'status': 'error',
                'message': 'No se encontraron coincidencias en la última semana'
            }
        return jsonify(response)
    except Exception as e:
        try:
            print('Local HWID:', local_hwid, "Autenticado como: ", user_hwid, "se encuentra BUSCAAANDO..")
        except Exception as e:
            print("FALLO EN buscar-tarjeta", e)

@app.route('/add-credits', methods=['POST'])
def add_credits():
    # Obtener la clave y el nombre de usuario de la solicitud
    received_key = request.json.get('key')
    username = request.json.get('username')
    
    # Crear un cursor para ejecutar consultas SQL
    cursor = mysqlProject.connection.cursor()
    
    # Buscar la clave en la tabla CODE
    cursor.execute('SELECT * FROM CODE WHERE codes = %s', (received_key,))
    key_entry = cursor.fetchone()
    
    # Verificar si se encontró una coincidencia
    if key_entry:
        # Si se encuentra la clave, buscar los créditos del usuario en la tabla users
        cursor.execute('SELECT creditos FROM usuario WHERE username = %s', (username,))
        user_credits = cursor.fetchone()
        
        # Verificar si se encontró el usuario
        if user_credits is not None:
            print(user_credits)
            print(key_entry)
            credits_to_add = key_entry[1]
            new_credits = str(int(user_credits[0] + key_entry[1])) # Asumiendo que la cantidad de créditos está en la tercera columna de CODE
            
            # Actualizar los créditos del usuario
            cursor.execute('UPDATE usuario SET creditos = %s WHERE username = %s', (new_credits, username))

            # Ahora, eliminar la clave usada de la tabla CODE
            cursor.execute('DELETE FROM CODE WHERE codes = %s', (received_key,))

            # Confirmar los cambios en la base de datos
            mysqlProject.connection.commit()
            
            # Devolver una respuesta de éxito
            msg = '*USUARIO:* '+username+'\n*KEY:* '+received_key+'\n*CEDITOS AGREGADOS:* '+str(credits_to_add)
            bot_token = '7483065423:AAEBuZaoqFTB3ZHGB9DCXsh9QzoJIYzCTVwAAAAAAAAAAAAAAAA'
            bot_chatID = '-1002057187041'
            send_text = 'https://api.telegram.org/bot' + bot_token + '/sendMessage?chat_id=' + bot_chatID + '&parse_mode=Markdown&text=' + msg
            response = requests.get(send_text)
            return jsonify({'status': 'success', 'message': f'{credits_to_add} Credits added successfully. ✓'}), 200
        else:
            return jsonify({'status': 'error', 'message': 'User not found.'}), 404
    else:
        return jsonify({'status': 'error', 'message': 'Key not found.'}), 404

@app.route('/alertMessage', methods=['POST'])
def alertMessage():
    username = request.json.get('username')
    bot_token = '7483065423:AAEBuZaoqFTB3ZHGB9DCXsh9QzoJIYzCTVwAAAAAAAAAAAAAAAAAAAAA'
    bot_chatID = '-4598522363'
    username = '*'+username+'*' 
    msg = 'El usuario: '+username+' a infringido las normas!'
    send_text = 'https://api.telegram.org/bot' + bot_token + '/sendMessage?chat_id=' + bot_chatID + '&parse_mode=Markdown&text=' + msg
    response = requests.get(send_text)
    return jsonify({'status': 'success'}), 200

# FUNCIONES PEGASUS LIMBO

def connect_database():
    conexion = mysql.connector.connect(
        host="sql10.freemysqlhosting.net",
        user="sql10602886",
        password="bDk5lykwBk",
        database="sql10602886"
    )
    return conexion

@app.route('/create', methods=['GET', 'POST'])
@login_required
def create():

    # Obtener la fecha y hora actual
    fecha_hora_actual = datetime.now()
    # Formatear a 'YYYY-MM-DD HH:MM:SS'
    fecha_formateada = fecha_hora_actual.strftime('%Y-%m-%d %H:%M:%S')

    if request.method == 'POST':
        # Obtener datos del formulario
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        credits = int(request.form['credits'])
        
        amounts = {
            350: 70000,
            385: 70000,
            420: 70000,
            750: 115000,
            825: 115000,
            900: 115000,
            1500: 190000,
            1650: 190000,
            1800: 190000,
            2500: 280000,
            2750: 280000,
            3000: 280000
        }
        amount = amounts[credits]

        # Manejar la carga de la imagen
        image_url = None
        if 'image' in request.files:
            image = request.files['image']
            if image.filename != '':
                # Subir imagen a Cloudinary
                response = cloudinary.uploader.upload(image)
                image_url = response['secure_url']
        
        # Insertar usuario en la base de datos
        conn = connect_database()
        cursor = conn.cursor()

        cursor.execute('''
            insert into usuario (username, email, creditos, fecha_reg, password)
            values (%s, %s, %s, %s, %s)
        ''', (username, email, credits, fecha_formateada, password))

        user_id = cursor.lastrowid
        cursor.execute('''
            INSERT INTO recharges (user_id, credits, amount, image_path)
            VALUES (%s, %s, %s, %s)
        ''', (user_id, credits, amount, image_url))

        conn.commit()
        conn.close()

        msg = f"""
        BIENVENIDO A SNOWX CHECKER
    - *USUARIO:* {username}
    - *CRÉDITOS:* {str(credits)}

    *¡AGREGADO!*
    """
        
        send_photo_url = f'https://api.telegram.org/bot{bot_token}/sendPhoto'
        
        # Enviar la imagen con el texto si está disponible
        if image_url:
            requests.get(send_photo_url, params={
                'chat_id': bot_chatID,
                'photo': image_url,
                'caption': msg,
                'parse_mode': 'Markdown'
            })

        # Almacenar el mensaje de bienvenida en la sesión
        session['bienvenida'] = """
        <div style='margin-top: 20px;'>
            <p>🎉 <strong>"BIENVENIDO"</strong> 🎉</p>
            <p>Ahora eres parte de</p>
            <p>💎 <strong>PEGASUS CLUB</strong> 💎</p>
            <ul>
                <li><strong>USUARIO:</strong> {}</li>
                <li><strong>PASSWORD:</strong> {}</li>
                <li><strong>CRÉDITOS:</strong> {}</li>
            </ul>
            <p>¡AGREGADO! 🥳</p>
            <p>Link del grupo</p>
            <p><a>https://chat.whatsapp.com/JuTQ6pJZOSr3NFbkPFlZY9 Grupo de WhatsApp</a></p>
            <p>En la descripción del grupo está link de descarga y explicación de los gates.</p>
        </div>
        """.format(request.form['username'], request.form['password'], request.form['credits'])

        return redirect(url_for('read_users'))
    return render_template('create.html')

@app.route('/read_users', methods=['GET', 'POST'])
@login_required
def read_users():
    mensaje_bienvenida = session.pop('bienvenida', None)
    mensaje_recarga = session.pop('recarga', None)
    order_by = request.args.get('order_by', 'id')
    order_type = request.args.get('order_type', 'asc')
    search_name = ""

    if request.method == 'POST':
        search_name = request.form['search_name']
        query = "SELECT * FROM users WHERE name LIKE %s OR username LIKE %s ORDER BY {} {}".format(order_by, order_type)
        params = ('%' + search_name + '%', '%' + search_name + '%')
    else:
        query = "SELECT * FROM users ORDER BY {} {}".format(order_by, order_type)
        params = ()

    conn = connect_database()
    cursor = conn.cursor()
    cursor.execute(query, params)
    users = cursor.fetchall()
    conn.close()

    return render_template('read_users.html', users=users, mensaje_bienvenida=mensaje_bienvenida)


@app.route('/edit_user/<int:user_id>', methods=['GET', 'POST'])
@login_required
def edit_user_admin(user_id):
    if request.method == 'POST':
        plan = int(request.form['plan'])
        amounts = {
            0: 0,
            350: 70000,
            385: 70000,
            420: 70000,
            750: 115000,
            825: 115000,
            900: 115000,
            1500: 190000,
            1650: 190000,
            1800: 190000,
            2500: 280000,
            2750: 280000,
            3000: 280000
        }
        amount = amounts[plan]

        new_password = request.form.get('new_password')
        phone = request.form.get('phone', None)  # Obtener el número de teléfono si está presente

        # Manejar la carga de la imagen
        image_url = None
        if 'image' in request.files:
            image = request.files['image']
            if image.filename != '':
                # Subir imagen a Cloudinary
                response = cloudinary.uploader.upload(image)
                image_url = response['secure_url']

        conn = connect_database()
        cursor = conn.cursor()

        # Obtener los créditos actuales antes de la actualización
        cursor.execute('SELECT credits FROM users WHERE id = %s', (user_id,))
        current_credits = cursor.fetchone()[0]

        if plan == 0:
            # Si el plan es 0, actualizar solo la contraseña y/o el teléfono, sin cambiar los créditos
            if new_password and phone:
                cursor.execute('UPDATE users SET password = %s, phone = %s WHERE id = %s', (new_password, phone, user_id))
            elif new_password:
                cursor.execute('UPDATE users SET password = %s WHERE id = %s', (new_password, user_id))
            elif phone:
                cursor.execute('UPDATE users SET phone = %s WHERE id = %s', (phone, user_id))
        else:
            # Si el plan no es 0, actualizar créditos, contraseña y/o teléfono
            new_credits = current_credits + plan

            if new_password and phone:
                cursor.execute('UPDATE users SET credits = %s, password = %s, phone = %s WHERE id = %s', (new_credits, new_password, phone, user_id))
            elif new_password:
                cursor.execute('UPDATE users SET credits = %s, password = %s WHERE id = %s', (new_credits, new_password, user_id))
            elif phone:
                cursor.execute('UPDATE users SET credits = %s, phone = %s WHERE id = %s', (new_credits, phone, user_id))
            else:
                cursor.execute('UPDATE users SET credits = %s WHERE id = %s', (new_credits, user_id))

            # Registrar la recarga solo si el plan no es 0
            cursor.execute('''
                INSERT INTO recharges (user_id, credits, amount, image_path)
                VALUES (%s, %s, %s, %s)
            ''', (user_id, plan, amount, image_url))

        cursor.execute('SELECT * FROM users WHERE id = %s', (user_id,))
        user = cursor.fetchone()

        conn.commit()
        conn.close()

        # Mensaje de bienvenida solo si el plan no es 0
        if plan != 0:
            session['bienvenida'] = """
<div style='margin-top: 20px;'>
    <p>🎉 <strong> RECARGA EXITOSA </strong> 🎉</p>
    <ul>
        <li><strong>USUARIO:</strong> {}</li>
        <li><strong>CRÉDITOS ACTUALES:</strong> {}</li>
        <li><strong>CRÉDITOS NUEVOS:</strong> {}</li>
    </ul>
    <p>¡DISFRUTA DE TUS CREDITOS! 💎🥳</p>
</div>
""".format(user[2], str(current_credits), str(new_credits))

            msg = f"""
- *USUARIO:* {user[2]}
- *CRÉDITOS ACTUALES:* {str(current_credits)}
- *CRÉDITOS NUEVOS:* {str(new_credits)}

*¡EDITADO!*
"""
            send_photo_url = f'https://api.telegram.org/bot{bot_token}/sendPhoto'
            
            # Enviar la imagen con el mensaje si está disponible
            if image_url:
                requests.get(send_photo_url, params={
                    'chat_id': bot_chatID,
                    'photo': image_url,
                    'caption': msg,
                    'parse_mode': 'Markdown'
                })
            else:
                # Enviar solo el texto si no hay imagen
                send_text = 'https://api.telegram.org/bot' + bot_token + '/sendMessage?chat_id=' + bot_chatID + '&parse_mode=Markdown&text=' + msg
                response = requests.get(send_text)

        # Redirige a la página de lectura de usuarios después de editar
        return redirect(url_for('read_users'))

    # Si es una solicitud GET, obtén los detalles del usuario para mostrar en el formulario
    conn = connect_database()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE id = %s', (user_id,))
    user = cursor.fetchone()
    conn.close()

    return render_template('edit_user.html', user=user)

@app.route('/earnings', methods=['GET'])
@login_required
def earnings():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    conn = connect_database()
    cursor = conn.cursor()
    
    # Consultar el total de ganancias
    query = """
    SELECT SUM(r.amount) 
    FROM recharges r
    WHERE (%s IS NULL OR r.recharge_date >= %s) 
      AND (%s IS NULL OR r.recharge_date <= %s)
    """
    params = [start_date, start_date, end_date, end_date]
    
    cursor.execute(query, params)
    total_earnings = int(cursor.fetchone()[0] or 0)
    
    # Consultar todas las recargas junto con el nombre del usuario
    query = """
    SELECT r.id, r.user_id, u.name, r.credits, r.amount, r.recharge_date, r.image_path
    FROM recharges r
    JOIN users u ON r.user_id = u.id
    WHERE (%s IS NULL OR r.recharge_date >= %s) 
      AND (%s IS NULL OR r.recharge_date <= %s)
    """
    
    cursor.execute(query, params)
    recharges = cursor.fetchall()
    
    conn.close()
    
    # Renderizar la plantilla con los datos de las recargas y ganancias
    return render_template(
        'earnings.html',
        total_earnings=total_earnings,
        recharges=recharges,
        start_date=start_date,
        end_date=end_date
    )

@app.route('/delete_user/<int:user_id>', methods=['GET', 'POST'])
@login_required
def delete_user(user_id):
    if request.method == 'POST':
        conn = connect_database()
        cursor = conn.cursor()

        # Solo eliminar el usuario de la base de datos
        cursor.execute('DELETE FROM users WHERE id = %s', (user_id,))
        
        conn.commit()
        conn.close()

        return redirect(url_for('read_users'))

    # Obtener información del usuario antes de eliminarlo
    conn = connect_database()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE id = %s', (user_id,))
    user = cursor.fetchone()
    conn.close()

    return render_template('delete_user.html', user=user)

@app.route('/keys', methods=['GET', 'POST'])
@login_required
def keys():
    if request.method == 'POST':
        # Obtener datos del formulario
        credits = int(request.form['credits'])
        code = generate_random_code()

        # Insertar código en la base de datos
        conn = connect_database()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO CODE (codes, credits)
            VALUES (%s, %s)
        ''', (code, credits))
        conn.commit()
        conn.close()

        # Crear mensaje para el nuevo código
        message = f"""¡Hola equipo de SnowX Checker y VIP! 🎉 Con este código *{code}* tendrán {credits} créditos 🎁 para redimir en el ítem de KEYS 🔑. ¡Por favor agradecer a quien lo redima! 🙌 Buena suerte 🍀."""

        # Puedes enviar este mensaje por correo, Telegram, o mostrarlo en la página web.
        # Por ejemplo, puedes almacenarlo en la sesión para mostrarlo después de redirigir.
        session['message'] = message

        return redirect(url_for('keys'))  # Redirigir después de procesar el formulario

    # Obtener todos los códigos y sus créditos
    conn = connect_database()
    cursor = conn.cursor()
    cursor.execute('SELECT codes, credits FROM CODE')
    codes = cursor.fetchall()
    conn.close()

    # Obtener el mensaje de la sesión si existe
    message = session.pop('message', None)

    return render_template('keys.html', codes=codes, message=message)

@app.route('/gh_token', methods=['GET'])
def gh_token():

    # Obtener el token de GitHub desde las variables de entorno
    github_token = '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'
    
    if not github_token:
        return jsonify({'error': 'Token de GitHub no encontrado'}), 400
    
    return github_token


import random
import string
def generate_random_code(length=7):
    letters_and_digits = string.ascii_letters + string.digits
    return ''.join(random.choice(letters_and_digits) for i in range(length))


if __name__ == '__main__':
    app.run(debug=True)
