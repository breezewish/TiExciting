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

    def __init__(self, *args, **kwargs):
        super().__init__(args, kwargs)
        self.ok = {}
        self.failed = {}
        self.unreachable = {}

    def v2_runner_on_ok(self, result):
        host = result._host
        self.ok[host] = result
        super().v2_runner_on_ok(result)

    def v2_runner_on_failed(self, result, ignore_errors=False):
        host = result._host
        self.failed[host] = self._dump_results(result._result)
        super().v2_runner_on_failed(result, ignore_errors=False)

    def v2_runner_on_unreachable(self, result):
        host = result._host
        self.unreachable[host] = result
        super().v2_runner_on_unreachable(result)


class AnsibleTask(object):

    def __init__(self, module, command):
        self.module = module
        self.command = command

    def _run(self):
        loader = DataLoader()
        passwords = dict(vault_pass='secret')

        self.results_callback = ResultCallback()

        inventory = InventoryManager(loader=loader, sources=['/etc/ansible/hosts'])
        variable_manager = VariableManager(loader=loader, inventory=inventory)

        # create play with tasks
        play_source = dict(
            name="Ansible Play",
            hosts='all',
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
                stdout_callback=results_callback,  # Use our custom callback instead of the ``default`` callback plugin
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
            info['stdout'] = result._result['stdout']
            info['delta'] = result
            result_all['success'][host] = info

        for host, result in self.results_callback.failed.items():
            if 'msg' in result._result:
                result_all['failed'][host] = result._result['msg']

        for host, result in self.results_callback.unreachable.items():
            if 'msg' in result._result:
                result_all['failed'][host] = result._result['msg']

        return json.dumps(result_all, ensure_ascii=False, sort_keys=True, indent=2)


context.CLIARGS = ImmutableDict(connection='local', module_path=None, forks=10, become=None,
                                become_method=None, become_user=None, check=False, diff=False)

if __name__ == '__main__':
    res = AnsibleTask('shell', 'hostname')
    print(res.get_result())
