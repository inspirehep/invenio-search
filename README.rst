..
    This file is part of Invenio.
    Copyright (C) 2015-2018 CERN.

    Invenio is free software; you can redistribute it and/or modify it
    under the terms of the MIT License; see LICENSE file for more details.

================
 Invenio-Search
================

To run the test suite locally:

.. code-block:: console

    pyenv virtualenv search
    pyenv activate search
    pip install -e ".[tests,opensearch2]"
    ./run-tests.sh
