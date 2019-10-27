# -*- coding: utf-8 -*-

import uuid
import random
import sqlite3
from flask import Flask, request, g, render_template, jsonify
from flask_socketio import SocketIO

from ansible_util.ansible_task import AnsibleTask

from queue import Queue, Empty

from deploy import gen_pd_script, gen_tidb_script, gen_tikv_script, write_to_file

DATABASE = './data.db'

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

q = Queue()

g_task_id = 1
g_task = {}


def mock_consumer(thread_id):
    while True:
        try:
            task = q.get_nowait()
            print('worker %d fetch job %d, will take %d sec...' % (thread_id, task[0], task[1]))
            socketio.sleep(task[1])
            print('worker %d finish job %d..' % (thread_id, task[0]))
        except Empty:
            socketio.sleep(1)


def mock_producer(thread_id):
    task_id = 1
    while True:
        sleep_time = random.randint(1, 10)
        q.put((task_id, sleep_time))
        print('producer put', (task_id, sleep_time))
        task_id += 1
        socketio.sleep(1)


TIDB_VERSION = 'v3.0.3'
TIDB_URL = 'http://download.pingcap.org/tidb-%s-linux-amd64.tar.gz' % TIDB_VERSION
TIDB_SHA256_URL = 'http://download.pingcap.org/tidb-%s-linux-amd64.sha256' % TIDB_VERSION
TIDB_DIR_NAME = 'tidb-%s-linux-amd64' % TIDB_VERSION


def worker_thread(worker_id):
    while True:
        try:
            task_id, step = q.get_nowait()

            socketio.emit('task', {'finish': False, 'step': step})

            print('worker [%d], do work (%d, %d)' % (worker_id, task_id, step['step_id']))

            if step['step_type'] == 1:
                task = AnsibleTask('get_url', 'url=%s dest=/tmp/tidb.sha256 force=yes' % TIDB_SHA256_URL)
                step['result'] = task.get_result()
            elif step['step_type'] == 2:
                task = AnsibleTask('shell', "cat /tmp/tidb.sha256|awk '{print $1}'")
                result = task.get_result()
                step['result'] = result['success']['localhost']['stdout']
            elif step['step_type'] == 3:

                sha256 = None
                dep_id = step['deps'][0]
                for dep_step in g_task[task_id]['steps']:
                    if dep_step['step_id'] == dep_id:
                        sha256 = dep_step['result']

                task = AnsibleTask('stat', 'checksum_algorithm=sha256 path=/tmp/tidb.tar.gz')
                result = task.get_result()
                stat = result['success']['localhost']['stat']
                if not stat['exists'] or stat['checksum'] != sha256:
                    task = AnsibleTask('get_url',
                                       'url=%s dest=/tmp/tidb.tar.gz force=yes checksum=sha256:%s' % (TIDB_URL, sha256))
                    task.get_result()
            elif step['step_type'] == 4:
                task = AnsibleTask('shell', 'tar -xzf /tmp/tidb.tar.gz')
                step['result'] = task.get_result()
            elif step['step_type'] == 5:
                pd_path = '/tmp/%s/bin/pd-server' % TIDB_DIR_NAME
                tikv_path = '/tmp/%s/bin/tikv-server' % TIDB_DIR_NAME
                tidb_path = '/tmp/%s/bin/tidb-server' % TIDB_DIR_NAME

                task = AnsibleTask('copy', 'src=%s dest=~/TiExciting/pd/ mode=0755' % pd_path, 'pd_servers')
                task.get_result()

                task = AnsibleTask('copy', 'src=%s dest=~/TiExciting/tikv/ mode=0755' % tikv_path, 'tikv_servers')
                task.get_result()

                task = AnsibleTask('copy', 'src=%s dest=~/TiExciting/tidb/ mode=0755' % tidb_path, 'tidb_servers')
                task.get_result()
            elif step['step_type'] == 6:
                tmp_path = '/tmp/%s.sh' % str(uuid.uuid4())
                write_to_file(tmp_path, step['arg'])
                server = step['extra']
                task = AnsibleTask('copy', 'src=%s dest=/home/tidb/TiExciting/pd/launch.sh mode=0755' % tmp_path,
                                   server['server_ip'])
                step['result'] = task.get_result()
            elif step['step_type'] == 7:
                tmp_path = '/tmp/%s.sh' % str(uuid.uuid4())
                write_to_file(tmp_path, step['arg'])
                server = step['extra']
                task = AnsibleTask('copy', 'src=%s dest=/home/tidb/TiExciting/tikv/launch.sh mode=0755' % tmp_path,
                                   server['server_ip'])
                step['result'] = task.get_result()
            elif step['step_type'] == 8:
                tmp_path = '/tmp/%s.sh' % str(uuid.uuid4())
                write_to_file(tmp_path, step['arg'])
                server = step['extra']
                task = AnsibleTask('copy', 'src=%s dest=/home/tidb/TiExciting/tidb/launch.sh mode=0755' % tmp_path,
                                   server['server_ip'])
                step['result'] = task.get_result()
            elif step['step_type'] == 9:
                task = AnsibleTask('shell', 'bash /home/tidb/TiExciting/pd/launch.sh', 'pd_servers', True)
                task.get_result()

                task = AnsibleTask('shell', 'bash /home/tidb/TiExciting/tikv/launch.sh', 'tikv_servers', True)
                task.get_result()

                task = AnsibleTask('shell', 'bash /home/tidb/TiExciting/tidb/launch.sh', 'tidb_servers', True)
                task.get_result()
            else:
                socketio.sleep(1)
                continue

            step['status'] = 'finished'
            print(step)
            print('worker [%d], do work done (%d, %d)' % (worker_id, task_id, step['step_id']))
            socketio.emit('task', {'finish': False, 'step': step})

            # 善后处理
            for sstep in g_task[task_id]['steps']:
                if step['step_id'] in sstep['ddeps']:
                    sstep['ddeps'].remove(step['step_id'])

        except Empty:
            socketio.sleep(1)


