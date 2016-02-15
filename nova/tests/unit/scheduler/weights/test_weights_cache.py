# Copyright (c) 2015 Spanish National Research Council (CSIC)
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
"""
Tests for image cache weigher.
"""

import hashlib

from nova.scheduler import host_manager
from nova.scheduler import weights
from nova.scheduler.weights import image_cache
from nova import test
from nova.tests.unit.scheduler import fakes


class CacheWeigherTestCase(test.NoDBTestCase):
    def setUp(self):
        super(CacheWeigherTestCase, self).setUp()
        self.weight_handler = weights.HostWeightHandler()
        self.weighers = [image_cache.ImageCacheWeigher()]

    def _get_weighed_hosts(self, hosts, image_id):
        weight_properties = {"request_spec": {"image": {"id": image_id}}}
        return self.weight_handler.get_weighed_objects(self.weighers,
                hosts, weight_properties)

    def _get_all_hosts(self):
        def fake_metric(value):
            return host_manager.MetricItem(value=value, timestamp='fake-time',
                                           source='fake-source')

        metrics = {
            "h1": fake_metric([hashlib.sha1("image 1").hexdigest()]),
            "h2": fake_metric([hashlib.sha1("image 2").hexdigest(),
                               hashlib.sha1("image 4").hexdigest()]),
            "h3": fake_metric([hashlib.sha1("image 3").hexdigest(),
                               hashlib.sha1("image 4").hexdigest()]),
        }

        host_values = [
            ('h1', 'n1', {'metrics': {'cached.images.sha1': metrics["h1"]}}),
            ('h2', 'n2', {'metrics': {'cached.images.sha1': metrics["h2"]}}),
            ('h3', 'n3', {'metrics': {'cached.images.sha1': metrics["h3"]}}),
            ('h4', 'n4', {'metrics': {}}),
        ]
        return [fakes.FakeHostState(host, node, values)
                for host, node, values in host_values]

    def _do_test(self, expected_weight, expected_host, image_id):
        hostinfo_list = self._get_all_hosts()
        weighed_host = self._get_weighed_hosts(hostinfo_list, image_id)[0]
        self.assertEqual(expected_weight, weighed_host.weight)
        self.assertEqual(expected_host, weighed_host.obj.host)

    def test_image_cached_in_one_node(self):
        self._do_test(1.0, 'h1', 'image 1')
        self._do_test(1.0, 'h2', 'image 2')
        self._do_test(1.0, 'h3', 'image 3')

    def test_image_cached_in_several_nodes(self):
        hostinfo_list = self._get_all_hosts()
        weighed_hosts = self._get_weighed_hosts(hostinfo_list, "image 4")
        for eh in ("h2", "h3"):
            weighed_host = weighed_hosts.pop(0)
            self.assertEqual(1.0, weighed_host.weight)
            self.assertEqual(eh, weighed_host.obj.host)

    def test_image_not_cached(self):
        self._do_test(0.0, 'h1', 'image foo')
