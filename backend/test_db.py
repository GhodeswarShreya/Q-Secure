from database import get_db_connection

connection = get_db_connection()

if connection:
    cursor = connection.cursor()

    cursor.execute("SHOW TABLES")

    print("\nTables in Q-Secure Database:")

    for table in cursor.fetchall():
        print(table[0])

    cursor.close()
    connection.close()

    print("\nDatabase connection test successful!")

else:
    print("Database connection failed!")