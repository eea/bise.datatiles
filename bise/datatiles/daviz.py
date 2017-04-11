""" Tiles to embed daviz
"""

from DateTime import DateTime
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from collective.cover.tiles.base import IPersistentCoverTile
from collective.cover.tiles.base import PersistentCoverTile
from collective.cover.tiles.data import PersistentCoverTileDataManager
from plone.app.textfield import RichText
from plone.autoform import directives as form
from zope.component import adapter
from zope.interface import implements
from zope.schema import TextLine        # , Int
import logging
import lxml.etree
import requests

logger = logging.getLogger('bise.datatiles.daviz')


class IDavizTile(IPersistentCoverTile):

    title = TextLine(title=u'Title',
                     description=u'Tile title',
                     required=False,)

    daviz_url = TextLine(title=u'Daviz URL', required=True,)
    description = RichText(title=u'Description', required=False)

    daviz_title = TextLine(title=u'Daviz title', required=False,)
    published = TextLine(title=u'Published', required=False)

    form.omitted('daviz_title')
    form.omitted('published')
    # TODO: implement chart name


class DavizTile(PersistentCoverTile):
    """ Base class for Daviz tiles
    """

    is_configurable = True
    is_editable = True
    is_droppable = False

    implements(IDavizTile)

    def is_empty(self):
        url = self.data.get('daviz_url', None)
        # title = self.data.get('daviz_url', None)
        # description = self.data.get('description', None)

        return not url


class DavizFullWidthTile(DavizTile):
    """ Daviz viewed in a big (fullwidth) tile
    """

    short_name = u'Daviz Embed'
    index = ViewPageTemplateFile('pt/daviz_fullwidth.pt')


class DavizPreviewTile(DavizTile):
    """ Daviz viewed in a big (fullwidth) tile
    """

    short_name = u'Daviz Preview'
    index = ViewPageTemplateFile('pt/daviz_preview.pt')

    def cleanup_url(self, url):
        if "#" in url:
            url = url.split("#")[0]
        return url


@adapter(IDavizTile)
class DavizTileDataManager(PersistentCoverTileDataManager):
    """ Data manager for daviz tiles, enables populating the
    from @@rdf based on url
    """

    # _provider = """Data provided by <a href=${url}>${title}</a>"""

    def cleanup_url(self, url):
        if "#" in url:
            url = url.split("#")[0]
        return url

    def _get_daviz_details(self, url):
        if not url.endswith('/@@rdf'):
            url = url + '/@@rdf'
        resp = requests.get(url)
        text = resp.text
        e = lxml.etree.fromstring(str(text))
        title = e.xpath(
            'davizvisualization:DavizVisualization/dcterms:title',
            namespaces=e.nsmap)[0].text
        issued = e.xpath(
            'davizvisualization:DavizVisualization/dcterms:issued',
            namespaces=e.nsmap)[0].text
        issued = self.context.toLocalizedTime(DateTime(issued))
        res = dict(daviz_title=title, published=issued)

        return res

    def set(self, data):
        url = self.cleanup_url(data.get('daviz_url'))

        try:
            extracted = self._get_daviz_details(url)
            data.update(extracted)
        except Exception:
            logger.exception("Errors while trying to extract daviz data")

        super(DavizTileDataManager, self).set(data)
