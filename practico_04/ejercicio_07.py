"""Base de Datos SQL - Uso de múltiples tablas"""

import datetime
import sqlite3
from ejercicio_02 import agregar_persona
from ejercicio_04 import buscar_persona
from ejercicio_06 import reset_tabla


def agregar_peso(id_persona, fecha, peso):
    """Implementar la funcion agregar_peso, que inserte un registro en la tabla 
    PersonaPeso.

    Debe validar:
    - Que el ID de la persona ingresada existe (reutilizando las funciones ya
        implementadas).
    - Que no existe de esa persona un registro de fecha posterior al que
        queremos ingresar.

    Debe devolver:
    - ID del peso registrado.
    - False en caso de no cumplir con alguna validacion."""

    conn = sqlite3.connect('Practico04_DB.db')
    cursor = conn.cursor()

    persona = buscar_persona(id_persona)

    if not persona:
        conn.close()
        return False

    cursor.execute('''
        SELECT * FROM PersonaPeso
        WHERE IdPersona = ? AND Fecha > ?
    ''', (id_persona, fecha))
    peso_existente = cursor.fetchone()

    if peso_existente:
        conn.close()
        return False

    cursor.execute('''
        INSERT INTO PersonaPeso (IdPersona, Fecha, Peso)
        VALUES (?, ?, ?)
    ''', (id_persona, fecha, peso))

    conn.commit()
    peso_id = cursor.lastrowid
    conn.close()
    return peso_id


# NO MODIFICAR - INICIO
@reset_tabla
def pruebas():
    id_juan = agregar_persona('juan perez', datetime.datetime(1988, 5, 15), 32165498, 180)
    assert agregar_peso(id_juan, datetime.datetime(2018, 5, 26), 80) > 0
    # Test Id incorrecto
    assert agregar_peso(200, datetime.datetime(1988, 5, 15), 80) is False
    # Test Registro previo al 2018-05-26
    assert agregar_peso(id_juan, datetime.datetime(2018, 5, 16), 80) is False


if __name__ == '__main__':
    pruebas()
# NO MODIFICAR - FIN
