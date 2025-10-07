import mysql.connector
import random
import string

# Configuración de la conexión a la base de datos MySQL
config = {
    'user': 'sql10602886',
    'password': 'bDk5lykwBk',
    'host': 'sql10.freemysqlhosting.net',
    'database': 'sql10602886',
    'raise_on_warnings': True
}

# Función para generar un código de regalo aleatorio
def generate_gift_code(length=7):
    characters = string.ascii_uppercase + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

# Verifica si el código ya existe en la base de datos
def code_exists(cursor, code):
    cursor.execute("SELECT `codes` FROM CODE WHERE `codes` = %s", (code,))
    return cursor.fetchone() is not None

def main():
    cnx = mysql.connector.connect(**config)
    cursor = cnx.cursor()
    try:
        # Solicitar al usuario la cantidad de códigos a generar y el valor de créditos
        num_codes = int(input("Ingrese la cantidad de códigos a generar: "))
        credits_value = int(input("Ingrese el valor de créditos para todos los códigos: "))

        # Generar y agregar nuevos códigos de regalo a la tabla CODE
        unique_codes = set()
        while len(unique_codes) < num_codes:
            code = generate_gift_code()
            if not code_exists(cursor, code):
                cursor.execute("INSERT INTO CODE (`codes`, `credits`) VALUES (%s, %s)", (code, credits_value))
                unique_codes.add(code)
                print(code)
                cnx.commit()

        print(f"{len(unique_codes)} nuevos registros únicos agregados a la tabla CODE con éxito.")
    except mysql.connector.Error as err:
        print(f"Se produjo un error: {err}")
    finally:
        cursor.close()
        cnx.close()

if __name__ == "__main__":
    main()