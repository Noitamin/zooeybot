
import sqlite3

class db:
    def __init__(self, db_name):
        self.db_name = db_name
        self.conn = sqlite3.connect(self.db_name)
        self.cursor = self.conn.cursor()

    def __del__(self):
        self.conn.close()
        print('Connection to {} was closed.'.format(self.db_name))

    def update_users(self, server):
        # Populate database fields
        print('Updating database structure for server {}'.format(server.id))
        try:
            self.cursor.execute("CREATE TABLE users(id INTEGER PRIMARY KEY, userid INTEGER)")
            self.conn.commit()
        except Exception as e:
            print(e)

        try:
            self.cursor.execute("ALTER TABLE users ADD COLUMN jail_count INTEGER")
            self.conn.commit()
        except Exception as e:
            print(e)

        try:
            self.cursor.execute("ALTER TABLE users ADD COLUMN jail_last INTEGER")
            self.conn.commit()
        except Exception as e:
            print(e)

        try:
            self.cursor.execute("ALTER TABLE users ADD COLUMN crystals INTEGER DEFAULT 0")
            self.conn.commit()
        except Exception as e:
            print(e)

        try:
            self.cursor.execute("ALTER TABLE users ADD COLUMN singles INTEGER DEFAULT 0")
            self.conn.commit()
        except Exception as e:
            print(e)

        try:
            self.cursor.execute("ALTER TABLE users ADD COLUMN tens INTEGER DEFAULT 0")
            self.conn.commit()
        except Exception as e:
            print(e)

        try:
            self.cursor.execute("ALTER TABLE users ADD COLUMN total_spark INTEGER DEFAULT 0")
            self.conn.commit()
        except Exception as e:
            print(e)

        # Check if all users are in table

        id_list = [member.id for member in server.members]

        for id in id_list:
            self.cursor.execute("SELECT userid FROM users WHERE userid=?", (int(id),))
            if not self.cursor.fetchone():
                self.execute("INSERT INTO users(userid) VALUES(?)", (int(id),))

        placeholders = ', '.join('?' for id in id_list)
        query = "DELETE FROM users WHERE userid NOT IN ({})".format(placeholders)
        self.execute(query, id_list)

        # DEBUG
        print("user ids in server:")
        self.cursor.execute("SELECT userid FROM users")
        user1 = self.cursor.fetchone()
        while user1:
            print(user1[0])
            user1 = self.cursor.fetchone()

        self.commit()

    def execute(self, query, *args):
        try:
            self.cursor.execute(query, *args)
        except Exception as e:
            self.conn.rollback()
            raise e

    def executeIfAble(self, query, *args):
        try:
            self.cursor.execute(query, *args)
        except:
            pass

    def commit(self):
        self.conn.commit()

    def get(self, userid, col):
        query = "SELECT {} FROM users WHERE userid=?".format(col)
        try:
            self.cursor.execute(query, (userid,))
        except Exception as e:
            print(e)
        data = self.cursor.fetchone()
        if data:
            return data[0]
        else:
            return None

    def set(self, userid, col, value):
        query = "UPDATE users SET {}=? WHERE userid=?".format(col)
        try:
            self.cursor.execute(query, (value, userid))
            self.commit()
        except Exception as e:
            print(e)

    def increment(self, userid, col):
        data = self.get(userid, col)
        if data is None:
            self.set(userid, col, 1)
        else:
            try:
                data += 1
            except TypeError as e:
                print(e)
            self.set(userid, col, data)
