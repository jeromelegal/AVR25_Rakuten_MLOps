#!/bin/bash

RESULT_FOLDER=test_results

# Execute api-gateway tests
echo "Executing api-gateway tests"
docker exec api-gateway pip3 install --break-system-packages pytest-cov && \
docker exec api-gateway python3 -m pytest \
        --junit-xml=test_result.xml \
        --cov=/app/api \
        --cov-report xml:test_coverage.xml \
        --cov-report term \
        --rootdir /app && \
docker cp api-gateway:/app/test_result.xml $RESULT_FOLDER/api-gateway_test_result.xml  && \
docker cp api-gateway:/app/test_coverage.xml $RESULT_FOLDER/api-gateway_test_coverage.xml