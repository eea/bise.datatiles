from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from collective.cover import _
from collective.cover.tiles.base import IPersistentCoverTile
from collective.cover.tiles.base import PersistentCoverTile
from plone.app.textfield import RichText
from plone.autoform.directives import write_permission
from zope import schema
from zope.interface import implementer


class IEmbedTile(IPersistentCoverTile):

    write_permission(embed='collective.cover.EmbedCode')
    embed = schema.Text(
        title=_(u'Embedding code'),
        required=False,
    )

    title = schema.TextLine(
        title=_(u'Title'),
        required=False,
    )

    description = RichText(title=u'Description', required=False)


@implementer(IEmbedTile)
class EmbedTile(PersistentCoverTile):

    index = ViewPageTemplateFile('pt/embed.pt')

    is_configurable = True
    is_editable = True
    is_droppable = False
    short_name = default = u'HTML Embed'

    def is_empty(self):
        return not (self.data.get('embed', None) or
                    self.data.get('title', None) or
                    self.data.get('description', None))

    def accepted_ct(self):
        """Return an empty list as no content types are accepted."""
        return []
