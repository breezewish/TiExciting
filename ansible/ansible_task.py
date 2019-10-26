# -*- coding: utf-8 -*-

# !/usr/bin/env python
# coding:utf-8

import json
from collections import namedtuple
from ansible.parsing.dataloader import DataLoader
from ansible.vars import VariableManager
from ansible.inventory import Inventory
from ansible.playbook.play import Play
from ansible.executor.task_queue_manager import TaskQueueManager
from ansible.plugins.callback import CallbackBase


# 这里为封装的返回信息，让我们获取返回信息更加方便进行处理
class ResultCallback(CallbackBase):
    def __init__(self, *args):
        super(ResultCallback, self).__init__(display=None)
        self.status_ok = json.dumps({}, ensure_ascii=False)
        self.status_fail = json.dumps({}, ensure_ascii=False)
        self.status_unreachable = json.dumps({}, ensure_ascii=False)
        self.status_playbook = ''
        self.status_no_hosts = False
        self.host_ok = {}
        self.host_failed = {}
        self.host_unreachable = {}

    def v2_runner_on_ok(self, result):
        host = result._host.get_name()
        self.runner_on_ok(host, result._result)
        self.host_ok[host] = result

    def v2_runner_on_failed(self, result, ignore_errors=False):
        host = result._host.get_name()
        self.runner_on_failed(host, result._result, ignore_errors)
        self.host_failed[host] = result

    def v2_runner_on_unreachable(self, result):
        host = result._host.get_name()
        self.runner_on_unreachable(host, result._result)
        self.host_unreachable[host] = result


class Task():
    def __init__(self, module, command):
        self.module = module
        self.command = command


def run(self):
    # 这里跟ansible.cfg文件中的配置一样
    Options = namedtuple('Options',
                         ['listtags',
                          'listtasks',
                          'listhosts',
                          'syntax',
                          'connection',
                          'module_path',
                          'forks',
                          'remote_user',
                          'private_key_file',
                          'ssh_common_args',
                          'ssh_extra_args',
                          'sftp_extra_args',
                          'scp_extra_args',
                          'become',
                          'become_method',
                          'become_user',
                          'verbosity',
                          'check']
                         )
    variable_manager = VariableManager()
    loader = DataLoader()
    options = Options(listtags=False,
                      listtasks=False,
                      listhosts=False,
                      syntax=False,
                      connection='smart',
                      module_path='/usr/lib/python2.6/site-packages/ansible/modules/',
                      forks=100,
                      remote_user='root',
                      private_key_file=None,
                      ssh_common_args=None,
                      ssh_extra_args=None,
                      sftp_extra_args=None,
                      scp_extra_args=None,
                      become=False,
                      become_method=None,
                      become_user='root',
                      verbosity=None,
                      check=False
                      )
    passwords = dict(vault_pass='secret')
    # 传入的hosts文件
    inventory = Inventory(loader=loader, variable_manager=variable_manager, host_list='config/hosts')
    variable_manager.set_inventory(inventory)

    # 要执行的task
    play_source = dict(
        name="Ansible Play",
        hosts='all',
        gather_facts='no',
        tasks=[
            dict(action=dict(module=self.module, args=self.command), register='shell_out'),
            # dict(action=dict(module='shell', args='id'), register='shell_out'),
            # dict(action=dict(module='shell', args=dict(msg='{{shell_out.stdout}}')))
        ]
    )
    play = Play().load(play_source, variable_manager=variable_manager, loader=loader)

    tqm = None
    try:
        tqm = TaskQueueManager(
            inventory=inventory,
            variable_manager=variable_manager,
            loader=loader,
            options=options,
            passwords=passwords,
        )
    self.results_callback = ResultCallback()
    tqm._stdout_callback = self.results_callback
    result = tqm.run(play)

finally:
if tqm is not None:
    tqm.cleanup()


def get_result(self):
    # 执行任务
    self.run()
    result_all = {'success': {}, 'failed': {}, 'unreachable': {}}
    for host, result in self.results_callback.host_ok.items():
        info = {}
    info['stdout'] = result._result['stdout']
    info['delta'] = result._result['delta']
    result_all['success'][host] = info


for host, result in self.results_callback.host_failed.items():
    if 'msg' in result._result:
        result_all['failed'][host] = result._result['msg']

for host, result in self.results_callback.host_unreachable.items():
    if 'msg' in result._result:
        result_all['unreachable'][host] = result._result['msg']

return json.dumps(result_all, ensure_ascii=False, sort_keys=True, indent=2)

if __name__ == '__main__':
    res = Task('shell', 'hostname')
    print
    res.get_result()

