#!/usr/bin/env bash
# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2020 CERN.
# Copyright (C) 2022 Graz University of Technology.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

# Quit on errors
set -o errexit

# Quit on unbound symbols
set -o nounset

# Always bring down docker services
function cleanup() {
    eval "$(docker-services-cli down --env)"
}
trap cleanup EXIT

echo "PostgreSQL version: ${POSTGRESQL_VERSION:-14}"
echo "OpenSearch version: ${OPENSEARCH_VERSION:-3.2.0}"

eval "$(
  POSTGRESQL_VERSION="${POSTGRESQL_VERSION:-14}" \
  OPENSEARCH_VERSION="${OPENSEARCH_VERSION:-3.2.0}" \
  docker-services-cli up --db "${DB:-postgresql14}" --search "${SEARCH:-opensearch}" --env
)"
docker ps --format 'table {{.Names}}\t{{.Image}}'
python -m pytest
tests_exit_code=$?
exit "$tests_exit_code"
