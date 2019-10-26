# -*- coding: utf-8 -*-

import random
import sqlite3
from flask import Flask, request, g, render_template
from flask_socketio import SocketIO

DATABASE = './data.db'

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()


def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv


def insert_db(query, args=()):
    db = get_db()
    db.execute(query, args)
    db.commit()


@app.route('/')
def hello():
    return f'Hello World'


def show_users():
    users = query_db("select * from user")
    return render_template('sql-test.html', users=users)


@app.route('/sql-test', methods=['GET', 'POST'])
def sql_test():
    if request.method == 'GET':
        return show_users()
    else:
        name = request.form['name']
        insert_db("insert into user (name) values (?)", (name,))
        return show_users()


@app.route('/ansible', methods=['GET', 'POST'])
def ansible_test():
    return render_template('ansible.html')


@app.route('/websocket', methods=['GET'])
def websocket_test():
    return render_template('socket.html')


@socketio.on('connect')
def test_connect():
    print('connect!')

    t1 = random.randint(1, 10)
    socketio.emit('server_response', {'data': t1})
    socketio.sleep(5)
    t2 = random.randint(1, 10)
    socketio.emit('server_response', {'data': t2})
    socketio.sleep(5)
    t3 = random.randint(1, 10)
    socketio.emit('server_response', {'data': t3})
    print(t1, t2, t3)

    # while True:
    #     t = random.randint(1, 10)
    #     socketio.emit('server_response', {'data': t})
    #     socketio.sleep(5)


@socketio.on('disconnect')
def test_disconnect():
    print('disconnect')


if __name__ == '__main__':
    socketio.run(app, debug=True)
