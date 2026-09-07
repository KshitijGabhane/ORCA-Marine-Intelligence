import mysql.connector


def get_db_connection():

    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="prince@183",
        database="orca_sos"
    )