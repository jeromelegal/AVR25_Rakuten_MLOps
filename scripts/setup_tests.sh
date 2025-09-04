#!/bin/bash

RESLUT_FOLDER=test_results
DELAY_BEFORE_TESTS_IN_SECONDS=120

# Create folder to store test results
echo "Create test resutl folder"
mkdir -p $RESLUT_FOLDER

# Waiting for all services to be up
# TODO: Should be made using a ping or a request
echo "Waiting for all services to be up ($DELAY_BEFORE_TESTS_IN_SECONDS s)..."
sleep $DELAY_BEFORE_TESTS_IN_SECONDS