# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2014, 2015, 2016 CERN.
#
# Invenio is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""Search engine API."""

from __future__ import unicode_literals

from flask import current_app

from flask_login import current_user

from elasticsearch.helpers import scan

from invenio_base.globals import cfg
from invenio_base.helpers import unicodifier

import pypeg2

from werkzeug.utils import cached_property

from .utils import parser, query_enhancers, query_walkers, search_walkers
from .walkers.elasticsearch_no_keywords import ElasticSearchNoKeywordsDSL
from .walkers.elasticsearch_no_keywords import QueryHasKeywords
from .walkers.match_unit import MatchUnit
from .walkers.terms import Terms


class Query(object):

    """Search engine implemetation.

    .. versionadded:: 2.1
       New search and match API.
    """

    def __init__(self, query):
        """Initialize with search query."""
        self._query = unicodifier(query)

    @cached_property
    def query(self):
        """Parse query string using given grammar."""
        try:
            tree = pypeg2.parse(self._query, parser(), whitespace="")
        except SyntaxError:
            from invenio_query_parser.ast import MalformedQuery
            return MalformedQuery("")
        for walker in query_walkers():
            tree = tree.accept(walker)
        return tree

    def search(self, user_info=None, collection=None, enhance=True, **kwargs):
        """Search records."""
        user_info = user_info or current_user
        # Enhance query first
        query = self.query
        current_app.logger.debug(query)

        if enhance:
            for enhancer in query_enhancers():
                query = enhancer(query, user_info=user_info,
                                 collection=collection)
        try:
            walker = ElasticSearchNoKeywordsDSL()
            query.accept(walker)
            query = {
                "multi_match": {
                    "query": self._query,
                    "zero_terms_query": "all",
                    "fields": [
                        "title^3",
                        "title.raw^10",
                        "abstract^2",
                        "abstract.raw^4",
                        "author^10",
                        "author.raw^15",
                        "reportnumber^10",
                        "eprint^10",
                        "doi^10"]}}
        except QueryHasKeywords:
            for walker in search_walkers():
                query = query.accept(walker)

        index = cfg["SEARCH_ELASTIC_COLLECTION_INDEX_MAPPING"].get(
            collection,
            cfg["SEARCH_ELASTIC_DEFAULT_INDEX"]
        )

        return Results(query, index=index)

    def match(self, record, user_info=None):
        """Return True if record match the query."""
        return self.query.accept(MatchUnit(record))

    def terms(self, keywords=None):
        """Return list of terms for given keywords in query pattern."""
        return self.query.accept(Terms(keywords=keywords))


class Results(object):

    def __init__(self, query, index=None, doc_type=None, **kwargs):
        self.body = {
            'from': 0,
            'size': 10,
            'query': query,
        }
        self.body.update(kwargs)

        self.index = index
        self.doc_type = doc_type or 'record'

        self._results = None

    @property
    def recids(self):
        from intbitset import intbitset
        from invenio_ext.es import es
        results = scan(
            es,
            query={
                'fields': [],
                'query': self.body.get("query")
            },
            index=self.index,
            doc_type=self.doc_type,
        )
        return intbitset([int(r['_id']) for r in results])

    def _search(self):
        from invenio_ext.es import es

        if self._results is None:
            if current_app.debug:
                import json
                json_body = json.dumps(self.body, indent=2)
                current_app.logger.debug(
                    "index: {0} - doc_type: {1} - query: {2}".format(
                        self.index,
                        self.doc_type,
                        json_body
                    )
                )
            self._results = es.search(
                index=self.index,
                doc_type=self.doc_type,
                body=self.body,
            )
        return self._results

    def records(self):
        from invenio_records.api import Record
        return [Record(r['_source']) for r in self._search()['hits']['hits']]

    def __len__(self):
        return self._search()['hits']['total']
