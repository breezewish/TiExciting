# -*- coding: utf-8 -*-

import json
import shutil
from ansible.module_utils.common.collections import ImmutableDict
from ansible.parsing.dataloader import DataLoader
from ansible.vars.manager import VariableManager
from ansible.inventory.manager import InventoryManager
from ansible.playbook.play import Play
from ansible.executor.task_queue_manager import TaskQueueManager
from ansible.plugins.callback import CallbackBase
from ansible import context
import ansible.constants as C


class ResultCallback(CallbackBase):

    def __init__(self):
        super(ResultCallback, self).__init__()
        self.ok = {}
        self.failed = {}
        self.unreachable = {}

    def v2_runner_on_ok(self, result):
        host = result._host.get_name()
        self.ok[host] = result
        super().v2_runner_on_ok(result)

    def v2_runner_on_failed(self, result, ignore_errors=False):
        host = result._host.get_name()
        self.failed[host] = result
        super().v2_runner_on_failed(result, ignore_errors=False)

    def v2_runner_on_unreachable(self, result):
        host = result._host.get_name()
        self.unreachable[host] = result
        super().v2_runner_on_unreachable(result)


class AnsibleTask(object):

    def __init__(self, module, command, group='localhost'):
        self.module = module
        self.command = command
        self.group = group

    def _run(self):
        loader = DataLoader()
        passwords = dict(vault_pass='secret')

        self.results_callback = ResultCallback()

        inventory = InventoryManager(loader=loader, sources=['/etc/ansible/hosts'])
        variable_manager = VariableManager(loader=loader, inventory=inventory)

        # create play with tasks
        play_source = dict(
            name="Ansible Play",
            hosts=self.group,
            gather_facts='no',
            tasks=[
                dict(action=dict(module=self.module, args=self.command), register='shell_out'),
            ]
        )
        play = Play().load(play_source, variable_manager=variable_manager, loader=loader)

        # actually run it
        tqm = None
        try:
            tqm = TaskQueueManager(
                inventory=inventory,
                variable_manager=variable_manager,
                loader=loader,
                passwords=passwords,
                stdout_callback=self.results_callback,
            )
            result = tqm.run(play)
        finally:
            if tqm is not None:
                tqm.cleanup()

    def get_result(self):
        self._run()
        result_all = {'success': {}, 'failed': {}, 'unreachable': {}}

        for host, result in self.results_callback.ok.items():
            info = {}
            if self.module=='shell':
                info['stdout'] = result._result['stdout']
                info['delta'] = result._result['delta']
            result_all['success'][host] = info

        for host, result in self.results_callback.failed.items():
            result_all['failed'][host] = result._result.get('msg') or result._result

        for host, result in self.results_callback.unreachable.items():
            result_all['unreachable'][host] = result._result.get('msg') or result._result

        return result_all
        # return json.dumps(result_all, ensure_ascii=False, sort_keys=True, indent=2)


context.CLIARGS = ImmutableDict(connection='smart', module_path=None, forks=10, become=None,
                                become_method=None, become_user=None, check=False, diff=False, verbosity=1)

if __name__ == '__main__':
    res = AnsibleTask('shell', 'ls ~', 'localhost')
    # res = AnsibleTask('shell', 'hostname')
    # res = AnsibleTask("copy", "src=./hosts dest=~/")
    print(res.get_result())
