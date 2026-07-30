import sqlite3
conn = sqlite3.connect('running_club.db')
cursor = conn.cursor()
cursor.execute('SELECT id, student_id, username, role FROM users')
for row in cursor.fetchall():
    print(row)
conn.close()
