""" Base classes for tiles
"""

from AccessControl import Unauthorized
from collective.cover.interfaces import ICoverUIDsProvider
from plone.tiles.interfaces import ITileDataManager
from plone.memoize import view
from plone.uuid.interfaces import IUUID
from plone import api
from plone.app.uuid.utils import uuidToObject

import logging

logger = logging.getLogger('bise.datatiles')


class AssignMultipleItemsMixin:

    @view.memoize
    def assigned(self):
        """Return the list of objects stored in the tile as UUID. If an UUID
        has no object associated with it, removes the UUID from the list.
        :returns: a list of objects.
        """
        # always get the latest data
        uuids = ITileDataManager(self).get().get('uuids', None)

        results = list()
        if uuids:
            ordered_uuids = [(k, v) for k, v in uuids.items()]
            ordered_uuids.sort(key=lambda x: x[1]['order'])

            for uuid in [i[0] for i in ordered_uuids]:
                obj = uuidToObject(uuid)
                if obj:
                    results.append(obj)
                else:
                    # maybe the user has no permission to access the object
                    # so we try to get it bypassing the restrictions
                    catalog = api.portal.get_tool('portal_catalog')
                    brain = catalog.unrestrictedSearchResults(UID=uuid)
                    if not brain:
                        # the object was deleted; remove it from the tile
                        self.remove_item(uuid)
                        logger.debug(
                            'Nonexistent object {0} removed from '
                            'tile'.format(uuid)
                        )

        return results

    def populate_with_object(self, obj):
        """ Add an object to the list of items
        :param obj: [required] The object to be added
        :type obj: Content object
        """
        super(AssignMultipleItemsMixin, self).populate_with_object(obj)
        uuids = ICoverUIDsProvider(obj).getUIDs()
        if uuids:
            self.populate_with_uuids(uuids)

    def populate_with_uuids(self, uuids):
        """ Add a list of elements to the list of items. This method will
        append new elements to the already existing list of items
        :param uuids: The list of objects' UUIDs to be used
        :type uuids: List of strings
        """
        if not self.isAllowedToEdit():
            raise Unauthorized(
                _('You are not allowed to add content to this tile'))
        data_mgr = ITileDataManager(self)

        old_data = data_mgr.get()
        if old_data['uuids'] is None:
            # If there is no content yet, just assign an empty dict
            old_data['uuids'] = dict()

        uuids_dict = old_data.get('uuids')
        if not isinstance(uuids_dict, dict):
            # Make sure this is a dict
            uuids_dict = old_data['uuids'] = dict()

        # if uuids_dict and len(uuids_dict) > self.limit:
        #     # Do not allow adding more objects than the defined limit
        #     return

        order_list = [int(val.get('order', 0))
                      for key, val in uuids_dict.items()]
        if len(order_list) == 0:
            # First entry
            order = 0
        else:
            # Get last order position and increment 1
            order_list.sort()
            order = order_list.pop() + 1

        for uuid in uuids:
            if uuid not in uuids_dict.keys():
                entry = dict()
                entry[u'order'] = unicode(order)
                uuids_dict[uuid] = entry
                order += 1

        old_data['uuids'] = uuids_dict
        data_mgr.set(old_data)

    def replace_with_uuids(self, uuids):
        """ Replaces the whole list of items with a new list of items
        :param uuids: The list of objects' UUIDs to be used
        :type uuids: List of strings
        """
        if not self.isAllowedToEdit():
            raise Unauthorized(
                _('You are not allowed to add content to this tile'))
        data_mgr = ITileDataManager(self)
        old_data = data_mgr.get()
        # Clean old data
        old_data['uuids'] = dict()
        data_mgr.set(old_data)
        # Repopulate with clean list
        self.populate_with_uuids(uuids)

    @view.memoize
    def get_uuid(self, obj):
        """Return the UUID of the object.
        :param obj: [required]
        :type obj: content object
        :returns: the object's UUID
        """
        return IUUID(obj, None)

    def remove_item(self, uuid):
        """ Removes an item from the list
        :param uuid: [required] uuid for the object that wants to be removed
        :type uuid: string
        """
        super(AssignMultipleItemsMixin, self).remove_item(uuid)
        data_mgr = ITileDataManager(self)
        old_data = data_mgr.get()
        uuids = data_mgr.get()['uuids']
        if uuid in uuids.keys():
            del uuids[uuid]
        old_data['uuids'] = uuids
        data_mgr.set(old_data)
