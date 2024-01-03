import os
import sys
import psycopg2
from configparser import ConfigParser


class Clients:
    def create_table(self):
        cur.execute("""
            DROP TABLE IF EXISTS clients CASCADE;
            DROP TABLE IF EXISTS phones CASCADE;
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS clients(
                client_id serial PRIMARY KEY,
                first_name varchar(40) NOT NULL,
                last_name varchar(40) NOT NULL,
                email varchar(60) UNIQUE
                );
        """)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS phones(
            phone_id serial PRIMARY KEY,
            client_id int NOT NULL REFERENCES clients(client_id),
            phone_number varchar(11) UNIQUE
            );
        """)

    def _get_all_phone_numbers(self, client_id):
        cur.execute("""
            SELECT phone_number FROM phones
            WHERE client_id = %s;
        """, (client_id,))
        return cur.fetchall()

    def _get_phone_id(self, phone_number):
        cur.execute("""
            SELECT phone_id FROM phones
            WHERE phone_number = %s
        """, (phone_number,))
        return cur.fetchone()

    def add_client(self, first_name, last_name, email, phone_number=None):
        cur.execute("""
            INSERT INTO clients(first_name, last_name, email)
            VALUES(%s, %s, %s) RETURNING client_id;
        """, (first_name, last_name, email))
        client_id = cur.fetchone()
        if phone_number:
            cur.execute("""
            INSERT INTO phones(client_id, phone_number)
            VALUES(%s, %s);
            """, (client_id, phone_number))

    def add_phone_number(self, client_id, phone_number):
        cur.execute("""
            INSERT INTO phones(client_id, phone_number)
            VALUES(%s, %s);
        """, (client_id, phone_number))

    def change_client(self, client_id, first_name=None, last_name=None,
                    email=None, phone_number=None):
        if first_name:
            cur.execute("""
                UPDATE clients SET first_name = %s
                WHERE client_id = %s;
            """, (first_name, client_id))
        if last_name:
            cur.execute("""
                UPDATE clients SET last_name = %s
                WHERE client_id = %s;
            """, (last_name, client_id))
        if email:
            cur.execute("""
                UPDATE clients SET email = %s
                WHERE client_id = %s;
            """, (email, client_id))
        if phone_number:
            all_phone_numbers = self._get_all_phone_numbers(client_id)
            if len(all_phone_numbers) > 1:
                print("Enter the client's previous phone number(11 digits)"
                      " to replace for:")
                old_phone_number = input()
                cur.execute("""
                UPDATE phones SET phone_number = %s
                WHERE phone_id = %s;
                """, (phone_number, self._get_phone_id(old_phone_number)))
            elif len(all_phone_numbers) == 1:
                cur.execute("""
                UPDATE phones SET phone_number = %s
                WHERE client_id = %s;
                """, (phone_number, client_id))
            else:
                self.add_phone_number(client_id, phone_number)

    def remove_phone_number(self, phone_number):
        cur.execute("""
            DELETE FROM phones
            WHERE phone_number = %s;
        """, (phone_number,))

    def remove_client(self, client_id):
        all_phone_numbers = self._get_all_phone_numbers(client_id)
        for phone_number in all_phone_numbers:
            cur.execute("""
                DELETE FROM phones
                WHERE phone_number = %s
            """, (phone_number,))
        cur.execute("""
            DELETE FROM clients
            WHERE client_id = %s;
        """, (client_id,))

    def search_client(self, *args):
        result = []
        for arg in args:
            cur.execute("""
                SELECT * FROM clients
                WHERE first_name = %s
            """, (arg,))
            res = cur.fetchall()
            result.extend(res)
            cur.execute("""
                SELECT * FROM clients
                WHERE last_name = %s
            """, (arg,))
            res = cur.fetchall()
            result.extend(res)
            cur.execute("""
                SELECT * FROM clients
                WHERE email = %s
                """, (arg,))
            res = cur.fetchall()
            result.extend(res)
            if arg.isdigit and len(arg) == 11:
                cur.execute("""
                    SELECT client_id FROM phones
                    WHERE phone_number = %s
                    """, (arg,))
                client_id = cur.fetchall()
                cur.execute("""
                    SELECT * FROM clients
                    WHERE client_id = %s
                """, (client_id[0][0],))
                res = cur.fetchall()
                result.extend(res)
        print(*result)


if __name__ == '__main__':
    client = Clients()
    parser = ConfigParser()
    creds_file_name = 'db_creds.ini'
    if creds_file_name not in os.listdir():
        print(f'Not found {creds_file_name} in the project folder {os.getcwd()}')
        sys.exit()
    try:
        parser.read(creds_file_name)
        db_params = {'database': parser['db_creds']['database'],
                     'user': parser['db_creds']['user'],
                     'password': parser['db_creds']['password'],
                     'host': parser['db_creds']['host'],
                     'port': parser['db_creds']['port']}
        conn = psycopg2.connect(**db_params)
    except KeyError as err:
        print(f'Incorrect key or value in {creds_file_name}', err)
        sys.exit()
    except psycopg2.OperationalError as err:
        print('Incorrect database credentials', err)
        sys.exit()
    except psycopg2.ProgrammingError as err:
        print('Incorrect database parameters', err)
        sys.exit()
    try:
        with conn:
            with conn.cursor() as cur:
                client.create_table()
            with conn.cursor() as cur:
                client.add_client('Elizabeth', 'Olsen', 'elizabeth@olsen.com',
                                  '08541324794')
                client.add_client('Vanessa', 'Kirby', 'vanessa@kirby.com',
                                  '41653287903')
            with conn.cursor() as cur:
                client.add_phone_number(1, '49742314580')
                client.add_phone_number(2, '18756378952')
                client.add_phone_number(2, '78361825908')
            with conn.cursor() as cur:
                client.change_client(2, 'Charlotte', 'Riley',
                                     'charlotte@riley.com', '27330945174')
            with conn.cursor() as cur:
                client.remove_phone_number('18756378952')
            with conn.cursor() as cur:
                client.remove_client(1)
            with conn.cursor() as cur:
                client.search_client('Riley')
    except psycopg2.InterfaceError as err:
        print('Cursor already closed', err)
    finally:
        conn.close()
