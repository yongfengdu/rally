# Copyright 2015: Mirantis Inc.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import mock

from rally.plugins.openstack.context import stacks
from tests.unit import fakes
from tests.unit import test

CTX = "rally.plugins.openstack.context"
SCN = "rally.plugins.openstack.scenarios"


class TestStackGenerator(test.TestCase):

    def _gen_tenants(self, count):
        tenants = {}
        for id in range(count):
            tenants[str(id)] = dict(name=str(id))
        return tenants

    def test_init(self):
        context = {
            "task": mock.MagicMock(),
            "config": {
                "stacks": {
                    "stacks_per_tenant": 1,
                    "resources_per_stack": 1
                }
            }
        }

        inst = stacks.StackGenerator(context)
        self.assertEqual(inst.config, context["config"]["stacks"])

    @mock.patch("%s.heat.utils.HeatScenario._create_stack" % SCN,
                return_value=fakes.FakeStack(id="uuid"))
    @mock.patch("%s.stacks.osclients" % CTX)
    def test_setup(self, mock_osclients, mock_heat_scenario__create_stack):
        tenants_count = 2
        users_per_tenant = 5
        stacks_per_tenant = 1

        fc = fakes.FakeClients()
        mock_osclients.Clients.return_value = fc

        tenants = self._gen_tenants(tenants_count)
        users = []
        for ten_id in tenants:
            for i in range(users_per_tenant):
                users.append({"id": i, "tenant_id": ten_id,
                              "endpoint": "endpoint"})

        context = {
            "config": {
                "users": {
                    "tenants": tenants_count,
                    "users_per_tenant": users_per_tenant,
                    "concurrent": 10,
                },
                "stacks": {
                    "stacks_per_tenant": stacks_per_tenant,
                    "resources_per_stack": 1
                }
            },
            "task": mock.MagicMock(),
            "users": users,
            "tenants": tenants
        }

        stack_ctx = stacks.StackGenerator(context)
        stack_ctx.setup()
        self.assertEqual(tenants_count * stacks_per_tenant,
                         mock_heat_scenario__create_stack.call_count)
        # check that stack ids have been saved in context
        for ten_id in context["tenants"].keys():
            self.assertEqual(stacks_per_tenant,
                             len(context["tenants"][ten_id]["stacks"]))

    @mock.patch("%s.stacks.resource_manager.cleanup" % CTX)
    def test_cleanup(self, mock_cleanup):
        context = {
            "task": mock.MagicMock(),
            "users": mock.MagicMock()
        }
        stack_ctx = stacks.StackGenerator(context)
        stack_ctx.cleanup()
        mock_cleanup.assert_called_once_with(names=["heat.stacks"],
                                             users=context["users"])
