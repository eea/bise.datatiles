""" Listing tiles
"""

from DateTime import DateTime
from Products.CMFPlone.utils import safe_unicode
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from collective.cover.tiles.base import IPersistentCoverTile
from collective.cover.tiles.base import PersistentCoverTile
from plone.app.textfield import RichText
from plone.app.uuid.utils import uuidToObject
from plone.tiles.interfaces import ITileDataManager
from plone.uuid.interfaces import IUUID
from zope.interface import implements
from zope.schema import TextLine, Int, Choice, Tuple
import json
import logging

# from z3c.relationfield.schema import RelationChoice
# from plone.formwidget.contenttree import UUIDSourceBinder
# from plone.app.vocabularies.catalog import CatalogSource
# from plone.app.vocabularies.catalog import CatalogVocabulary

logger = logging.getLogger('bise.datatiles')


class IListingTile(IPersistentCoverTile):

    title = TextLine(
        title=u'Title',
        required=False,
    )

    # uuid = RelationChoice(
    #     title=u"Linked Source",
    #     source=UUIDSourceBinder(portal_type="Sparql"),
    #     required=False,
    # )
    uuid = Tuple(title=u"Linked Sources",
                 value_type=Choice(
                     title=u"Linked Source",
                     vocabulary="bise.datasource_vocabulary",
                     required=False,
                 ))

    text = RichText(title=u'Text', required=False)

    view_more_url = TextLine(
        title=u'View More URL',
        required=False,
    )

    count = Int(
        title=u'Number of items to display, per source',
        required=False,
        default=6,
    )


class DavizListingTile(PersistentCoverTile):
    """ Base class for Daviz listing tiles

    It accepts both ElasticSearch and Sparql query objects.
    """

    is_configurable = False
    is_editable = True
    is_droppable = False    # True

    implements(IListingTile)

    def render_cell(self, info):
        return self.cell_tpl(daviz=info)

    def accepted_ct(self):
        """Return an empty list as no content types are accepted."""
        return ['Sparql']

    def get_sources(self):
        uuids = self.data.get('uuid')
        if not uuids:
            raise StopIteration
        for uuid in uuids:
            source = uuidToObject(uuid)
            if not source:
                logger.warning("Could not find object with uuid %s", uuid)
                continue
            yield source

    def _extract_sparql_data(self, source, count):
        result = []
        try:
            data = source.getSparqlCacheResults()
        except Exception:
            logger.exception("Error in getting cached data "
                             "for sparql %s", source)
            return []
        try:
            rows, cols = (data['result']['rows'][:count],
                          data['result']['var_names'][:count])
        except Exception:
            logger.exception("No results in sparql %s", source)
            return []

        for row in self._to_dict(rows, cols):
            row['thumb_url'] = "%s/image_preview" % row['item_url']
            result.append(row)
            # a row needs to have:
            # thumb_url, item_url, item_title, item_published
        return result

    def _extract_es_data(self, source, count):
        text = source.get_cached_results()
        if not text:
            return []
        data = json.loads(text)
        # cached = getattr(source, 'cached_results', None)
        # if cached is None:
        #     return []
        #
        # data = json.loads(cached.data)

        try:
            rows = [x['_source'] for x in data['hits']['hits']]
        except KeyError:
            return []

        result = []
        c = 0

        for row in rows:
            title = row.get('title', row.get('name'))
            if not title:
                logger.warning("Could not extract row information for %r", row)
                continue
            row['item_title'] = title
            row['thumb_url'] = (source.base_address or '') + \
                row.get('thumb', '')
            row['item_url'] = row.get('url', '')
            row['item_published'] = row.get('published_on', '')
            result.append(row)
            c += 1
            if c > count:
                break

        return result

    def children(self):
        count = self.data.get('count', 6)
        sources = self.get_sources()

        result = []
        for source in sources:
            if source.portal_type == "Sparql":
                result.extend(self._extract_sparql_data(source, count))
            elif source.portal_type == 'ElasticSearch':
                result.extend(self._extract_es_data(source, count))

        return result

    # def populate_with_object(self, obj):
    #     PersistentCoverTile.populate_with_object(self, obj)
    #
    #     if obj.portal_type not in self.accepted_ct():
    #         return
    #
    #     data = {
    #         'title': safe_unicode(obj.Title()),
    #         'uuid': IUUID(obj),
    #     }
    #     data_mgr = ITileDataManager(self)
    #     data_mgr.set(data)

    def is_empty(self):
        return not (self.data.get('uuid', None))

    def _to_dict(self, rows, cols):
        """ Packs a sparql result into a listing of dicts
        """
        res = []
        for row in rows:
            l = {}
            for i, c in enumerate(cols):
                l[c] = row[i]
            res.append(l)

        return res

    def format_date(self, ds):
        """ Convert a (possible) sparql literal to DateTime
        """
        if str(ds) == "None":
            return None
        try:
            return DateTime(str(ds))
        except Exception:
            logger.exception("Error while parsing date from sparql")
            return None


