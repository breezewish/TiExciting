# -*- coding: utf-8 -*-

import sys

sys.path.append('..')

from ansible_util.ansible_task import AnsibleTask

TIDB_VERSION = 'v3.0.3'
TIDB_URL = 'http://download.pingcap.org/tidb-%s-linux-amd64.tar.gz' % TIDB_VERSION
TIDB_SHA256_URL = 'http://download.pingcap.org/tidb-%s-linux-amd64.sha256' % TIDB_VERSION
TIDB_DIR_NAME = 'tidb-%s-linux-amd64' % TIDB_VERSION


def deploy():
    # 1. 下载sha256
    task = AnsibleTask('get_url', 'url=%s dest=/tmp/tidb.sha256 force=yes' % TIDB_SHA256_URL)
    print(task.get_result())

    # 2. 取出sha256
    task = AnsibleTask('shell', "cat /tmp/tidb.sha256|awk '{print $1}'")
    result = task.get_result()
    print(result)
    sha256 = result['success']['localhost']['stdout']

    task = AnsibleTask('stat', 'checksum_algorithm=sha256 path=/tmp/tidb.tar.gz')
    result = task.get_result()
    print(result)
    if not result['exists'] or result['checksum'] != sha256:
        # 3. 下载大礼包并检查sha256
        task = AnsibleTask('get_url', 'url=%s dest=/tmp/tidb.tar.gz force=yes checksum=sha256:%s' % (TIDB_URL, sha256))
        print(task.get_result())

    # 4. 解压大礼包
    task = AnsibleTask('shell', 'tar -xzf /tmp/tidb.tar.gz')
    print(task.get_result())

    # 5. 分发大礼包
    # pd   => /tmp/{{TIDB_DIR_NAME}}/bin/pd-server
    # tikv => /tmp/{{TIDB_DIR_NAME}}/bin/tikv-server
    # tidb => /tmp/{{TIDB_DIR_NAME}}/bin/tidb-server
    pd_path = '/tmp/%s/bin/pd-server' % TIDB_DIR_NAME
    tikv_path = '/tmp/%s/bin/tikv-server' % TIDB_DIR_NAME
    tidb_path = '/tmp/%s/bin/tidb-server' % TIDB_DIR_NAME

    task = AnsibleTask('copy', 'src=%s dest=~/TiExciting/pd/' % pd_path, 'pd_servers')
    print(task.get_result())

    task = AnsibleTask('copy', 'src=%s dest=~/TiExciting/tikv/' % tikv_path, 'tikv_servers')
    print(task.get_result())

    task = AnsibleTask('copy', 'src=%s dest=~/TiExciting/tidb/' % tidb_path, 'tidb_servers')
    print(task.get_result())

    # 6. 生成执行脚本

    # 7. 执行命令


if __name__ == '__main__':
    deploy()
