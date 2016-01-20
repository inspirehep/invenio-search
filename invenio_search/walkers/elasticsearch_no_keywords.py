# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015, 2016 CERN.
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

"""Implement AST convertor to Elastic Search DSL."""

from invenio_query_parser.ast import (
    AndOp, DoubleQuotedValue, EmptyQuery,
    GreaterEqualOp, GreaterOp, Keyword,
    KeywordOp, LowerEqualOp, LowerOp,
    NotOp, OrOp, RangeOp, RegexValue,
    SingleQuotedValue, Value, ValueQuery
)
from invenio_query_parser.visitor import make_visitor


class QueryHasKeywords(Exception):
    pass


class ElasticSearchNoKeywordsDSL(object):

    """Implement visitor to create Elastic Search DSL for queries that don't include keywords."""

    visitor = make_visitor()

    def __init__(self):
        self.values = ""

    @visitor(KeywordOp)
    def visit(self, node, left, right):
        raise QueryHasKeywords()

    @visitor(AndOp)
    def visit(self, node, left, right):
        return {
            "multi_match": {
                "message": {
                    "query": str.strip(str(self.values)),
                    "operator": "or",
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
                        "doi^10"]}}}

    @visitor(OrOp)
    def visit(self, node, left, right):
        pass

    @visitor(NotOp)
    def visit(self, node, op):
        pass

    @visitor(ValueQuery)
    def visit(self, node, op):
        return {
            "multi_match": {
                "message": {
                    "query": str.strip(str(self.values)),
                    "operator": "or",
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
                        "doi^10"]}}}

    @visitor(Keyword)
    def visit(self, node):
        pass

    @visitor(Value)
    def visit(self, node):
        self.values += node.value + ' '

    @visitor(SingleQuotedValue)
    def visit(self, node):
        self.values += node.value + ' '

    @visitor(DoubleQuotedValue)
    def visit(self, node):
        self.values += node.value + ' '

    @visitor(RegexValue)
    def visit(self, node):
        pass

    @visitor(RangeOp)
    def visit(self, node, left, right):
        pass

    @visitor(EmptyQuery)
    def visit(self, node):
        return {
            "match_all": {}
        }

    @visitor(GreaterOp)
    def visit(self, node, value_fn):
        pass

    @visitor(LowerOp)
    def visit(self, node, value_fn):
        pass

    @visitor(GreaterEqualOp)
    def visit(self, node, value_fn):
        pass

    @visitor(LowerEqualOp)
    def visit(self, node, value_fn):
        pass
    # pylint: enable=W0612,E0102