class DavizGridListingTile(DavizListingTile):
    """ Daviz-in-a-grid listing tile
    """

    index = ViewPageTemplateFile('pt/daviz_grid_listing.pt')
    cell_tpl = ViewPageTemplateFile('pt/daviz_cell.pt')

    short_name = u'Daviz Grid'


class DavizSingleRowListingTile(DavizListingTile):
    """ Daviz in a singele row listing tile
    """

    index = ViewPageTemplateFile('pt/daviz_singlerow_listing.pt')
    cell_tpl = ViewPageTemplateFile('pt/daviz_cell.pt')

    short_name = "Visualizations Row"


class IElasticSearchTile(IListingTile):
    """
    """

    # uuid = RelationChoice(
    #     title=u"Linked Source",
    #     source=UUIDSourceBinder(
    #         portal_type="ElasticSearch",
    #     ),
    #     required=False,
    # )
    uuid = Choice(
        title=u"Linked Source",
        vocabulary="bise.elasticsearch_vocabulary",
        required=False,
    )


class ElasticSearchBaseTile(PersistentCoverTile):
    """ ElasticSearch / Bise Catalogue Teaser tile
    """
    implements(IElasticSearchTile)

    def title(self):
        return self.data.get('title', 'Missing tile title')

    def children(self):
        uuid = self.data.get('uuid')
        if not uuid:
            return []
        source = uuidToObject(uuid)
        if not source:
            return []

        data = {}
        text = source.get_cached_results()
        if text:
            data = json.loads(text)
        else:
            return []

        try:
            rows = [x['_source']
                    for x in data.get('hits', {}).get('hits')]
        except KeyError:
            return []

        return rows

    def accepted_ct(self):
        """Return an empty list as no content types are accepted."""
        return ['ElasticSearch']

    def populate_with_object(self, obj):
        PersistentCoverTile.populate_with_object(self, obj)

        if obj.portal_type not in self.accepted_ct():
            return

        data = {
            'title': safe_unicode(obj.Title()),
            'uuid': IUUID(obj),
        }
        data_mgr = ITileDataManager(self)
        data_mgr.set(data)

    def is_empty(self):
        return not (self.data.get('uuid', None))

    def get_sources(self):
        uuid = self.data.get('uuid')
        if not uuid:
            return []
        source = uuidToObject(uuid)
        if not source:
            logger.warning("Could not find object with uuid %s", uuid)
        return [source]


class ElasticSearchTeaserTile(ElasticSearchBaseTile):
    """ ElasticSearch / Bise Catalogue Teaser tile
    """

    index = ViewPageTemplateFile('pt/es_teaser.pt')
    short_name = "Catalogue Teaser"


class ElasticSearchListingTile(ElasticSearchBaseTile):
    """ ElasticSearch / Bise Catalogue Teaser tile
    """

    index = ViewPageTemplateFile('pt/es_listing.pt')
    short_name = "Catalogue Listing"

    def get_url(self, obj):
        # try different strategies to get the source url from the catalogue
        # info
        source = self.get_sources()[0]
        base = source.base_address
        fallback = 'http://catalogue.biodiversity.europa.eu'

        strategies = [
            lambda o: o['url'],
            lambda o: o['source_url'],
            lambda o: (base or '') + obj['file_name'],
            lambda o: fallback + obj['file_name'],
        ]
        for (i, s) in enumerate(strategies):
            try:
                val = s(obj)
                if val:
                    return val
            except KeyError:
                continue

        return ""

    def get_title(self, obj):
        if 'title' in obj:
            return obj['title']
        if 'name' in obj:
            return obj['name']