def dispatcher_thread():
    while True:
        for _, task in g_task.items():
            if task['status'] == 'running':

                done = True

                for step in task['steps']:
                    if step['status'] == 'running' or step['status'] == 'unfinished':
                        done = False
                    if step['status'] == 'unfinished' and not step['ddeps']:
                        step['status'] = 'running'
                        q.put((task['task_id'], step))
                        done = False

                if done:
                    task['status'] = 'finished'
                    socketio.emit('task', {'finish': True})

        socketio.sleep(1)


dispatcher = None


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
    return 'Hello World'


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


def background_thread():
    count = 0
    while True:
        socketio.sleep(2)
        count += 1
        print(count)
        socketio.emit('my response',
                      {'data': 'Message from server', 'count': count})


thread = None


@socketio.on('connect')
def test_connect():
    print('connect!')


@socketio.on('disconnect')
def test_disconnect():
    print('disconnect')


@socketio.on('deploy')
def handle_deploy(message):
    task = g_task[message['task_id']]
    task['status'] = 'running'
    print('deploy task', task['task_id'])

    socketio.emit("sync", {'task': task})

    global dispatcher
    if dispatcher is None:
        dispatcher = socketio.start_background_task(target=dispatcher_thread)
        socketio.start_background_task(target=worker_thread, worker_id=1)
        socketio.start_background_task(target=worker_thread, worker_id=2)
        socketio.start_background_task(target=worker_thread, worker_id=3)


