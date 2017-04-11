""" A tile that inserts a contents listing for a specific folder
"""

from Products.CMFPlone.utils import safe_unicode
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from collective.cover.tiles.base import IPersistentCoverTile
from collective.cover.tiles.base import PersistentCoverTile
from plone.app.uuid.utils import uuidToObject
from plone.formwidget.contenttree import UUIDSourceBinder
from plone.tiles.interfaces import ITileDataManager
from plone.uuid.interfaces import IUUID
from z3c.relationfield.schema import RelationChoice
from zope.interface import implements
from zope.schema import TextLine
import logging

logger = logging.getLogger('bise.datatiles')


class IFolderContentsListingTile(IPersistentCoverTile):

    title = TextLine(
        title=u'Title',
        required=False,
    )

    uuid = RelationChoice(
        title=u"Folder Root",
        source=UUIDSourceBinder(portal_type=['Folder', 'FolderishPage',
                                             'SubTopic', 'MainTopic']),
        required=False,
    )


class FolderContentsListingTile(PersistentCoverTile):
    """ Folder listing tile
    """

    implements(IFolderContentsListingTile)

    index = ViewPageTemplateFile('pt/folder_contents.pt')

    is_configurable = False
    is_editable = False
    is_droppable = True
    short_name = u'Folder Listing'

    def children(self):
        source = uuidToObject(self.data['uuid'])
        if source is None:
            return []
        return source.getFolderContents(
            contentFilter=dict(portal_type=['Folder', 'FolderishPage',
                                            'SubTopic', 'MainTopic']))

    def title(self):
        return self.data.get('title', 'Missing tile title')

    def is_empty(self):
        return not self.children()
        # return not (self.data.get('uuid', None))

    def accepted_ct(self):
        """Return an empty list as no content types are accepted."""
        return ['Folder', 'FolderishPage']

    def populate_with_object(self, obj):
        super(FolderContentsListingTile, self).populate_with_object(obj)

        if obj.portal_type not in self.accepted_ct():
            return

        data = {
            'title': safe_unicode(obj.Title()),
            'uuid': IUUID(obj),
        }
        data_mgr = ITileDataManager(self)
        data_mgr.set(data)
