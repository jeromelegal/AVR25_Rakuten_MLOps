#!/bin/bash

SUFFIX="$1"
RESULT_FOLDER=test_results
CONTAINER_NAME="api-minio$SUFFIX"

# Create folder to store test results
echo "Create test result folder"
mkdir -p $RESULT_FOLDER

# Execute api-minio tests
echo "Executing api-minio tests in container $CONTAINER_NAME"
docker exec $CONTAINER_NAME pip install --break-system-packages -r requirements/dev.txt && \
docker cp src/api-minio/test/test.sh $CONTAINER_NAME:/usr/local/bin/test.sh  && \
docker exec $CONTAINER_NAME chown root:root /usr/local/bin/test.sh  && \
docker exec $CONTAINER_NAME chmod +x /usr/local/bin/test.sh  && \
docker exec $CONTAINER_NAME test.sh  && \
docker cp $CONTAINER_NAME:/app/test_result.xml $RESULT_FOLDER/api-minio_test_result.xml  && \
docker cp $CONTAINER_NAME:/app/test_coverage.xml $RESULT_FOLDER/api-minio_test_coverage.xml
