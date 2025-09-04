#!/bin/bash

DELAY_BEFORE_TESTS_IN_SECONDS=120

# Waiting for all services to be up
# TODO: Should be made using a ping or a request
echo "Waiting for all services to be up ($DELAY_BEFORE_TESTS_IN_SECONDS s)..."
sleep $DELAY_BEFORE_TESTS_IN_SECONDS