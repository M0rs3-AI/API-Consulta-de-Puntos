from flask import Flask, jsonify, request
from flask_mail import Mail, Message
import random
import string
import pyodbc

app = Flask(__name__)
mail = Mail(app)

app.config['MAIL_SERVER'] = 'smtp.example.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'your-email@example.com'
app.config['MAIL_PASSWORD'] = 'your-password'
mail = Mail(app)

# Utiliza la autenticación de Windows para conectarse a la base de datos
conn_string = "Driver={SQL Server};Server=OMENBYHP;Database=COHERVI_BAK;Trusted_Connection=yes;"

@app.route('/users/login', methods=['POST'])
def login():
    try:
        data = request.json
        cedula = data['cedula']
        password = data['password']

        conn = pyodbc.connect(conn_string)
        cursor = conn.cursor()

        # Verificar las credenciales en la base de datos
        cursor.execute("SELECT COUNT(*) FROM dbo.CLI_CLIENTES WHERE Ruc = ? AND password = ?", cedula, password)
        count = cursor.fetchone()[0]
        if count > 0:
            cursor.execute("SELECT Nombre, Ruc, password, Puntos, Dirección, Teléfono1, Email FROM dbo.CLI_CLIENTES WHERE Ruc = ? AND password = ?", cedula, password)
            row = cursor.fetchone()
            
            clientes = {
                'Nombre': row.Nombre,
                'Cedula': row.Ruc,
                'Password': row.password,
                'Puntos': row.Puntos,
                'Direccion': row.Dirección,
                'Telefono1': row.Teléfono1,
                'Correo': row.Email
            }
            return jsonify({'success': True, 'data': clientes})
        else:
            # Credenciales incorrectas
            return jsonify({'success': False, 'message': 'Credenciales incorrectas'}), 401
    except Exception as e:
        # Manejar cualquier error
        print(e)
        return jsonify({'success': False, 'message': 'Error en el servidor'}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/users/update', methods=['POST'])
def update_user():
    try:
        data = request.json
        cedula = data['cedula']
        
        query = "UPDATE dbo.CLI_CLIENTES SET "
        params = []
        set_clauses = []

        # Agrega cada campo a la consulta si está presente
        if 'new_email' in data and data['new_email']:
            set_clauses.append("Email = ?")
            params.append(data['new_email'])
        if 'new_direccion' in data and data['new_direccion']:
            set_clauses.append("Dirección = ?")
            params.append(data['new_direccion'])
        if 'new_telefono' in data and data['new_telefono']:
            set_clauses.append("Teléfono1 = ?")
            params.append(data['new_telefono'])

        # Completa la consulta
        query += ', '.join(set_clauses) + " WHERE Ruc = ?"
        params.append(cedula)

        # Ejecuta la consulta
        conn = pyodbc.connect(conn_string)
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()

        return jsonify({'success': True, 'message': 'Perfil actualizado con éxito'}), 200

    except Exception as e:
        print(e)
        return jsonify({'success': False, 'message': 'Error al actualizar el perfil'}), 500

    finally:
        cursor.close()
        conn.close()

@app.route('/users/<cedula>', methods=['GET'])
def get_user_data(cedula):
    try:
        cedula = cedula.strip()
        conn = pyodbc.connect(conn_string)
        cursor = conn.cursor()

        # Obtén los datos del usuario desde la base de datos usando la cédula
        cursor.execute("SELECT Nombre, Ruc, password, Puntos, Dirección, Teléfono1, Email FROM dbo.CLI_CLIENTES WHERE Ruc = ?", cedula)
        row = cursor.fetchone()

        if row:
            user_data = {
                'Nombre': row.Nombre,
                'Cedula': row.Ruc,
                'Password': row.password,
                'Correo': row.Email,
                'Puntos': row.Puntos,
                'Direccion': row.Dirección,
                'Telefono1': row.Teléfono1
            }
            return jsonify(user_data), 200
        else:
            return jsonify({'message': 'Usuario no encontrado'}), 404

    except Exception as e:
        print(e)
        return jsonify({'message': 'Error en el servidor'}), 500

    finally:
        cursor.close()
        conn.close()


@app.route('/users', methods=['GET'])
def obtener_clientes():
    try:
        conn = pyodbc.connect(conn_string)
        cursor = conn.cursor()
        
        # Ajusta la consulta SQL según lo que necesites extraer de la base de datos
        cursor.execute("SELECT Nombre, Ruc, password, Puntos, Dirección, Teléfono1, Email FROM dbo.CLI_CLIENTES")  # [COHERVI_BAK].[dbo].[CLI_CLIENTES]
        rows = cursor.fetchall()

        # Construir una lista de diccionarios para convertir a JSON
        clientes = []
        for row in rows:
            clientes.append({
                'Nombre': row.Nombre,
                'Cedula': row.Ruc,
                'Password': row.password,
                'Puntos': row.Puntos,
                'Direccion': row.Dirección,
                'Telefono1': row.Teléfono1,
                'Correo': row.Email
            })

        cursor.close()
        conn.close()

        return jsonify(clientes)

    except Exception as e:
        # Manejar cualquier error
        return jsonify()

@app.route('/users/change_password', methods=['POST'])
def change_password():
    try:
        data = request.json
        cedula = data['cedula']
        currentPassword = data['currentPassword']
        newPassword = data['newPassword']
        
        if ' ' in newPassword:
            return jsonify({'success': False, 'message': 'La contraseña no puede contener espacios'}), 400


        conn = pyodbc.connect(conn_string)
        cursor = conn.cursor()

        # Comprueba la contraseña actual
        cursor.execute("SELECT password FROM dbo.CLI_CLIENTES WHERE Ruc = ?", cedula)
        record = cursor.fetchone()
        if record and record.password.strip == currentPassword:
            # Cambia la contraseña
            cursor.execute("UPDATE dbo.CLI_CLIENTES SET password = ? WHERE Ruc = ?", newPassword, cedula)
            conn.commit()
            return jsonify({'success': True, 'message': 'Contraseña actualizada con éxito'}), 200
        else:
            return jsonify({'success': False, 'message': 'Contraseña actual incorrecta'}), 400

    except Exception as e:
        print(e)
        return jsonify({'success': False, 'message': 'Error en el servidor'}), 500

    finally:
        cursor.close()
        conn.close()

@app.route('/recover_password', methods=['POST'])
def recover_password():
    email = request.json.get('email')
    if not email:
        return jsonify({'message': 'Email is required'}), 400
    
    
    conn = pyodbc.connect(conn_string)
    cursor = conn.cursor()

    try:
        # Verificar si el email existe en la base de datos
        cursor.execute("SELECT COUNT(*) FROM tabla_usuarios WHERE Email = ?", email)
        if cursor.fetchone()[0] == 0:
            return jsonify({'message': 'Email not found'}), 404

        # Generar una contraseña temporal
        temp_password = ''.join(random.choice(string.ascii_letters + string.digits) for i in range(10))

        # Actualizar la base de datos con la contraseña temporal
        cursor.execute("UPDATE tabla_usuarios SET Password = ? WHERE Email = ?", temp_password, email)
        conn.commit()

        # Enviar el email con la contraseña temporal
        msg = Message('Recuperación de Contraseña', sender='tu_correo@example.com', recipients=[email])
        msg.body = f'Tu nueva contraseña temporal es: {temp_password}'
        mail.send(msg)

        return jsonify({'message': 'Email sent'}), 200

    except Exception as e:
        print(e)
        return jsonify({'message': 'Server error'}), 500

    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    app.run(debug=True)