def gen_steps(config, hosts):
    step_id = 1
    steps = []

    # 1. 下载sha256
    step = {
        'step_id': step_id,
        'step_type': 1,
        'msg': '下载sha256',
        'arg': '',
        'extra': None,
        'deps': [],
        'ddeps': [],
        'status': 'unfinished',
        'result': None
    }
    steps.append(step)
    step_id += 1

    # 2. 取出sha256
    step = {
        'step_id': step_id,
        'step_type': 2,
        'msg': '读取sha256',
        'arg': '',
        'extra': None,
        'deps': [1],
        'ddeps': [1],
        'status': 'unfinished',
        'result': None
    }
    steps.append(step)
    step_id += 1

    # 3. 下载大礼包
    step = {
        'step_id': step_id,
        'step_type': 3,
        'msg': '下载TIDB年度大礼包',
        'arg': '',
        'extra': None,
        'deps': [2],
        'ddeps': [2],
        'status': 'unfinished',
        'result': None
    }
    steps.append(step)
    step_id += 1

    # 4. 解压大礼包
    step = {
        'step_id': step_id,
        'step_type': 4,
        'msg': '解压TIDB年度大礼包',
        'arg': '',
        'extra': None,
        'deps': [3],
        'ddeps': [3],
        'status': 'unfinished',
        'result': None
    }
    steps.append(step)
    step_id += 1

    # 5. 分发大礼包
    step = {
        'step_id': step_id,
        'step_type': 5,
        'msg': '分发TIDB大礼包给随从们',
        'arg': '',
        'extra': None,
        'deps': [4],
        'ddeps': [4],
        'status': 'unfinished',
        'result': None
    }
    steps.append(step)
    step_id += 1

    pd_name_cluster = [(server['pd_id'], server['server_ip'], server['server_port']) for server in config if
                       server['role'] == 'pd']
    pd_cluster = [(server['server_ip'], server['server_port']) for server in config if server['role'] == 'pd']

    deps = []
    # 6. 生成执行脚本
    for server in config:
        if server['role'] == 'pd':
            step = {
                'step_id': step_id,
                'step_type': 6,
                'msg': '为[%s:%d]生成PD部署脚本' % (server['server_ip'], server['server_port']),
                'arg': gen_pd_script(server['pd_id'], server['data_dir'], server['server_ip'], server['server_port'],
                                     server['status_port'], pd_name_cluster),
                'extra': server,
                'deps': [5],
                'ddeps': [5],
                'status': 'unfinished',
                'result': None
            }
            deps.append(step_id)
            steps.append(step)
            step_id += 1
        elif server['role'] == 'tikv':
            step = {
                'step_id': step_id,
                'step_type': 7,
                'msg': '为[%s:%d]生成TIKV部署脚本' % (server['server_ip'], server['server_port']),
                'arg': gen_tikv_script('', server['data_dir'], server['server_ip'], server['server_port'],
                                       server['status_port'], pd_cluster),
                'extra': server,
                'deps': [5],
                'ddeps': [5],
                'status': 'unfinished',
                'result': None
            }
            deps.append(step_id)
            steps.append(step)
            step_id += 1
        elif server['role'] == 'tidb':
            step = {
                'step_id': step_id,
                'step_type': 8,
                'msg': '为[%s:%d]生成TIDB部署脚本' % (server['server_ip'], server['server_port']),
                'arg': gen_tidb_script('', server['data_dir'], server['server_ip'], server['server_port'],
                                       server['status_port'], pd_cluster),
                'extra': server,
                'deps': [5],
                'ddeps': [5],
                'status': 'unfinished',
                'result': None
            }
            deps.append(step_id)
            steps.append(step)
            step_id += 1

    # 7. 执行脚本
    step = {
        'step_id': step_id,
        'step_type': 9,
        'msg': '启动TIDB集群',
        'arg': '',
        'extra': None,
        'deps': list(deps),
        'ddeps': list(deps),
        'status': 'unfinished',
        'result': None
    }
    steps.append(step)
    step_id += 1

    return steps


@app.route('/submitTask', methods=['POST'])
def submit_task():
    config = request.get_json()
    hosts = {
        'pd_servers': list(set([server['server_ip'] for server in config if server['role'] == 'pd'])),
        'tidb_servers': list(set([server['server_ip'] for server in config if server['role'] == 'tidb'])),
        'tikv_servers': list(set([server['server_ip'] for server in config if server['role'] == 'tikv']))
    }

    global g_task_id

    task = {
        'task_id': g_task_id,
        'config': config,
        'status': 'unfinished',
        'hosts': hosts,
        'steps': gen_steps(config, hosts)
    }

    g_task[g_task_id] = task
    g_task_id += 1

    return jsonify({'code': 0, 'task_id': task['task_id']})


if __name__ == '__main__':
    socketio.run(app, debug=True)
