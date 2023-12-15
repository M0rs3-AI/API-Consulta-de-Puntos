from flask import Flask, jsonify, request
import pyodbc

app = Flask(__name__)

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
            cursor.execute("SELECT Nombre, Ruc, password, Puntos, Dirección, Teléfono1 FROM dbo.CLI_CLIENTES WHERE Ruc = ? AND password = ?", cedula, password)
            row = cursor.fetchone()
            
            clientes = {
                'Nombre': row.Nombre,
                'Password': row.password,
                'Cedula': row.Ruc,
                'Direccion': row.Dirección,
                'Telefono1': row.Teléfono1
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

@app.route('/users', methods=['GET'])
def obtener_clientes():
    try:
        conn = pyodbc.connect(conn_string)
        cursor = conn.cursor()
        
        # Ajusta la consulta SQL según lo que necesites extraer de la base de datos
        cursor.execute("SELECT Nombre, Ruc, password, Puntos, Dirección, Teléfono1 FROM dbo.CLI_CLIENTES")  # [COHERVI_BAK].[dbo].[CLI_CLIENTES]
        rows = cursor.fetchall()

        # Construir una lista de diccionarios para convertir a JSON
        clientes = []
        for row in rows:
            clientes.append({
                'Nombre': row.Nombre,
                'Password': row.password,
                'Cedula': row.Ruc,
                'Direccion': row.Dirección,
                'Telefono1': row.Teléfono1
            })

        cursor.close()
        conn.close()

        return jsonify(clientes)

    except Exception as e:
        # Manejar cualquier error
        return jsonify()

if __name__ == '__main__':
    app.run(debug=True)