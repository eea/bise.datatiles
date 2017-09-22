""" A content type to define an cache an ElasticSearch query
"""

import datetime
import json
import logging

import DateTime
import pytz
import requests
# from eea.cache import cache
from plone import namedfile
from plone.app.async.interfaces import IAsyncService
from plone.directives import dexterity, form
from plone.namedfile.file import NamedFile
from plone.uuid.interfaces import IUUID
from zope import schema
from zope.component import getUtility
from zope.interface import implements

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
    refresh_rate = schema.Choice(
        title=u"Refresh rate",
        description=u"How often should the results be fetched",
        required=True,
        default=u'Weekly',
        values=['Once', 'Hourly', 'Daily', 'Weekly']
    )


def cache_key(fun, context):
    return IUUID(context)


class ElasticSearch(dexterity.Item):
    implements(IElasticSearch)

    def get_cached_results(self):
        if getattr(self, 'cached_results', None):
            return getattr(self.cached_results, 'data')

        # return self._cached_results()

    # @cache(cache_key, lifetime=60*60*8)     # 8 hours cache
    # def _cached_results(self):
    #     if not (self.endpoint and self.query):
    #         return
    #
    #     logger.info("Updating results cache for %s", self.absolute_url())
    #     try:
    #         resp = requests.post(
    #             self.endpoint,
    #             json=json.loads(self.query),
    #             timeout=2
    #         )
    #     except Exception, e:
    #         logger.error("Error in updating results for ES: %s", e)
    #         return ""
    #
    #     return resp.text
    #
    def updateLastWorkingResults(self):
        self.modification_date = DateTime.DateTime()
        resp = requests.post(
            self.endpoint,
            json=json.loads(self.query),
            timeout=2
        )
        self.cached_results = NamedFile(data=resp.text,
                                        contentType='text/x-json',
                                        filename=u'cached_data.json')
        # self._p_changed = True


def async_update_cached_data(obj, modification_date):
    # We want to handle the case when multiple async jobs are created.
    # the jobs that are already created will silently die

    if not (obj.modification_date == modification_date):
        return

    obj.updateLastWorkingResults()

    refresh_rate = getattr(obj, "refresh_rate", "Weekly")

    # Refresh hourly if no results are found

    if refresh_rate == 'Once':
        if obj.get_cached_results():
            return
        refresh_rate == 'Hourly'

    before = datetime.datetime.now(pytz.UTC)
    delay = before + datetime.timedelta(hours=1)

    if refresh_rate == "Daily":
        delay = before + datetime.timedelta(days=1)

    if refresh_rate == "Weekly":
        delay = before + datetime.timedelta(weeks=1)

    if refresh_rate != "Once":
        async = getUtility(IAsyncService)
        async.queueJobWithDelay(None,
                                delay,
                                async_update_cached_data,
                                obj,
                                modification_date,
                                )


def handle_es_change(obj, event):
    """ Update last working results when ElasticSearch is added or modified """

    async = getUtility(IAsyncService)
    logger.info("Queued job to async update %r", obj)

    async.queueJob(async_update_cached_data,
                   obj,
                   obj.modification_date
                   )
