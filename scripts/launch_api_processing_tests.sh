#!/bin/bash

SUFFIX="$1"
RESULT_FOLDER=test_results
CONTAINER_NAME="api-processing$SUFFIX"
# Create folder to store test results
echo "Create test result folder"
mkdir -p $RESULT_FOLDER

# Execute api-processing tests
echo "Executing api-processing tests in container $CONTAINER_NAME"
docker exec $CONTAINER_NAME pip3 install --break-system-packages pytest-cov && \
docker exec $CONTAINER_NAME pip3 install --break-system-packages -r requirements/dev.txt && \
docker exec $CONTAINER_NAME python3 -m pytest \
        --junit-xml=test_result.xml \
        --cov=/app/api \
        --cov-report xml:test_coverage.xml \
        --cov-report term \
        --rootdir /app && \
docker cp $CONTAINER_NAME:/app/test_result.xml $RESULT_FOLDER/api-processing_test_result.xml  && \
docker cp $CONTAINER_NAME:/app/test_coverage.xml $RESULT_FOLDER/api-processing_test_coverage.xml