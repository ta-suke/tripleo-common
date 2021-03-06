# Copyright 2016 Red Hat, Inc.
# All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
import mock

from tripleo_common.actions import package_update
from tripleo_common.tests import base


class UpdateStackActionTest(base.TestCase):

    def setUp(self,):
        super(UpdateStackActionTest, self).setUp()
        self.timeout = 1
        self.container = 'container'

    @mock.patch('tripleo_common.actions.templates.ProcessTemplatesAction.run')
    @mock.patch('tripleo_common.actions.base.TripleOAction.get_object_client')
    @mock.patch('tripleo_common.actions.base.TripleOAction.'
                'get_orchestration_client')
    @mock.patch('tripleo_common.actions.base.TripleOAction.'
                'get_compute_client')
    @mock.patch('heatclient.common.template_utils.get_template_contents')
    @mock.patch('tripleo_common.utils.plan.get_env')
    @mock.patch('tripleo_common.utils.plan.update_in_env')
    @mock.patch('heatclient.common.template_utils.deep_update')
    def test_run(self, mock_deepupdate,
                 mock_updateinenv,
                 mock_getenv,
                 mock_template_contents,
                 mock_compute_client,
                 mock_orchestration_client,
                 mock_object_client,
                 mock_templates_run):
        mock_ctx = mock.MagicMock()

        heat = mock.MagicMock()
        heat.stacks.get.return_value = mock.MagicMock(
            stack_name='stack', id='stack_id')
        mock_orchestration_client.return_value = heat

        mock_template_contents.return_value = ({}, {
            'heat_template_version': '2016-04-30'
        })
        mock_swift = mock.MagicMock()
        env = {
            'parameters': {
                'ControllerCount': 1,
                'ComputeCount': 1,
                'ObjectStorageCount': 0,
                'BlockStorageCount': 0,
                'CephStorageCount': 0,
            },
            'stack_name': 'overcloud',
            'stack_status': "CREATE_COMPLETE",
            'outputs': [
                {'output_key': 'RoleConfig',
                 'output_value': {
                     'foo_config': 'foo'}},
                {'output_key': 'RoleData',
                 'output_value': {
                     'FakeCompute': {
                         'config_settings': {'nova::compute::fake'
                                             'libvirt_virt_type': 'qemu'},
                         'global_config_settings': {},
                         'logging_groups': ['root', 'neutron', 'nova'],
                         'logging_sources': [{'path': '/var/log/fake.log',
                                             'type': 'tail'}],
                         'monitoring_subscriptions': ['nova-compute'],
                         'service_config_settings': None,
                         'service_metadata_settings': None,
                         'service_names': ['nova_compute', 'fake_service'],
                         'step_config': ['include ::tripleo::profile::fake',
                                         'include ::timezone'],
                         'upgrade_batch_tasks': [],
                         'upgrade_tasks': [{'name': 'Stop fake service',
                                            'service': 'name=fo state=stopped',
                                            'tags': 'step1',
                                            'when': 'existingcondition'},
                                           {'name': 'Stop nova-compute',
                                            'service': 'name=nova-compute '
                                                       'state=stopped',
                                            'tags': 'step1',
                                            'when': ['existing', 'list']}]
                         }}}]}

        update_env = {'resource_registry':
                      {'OS::TripleO::DeploymentSteps': 'OS::Heat::None'}}

        mock_getenv.return_value = env
        fake_registry = {'parameter_defaults':
                         {'DockerKeystoneImage': '192.168.24.1:8787/'
                                                 'keystone-docker:latest',
                          'DockerHeatApiImage:': '192.168.24.1:8787/'
                                                 'heat-api-docker:latest'}}
        update_env.update(fake_registry)
        mock_swift.get_object.return_value = ({}, env)
        mock_object_client.return_value = mock_swift

        action = package_update.UpdateStackAction(self.timeout, fake_registry,
                                                  container=self.container)
        action.run(mock_ctx)
        mock_updateinenv.assert_called_once_with(
            mock_swift, env, 'parameter_defaults',
            fake_registry['parameter_defaults']
        )

        mock_deepupdate.assert_called_once_with(env, update_env)

        heat.stacks.update.assert_called_once_with('stack_id')
