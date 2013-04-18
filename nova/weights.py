# Copyright (c) 2011-2012 OpenStack Foundation
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
Pluggable Weighing support
"""

from nova import loadables


def normalize(weight_list, normalize_to=1.0):
    """Normalize the values in a list.

    Normalize the values between 0 and normalize_to (default 1.0). If all the
    values are equal they are normalized to 0.
    """
    lmax = max(weight_list) * 1.0
    lmin = min(weight_list) * 1.0
    if lmax == lmin:
        return [0] * len(weight_list)
    range_ = lmax - lmin
    return [normalize_to * (i - lmin) / range_ for i in weight_list]


class WeighedObject(object):
    """Object with weight information."""
    def __init__(self, obj, weight):
        self.obj = obj
        self.weight = weight

    def __repr__(self):
        return "<WeighedObject '%s': %s>" % (self.obj, self.weight)


class BaseWeigher(object):
    """Base class for pluggable weighers."""
    def _weight_multiplier(self):
        """How weighted this weigher should be.  Normally this would
        be overriden in a subclass based on a config value.
        """
        return 1.0

    def _weigh_object(self, obj, weight_properties):
        """Override in a subclass to specify a weight for a specific
        object.
        """
        return 0.0

    def weigh_objects(self, weighed_obj_list, weight_properties):
        """Weigh multiple objects.  Override in a subclass if you need
        need access to all objects in order to manipulate weights.
        """
        # Calculate the weights
        weights = []
        for obj in weighed_obj_list:
            weights.append(self._weigh_object(obj.obj, weight_properties))

        # normalize, multiply and sum up
        weights = normalize(weights)
        for obj in weighed_obj_list:
            obj.weight += (self._weight_multiplier() *
                           weights[weighed_obj_list.index(obj)])


class BaseWeightHandler(loadables.BaseLoader):
    object_class = WeighedObject

    def get_weighed_objects(self, weigher_classes, obj_list,
            weighing_properties):
        """Return a sorted (highest score first) list of WeighedObjects."""

        if not obj_list:
            return []

        weighed_objs = [self.object_class(obj, 0.0) for obj in obj_list]
        for weigher_cls in weigher_classes:
            weigher = weigher_cls()
            weigher.weigh_objects(weighed_objs, weighing_properties)

        return sorted(weighed_objs, key=lambda x: x.weight, reverse=True)
