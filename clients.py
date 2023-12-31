import psycopg2
from psycopg2 import OperationalError
import sys


class Client:
    try:
        conn = psycopg2.connect(database='client_db', user='postgres',
                                password='123456')
        cur = conn.cursor()
    except OperationalError as err:
        print('Incorrect database credentials', err)
        sys.exit()

    def create_table(self):
        self.cur.execute("""
            DROP TABLE IF EXISTS phone;
            DROP TABLE IF EXISTS client;       
        """)
        self.cur.execute("""
            CREATE TABLE IF NOT EXISTS client(
                client_id serial PRIMARY KEY,
                first_name varchar(40) NOT NULL,
                last_name varchar(40) NOT NULL,
                email varchar(60) UNIQUE
                );
        """)
        self.cur.execute("""
            CREATE TABLE IF NOT EXISTS phone(
                phone_id serial PRIMARY KEY,
                client_id int NOT NULL REFERENCES client(client_id),
                phone_number varchar(11) UNIQUE
                );
        """)
        self.conn.commit()

    def _get_all_phone_numbers(self, client_id):
        self.cur.execute("""
            SELECT phone_number FROM phone
            WHERE client_id = %s;
        """, (client_id,))
        return self.cur.fetchall()

    def _get_phone_id(self, phone_number):
        self.cur.execute("""
            SELECT phone_id FROM phone
            WHERE phone_number = %s
        """, (phone_number,))
        return self.cur.fetchone()

    def add_client(self, first_name, last_name, email, phone_number=None):
        self.cur.execute("""
            INSERT INTO client(first_name, last_name, email) 
            VALUES(%s, %s, %s) RETURNING client_id;
        """, (first_name, last_name, email))
        client_id = self.cur.fetchone()
        if phone_number:
            self.cur.execute("""
            INSERT INTO phone(client_id, phone_number)
            VALUES(%s, %s);
            """, (client_id, phone_number))
        self.conn.commit()

    def add_phone_number(self, client_id, phone_number):
        self.cur.execute("""
            INSERT INTO phone(client_id, phone_number)
            VALUES(%s, %s);
        """, (client_id, phone_number))
        self.conn.commit()

    def change_data(self, client_id, first_name=None, last_name=None,
                    email=None, phone_number=None):
        if first_name:
            self.cur.execute("""
                UPDATE client SET first_name = %s
                WHERE client_id = %s;
            """, (first_name, client_id))
        if last_name:
            self.cur.execute("""
                UPDATE client SET last_name = %s
                WHERE client_id = %s;
            """, (last_name, client_id))
        if email:
            self.cur.execute("""
                UPDATE client SET email = %s
                WHERE client_id = %s;
            """, (email, client_id))
        if phone_number:
            all_phone_numbers = self._get_all_phone_numbers(client_id)
            if len(all_phone_numbers) > 1:
                print("Enter the client's previous phone number(11 digits)"
                      " to replace for:")
                old_phone_number = input()
                self.cur.execute("""
                UPDATE phone SET phone_number = %s
                WHERE phone_id = %s;
                """, (phone_number, self._get_phone_id(old_phone_number)))
            elif len(all_phone_numbers) == 1:
                self.cur.execute("""
                UPDATE phone SET phone_number = %s
                WHERE client_id = %s;
                """, (phone_number, client_id))
            else:
                self.add_phone_number(client_id, phone_number)
            self.conn.commit()

    def delete_phone_number(self, phone_number):
        self.cur.execute("""
            DELETE FROM phone
            WHERE phone_number = %s;
        """, (phone_number,))
        self.conn.commit()

    def delete_client(self, client_id):
        all_phone_numbers = self._get_all_phone_numbers(client_id)
        for phone_number in all_phone_numbers:
            self.cur.execute("""
                DELETE FROM phone
                WHERE phone_number = %s
            """, (phone_number,))
        self.cur.execute("""
            DELETE FROM client
            WHERE client_id = %s;
        """, (client_id,))
        self.conn.commit()

    def find_client(self, first_name=None, last_name=None,
                    email=None, phone_number=None):
        result = []
        if first_name:
            self.cur.execute("""
                SELECT * FROM client
                WHERE first_name = %s;
            """, (first_name,))
            res = self.cur.fetchall()
            result.extend(res)
        if last_name:
            self.cur.execute("""
                SELECT * FROM client
                WHERE last_name = %s;
            """, (last_name,))
            res = self.cur.fetchall()
            result.extend(res)
        if email:
            self.cur.execute("""
                SELECT * FROM client
                WHERE email = %s;
            """, (email,))
            res = self.cur.fetchall()
            result.extend(res)
        if phone_number:
            self.cur.execute("""
                SELECT * FROM phone
                WHERE phone_number = %s;
            """, (phone_number,))
            res = self.cur.fetchall()
            result.extend(res)
        if len(result) == 0:
            return
        print(*result)


client = Client()
client.create_table()
client.add_client('Elizabeth', 'Olsen', 'elizabeth@olsen.com', '08541324794')
client.add_phone_number(1, '49742314580')
client.add_client('Vanessa', 'Kirby', 'vanessa@kirby.com', '41653287903')
client.add_phone_number(2, '18756378952')
client.add_phone_number(2, '78361825908')
client.change_data(2, 'Charlotte', 'Riley', 'charlotte@riley.com', '27330945174')
client.delete_phone_number('18756378952')
client.delete_client(1)
client.find_client(last_name='Riley')
client.cur.close()
client.conn.close()
