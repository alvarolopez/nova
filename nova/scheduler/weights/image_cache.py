# Copyright (c) 2013 OpenStack Foundation
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
Image Cache Weigher.
"""

from oslo.config import cfg

from nova.scheduler import weights

image_cache_weight_opts = [
        cfg.FloatOpt('image_cache_weight_multiplier',
                     default=1.0,
                     help='Multiplier for the cached image weighter'),
        cfg.BoolOpt('image_cache_weight_inverse',
                     default=False,
                     help='By default we give a higer weight to nodes '
                          'that have an image cached, set this to False '
                          'for the oposite.')
]

CONF = cfg.CONF
CONF.register_opts(image_cache_weight_opts)


class ImageCacheWeigher(weights.BaseHostWeigher):
    def _weight_multiplier(self):
        """Override the weight multiplier."""
        return CONF.image_cache_weight_multiplier

    def _weigh_object(self, host_state, weight_properties):
        """Weight the node according to the cached images."""
        sha1 = weight_properties.get("image_sha", None)
        has = False
        if sha1 in host_state.capabilities["available_images"]:
            has = True

        if CONF.image_cache_weight_inverse:
            has = not has

        if has:
            return 1.0

        return 0.0
