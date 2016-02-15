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
Image cache weigher. Weigh hosts based on their cached images.
"""

import hashlib

import nova.conf
from nova.scheduler import weights

CONF = nova.conf.CONF


class ImageCacheWeigher(weights.BaseHostWeigher):
    minval = 0
    maxval = 1

    def weight_multiplier(self):
        """Override the weight multiplier."""
        return CONF.cache_weight_multiplier

    def _weigh_object(self, host_state, request_spec):
        """Higher weights win."""

        # The image cache reports the sha1 hash of the UUID of the
        # cached images
        cached_sha1 = host_state.cached_images
        image_id = request_spec.image.id
        if not image_id:
            return self.minval

        image_sha1 = hashlib.sha1(image_id).hexdigest()
        if image_sha1 in cached_sha1:
            return self.maxval

        return self.minval
