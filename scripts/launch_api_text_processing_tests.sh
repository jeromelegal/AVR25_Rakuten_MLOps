#!/bin/bash

RESLUT_FOLDER=test_results

# Create folder to store test results
echo "Create test resutl folder"
mkdir -p $RESLUT_FOLDER

# Execute api-text-processing tests
echo "Executing api-text-processing tests"
docker exec api-text-processing pip3 install --break-system-packages pytest-cov && \
docker exec api-text-processing python3 -m pytest \
        --junit-xml=test_result.xml \
        --cov=/app/api \
        --cov-report xml:test_coverage.xml \
        --cov-report term \
        --rootdir /app && \
docker cp api-text-processing:/app/test_result.xml $RESULT_FOLDER/api-text-processing_test_result.xml  && \
docker cp api-text-processing:/app/test_coverage.xml $RESULT_FOLDER/api-text-processing_test_coverage.xml