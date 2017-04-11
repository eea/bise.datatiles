""" A content type to define an cache an ElasticSearch query
"""

from eea.cache import cache
from plone import namedfile
from plone.directives import dexterity
from plone.directives import form
from plone.uuid.interfaces import IUUID
from zope import schema
from zope.interface import implements
import json
import logging
import requests

logger = logging.getLogger('bise.datatiles.elasticsearch')


class IElasticSearch(form.Schema):
    """ ElasticSearch precookedsearch content type
    """

    endpoint = schema.TextLine(title=u"ES Endpoint URL",
                               required=True)

    query = schema.Text(
        title=u'ElasticSearch Query in JSON format',
        required=True,
    )
    base_address = schema.TextLine(title=u"Base address for domain-free URLs ",
                                   required=True)

    form.omitted('cached_results')
    cached_results = namedfile.field.NamedBlobFile(title=u"Cached results",
                                                   required=False)


def cache_key(fun, context):
    return IUUID(context)


class ElasticSearch(dexterity.Item):
    implements(IElasticSearch)

    def get_cached_results(self):
        return self._cached_results()

    @cache(cache_key, lifetime=60*60*8)     # 8 hours cache
    def _cached_results(self):
        if not (self.endpoint and self.query):
            return

        logger.info("Updating results cache for %s", self.absolute_url())
        try:
            resp = requests.post(
                self.endpoint,
                json=json.loads(self.query),
                timeout=2
            )
        except Exception, e:
            logger.error("Error in updating results for ES: %s", e)
            return ""

        return resp.text


def handle_es_change(obj, event):
    return
    # obj.precache_data()


# import DateTime
# from plone.app.async.interfaces import IAsyncService
# from zope.component import getUtility
#
# def async_update_cached_data(obj):
#     obj.precache_data()
# def es_added_or_modified(obj, evt):
#     async = getUtility(IAsyncService)
#
#     obj.scheduled_at = DateTime.DateTime()
#
#     async.queueJob(async_update_cached_data, obj)
