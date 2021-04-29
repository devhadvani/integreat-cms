#!/bin/bash

# This script imports test data into the database.

# Import utility functions
source "$(dirname "${BASH_SOURCE[0]}")/_functions.sh"

require_database

deescalate_privileges pipenv run integreat-cms-cli loaddata "${BASE_DIR}/src/cms/fixtures/test_data.json"
echo "✔ Imported test data" | print_success
