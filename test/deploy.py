# -*- coding: utf-8 -*-

import sys

sys.path.append('..')

from ansible_util.ansible_task import AnsibleTask

TIDB_VERSION = 'v3.0.3'
TIDB_URL = 'http://download.pingcap.org/tidb-%s-linux-amd64.tar.gz' % TIDB_VERSION
TIDB_SHA256_URL = 'http://download.pingcap.org/tidb-%s-linux-amd64.sha256' % TIDB_VERSION


def deploy():
    task = AnsibleTask('get_url', 'url=%s dest=/tmp/tidb.sha256 force=yes' % TIDB_SHA256_URL, 'localhost')
    print(task.get_result())
    task = AnsibleTask('shell', "cat /tmp/tidb.sha256|awk '{print $1}'", 'localhost')
    result = task.get_result()
    print(result)
    sha256 = result['success']['localhost']['stdout']
    task = AnsibleTask('get_url', 'url=%s dest=/tmp/tidb.tar.gz force=yes checksum=%s' % (TIDB_URL, sha256), 'localhost')
    print(task.get_result())


if __name__ == '__main__':
    deploy()
