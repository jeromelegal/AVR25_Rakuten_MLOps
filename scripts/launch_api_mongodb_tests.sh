#!/bin/bash

SUFFIX="$1"
RESULT_FOLDER=test_results
CONTAINER_NAME="api-mongodb$SUFFIX"

# Create folder to store test results
echo "Create test result folder"
mkdir -p $RESULT_FOLDER

# Execute api-mongodb tests
echo "Executing api-mongodb tests"
docker exec api-mongodb pip3 install --break-system-packages pytest-cov && \
docker exec api-mongodb python3 -m pytest \
        --junit-xml=test_result.xml \
        --cov=/app/api \
        --cov-report xml:test_coverage.xml \
        --cov-report term \
        --rootdir /app && \
docker cp api-mongodb:/app/test_result.xml $RESULT_FOLDER/api-mongodb_test_result.xml  && \
docker cp api-mongodb:/app/test_coverage.xml $RESULT_FOLDER/api-mongodb_test_coverage.xml