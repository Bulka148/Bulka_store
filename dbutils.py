
import psycopg2


class Database:
    def __init__(self):
        self.con = psycopg2.connect(
            dbname="Bulka_store",
            user="postgres",
            password="Bcvfubkjd2003148",
            host="localhost",
            port=5432
        )
        self.cur = self.con.cursor()
        self.con.autocommit = True

    def add_human(self, human):
        self.cur.execute('INSERT INTO human VALUES(default, %s, %s, default) RETURNING id',
                         (human['login'], human['password']))
        return self.cur.fetchone()[0]

    def get_human(self, login, password):
        if not password:
            self.cur.execute('SELECT id FROM human WHERE login=%s', (login,))
        else:
            self.cur.execute('SELECT * FROM human WHERE login=%s AND password=%s', (login, password))
        a = self.cur.fetchone()
        return {'id': a[0], 'login': a[1], 'password': a[2], 'is_admin': a[3]} if a else {}

    def edit_human(self, human_id, human):
        self.cur.execute('UPDATE human SET login=%s, password=%s WHERE id = %s',
                         (human['login'], human['password'], human_id))

    def add_bread(self, p):
        self.cur.execute('INSERT INTO bread VALUES(default, %s, %s, %s) RETURNING id',
                         (p['name'], p['price'], p['type']))
        return self.cur.fetchone()[0]

    def get_bread(self, bread_id=None):
        self.cur.execute('SELECT * FROM bread ORDER BY id')
        bread = []
        for a in self.cur.fetchall():
            bread.append({'id': a[0], 'name': a[1], 'price': a[2], 'type': a[3]})
            if a[0] == bread_id:
                return bread[-1]
        return bread

    def edit_bread(self, bread_id, bread):
        self.cur.execute('UPDATE bread SET name=%s, price=%s, type=%s WHERE id = %s',
                         (bread['name'], bread['price'], bread['type'], bread_id))

    def delete_bread(self, bread_id):
        self.cur.execute('DELETE FROM bread WHERE id = %s', (bread_id,))

    def add_to_favourite(self, human_id, bread_id):
        self.cur.execute('INSERT INTO favourite VALUES(%s, %s)', (human_id, bread_id))

    def get_from_favourite(self, human_id):
        self.cur.execute('SELECT * FROM favourite WHERE human_id=%s', (human_id,))
        return [e[1] for e in self.cur.fetchall()]

    def delete_from_favourite(self, human_id, bread_id):
        self.cur.execute('DELETE FROM favourite WHERE human_id=%s AND bread_id=%s', (human_id, bread_id))

    def add_to_cart(self, human_id, bread_id):
        self.cur.execute('INSERT INTO cart VALUES(%s, %s)', (human_id, bread_id))

    def get_from_cart(self, human_id):
        self.cur.execute('SELECT * FROM cart WHERE human_id=%s', (human_id,))
        return [e[1] for e in self.cur.fetchall()]

    def delete_from_cart(self, human_id, bread_id):
        self.cur.execute('DELETE FROM cart WHERE human_id=%s AND bread_id=%s', (human_id, bread_id))

    def make_booking(self, human_id, bread_id):
        price = sum([self.get_bread(b_id)['price'] for b_id in bread_id])
        self.cur.execute('INSERT INTO booking VALUES(default, %s, %s) RETURNING id', (human_id, price))
        booking_id = self.cur.fetchone()[0]
        for b_id in bread_id:
            self.cur.execute('INSERT INTO booking_bread VALUES(%s, %s)', (booking_id, b_id))

    def get_bookings_id(self, human_id):
        self.cur.execute('SELECT id FROM booking WHERE human_id=%s', (human_id,))
        return self.cur.fetchall()

    def get_booking(self, booking_id):
        self.cur.execute('SELECT * FROM booking WHERE id=%s', (booking_id,))
        a = self.cur.fetchone()
        booking = {'booking_id': a[0], 'human_id': a[1], 'price': a[2]}
        self.cur.execute('SELECT bread_id FROM booking_bread WHERE booking_id=%s', (booking_id,))
        booking['bread'] = [self.get_bread(a[0]) for a in self.cur.fetchall()]
        return booking
