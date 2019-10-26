# -*- coding: utf-8 -*-

import sys

sys.path.append('..')

from ansible.ansible_task import AnsibleTask

TIDB_VERSION = 'v3.0.3'
TIDB_URL = 'http://download.pingcap.org/tidb-%s-linux-amd64.tar.gz' % TIDB_VERSION
TIDB_SHA256_URL = 'http://download.pingcap.org/tidb-%s-linux-amd64.sha256' % TIDB_VERSION


def deploy():
    task = AnsibleTask('get_url', 'url=%s dest=/tmp/tidb.sha256 force=yes' % TIDB_SHA256_URL, 'localhost')
    print(task.get_result())
    task = AnsibleTask('shell', "cat /tmp/tidb.sha256|awk '{print $1}'")
    print(task.get_result())
    # task = AnsibleTask('get_url', 'url=%s dest=/tmp/tidb.tar.gz force=yes checksum' % TIDB_URL, 'localhost')
    # print(task.get_result())


if __name__ == '__main__':
    deploy()
