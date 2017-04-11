from Products.CMFCore.utils import getToolByName
from zope.interface import alsoProvides
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleVocabulary, SimpleTerm
from zope.site.hooks import getSite


def datasource_vocabulary_factory(ptype):
    def factory(context):
        try:
            catalog = getToolByName(context, 'portal_catalog')
        except AttributeError:
            catalog = getToolByName(getSite(), 'portal_catalog')

        brains = catalog(portal_type=ptype)
        terms = [SimpleTerm(b.UID, b.UID, b.Title) for b in brains]

        return SimpleVocabulary(terms)

    return factory


sparql_vocabulary = datasource_vocabulary_factory("Sparql")
alsoProvides(sparql_vocabulary, IVocabularyFactory)

elasticsearch_vocabulary = datasource_vocabulary_factory('ElasticSearch')
alsoProvides(elasticsearch_vocabulary, IVocabularyFactory)

datasource_vocabulary = datasource_vocabulary_factory(['Sparql',
                                                       'ElasticSearch'])
alsoProvides(datasource_vocabulary, IVocabularyFactory)
