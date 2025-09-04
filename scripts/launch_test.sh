#!/bin/bash

RESLUT_FOLDER=test_results
DELAY_BEFORE_TESTS_IN_SECONDS=120

# Create folder to store test results
echo "Create test resutl folder"
mkdir -p $RESLUT_FOLDER

# # Start docker all services
# echo "Starting all the services"
# docker-compose up -d --build --force-recreate

# # Waiting for all services to be up
# # TODO: Should be made using a ping or a request
# echo "Waiting for all services to be up ($DELAY_BEFORE_TESTS_IN_SECONDS s)..."
# sleep $DELAY_BEFORE_TESTS_IN_SECONDS

# Execute api-minio tests
echo "Executing api-minio tests"
docker exec api-minio pip install --break-system-packages -r requirements/dev.txt && \
docker cp src/api-minio/test/test.sh api-minio:/usr/local/bin/test.sh  && \
docker exec api-minio chown root:root /usr/local/bin/test.sh  && \
docker exec api-minio chmod +x /usr/local/bin/test.sh  && \
docker exec api-minio test.sh  && \
docker cp api-minio:/app/test_result.xml $RESLUT_FOLDER/api-minio_test_result.xml  && \
docker cp api-minio:/app/test_coverage.xml $RESLUT_FOLDER/api-minio_test_coverage.xml

# # Shutting down services
# echo "Shutting down services"
# docker-compose down