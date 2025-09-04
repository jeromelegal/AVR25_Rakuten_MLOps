#!/bin/bash

RESULT_FOLDER=test_results

# Execute api-minio tests
echo "Executing api-minio tests"
docker exec api-minio pip install --break-system-packages -r requirements/dev.txt && \
docker cp src/api-minio/test/test.sh api-minio:/usr/local/bin/test.sh  && \
docker exec api-minio chown root:root /usr/local/bin/test.sh  && \
docker exec api-minio chmod +x /usr/local/bin/test.sh  && \
docker exec api-minio test.sh  && \
docker cp api-minio:/app/test_result.xml $RESULT_FOLDER/api-minio_test_result.xml  && \
docker cp api-minio:/app/test_coverage.xml $RESULT_FOLDER/api-minio_test_coverage.xml
