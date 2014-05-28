#!/bin/bash


USEP_WORKER_NAME=usep_worker_$RANDOM
USEP_WORKER_LOG_FILENAME=$usep_gh__LOG_DIR/$USEP_WORKER_NAME.log
USEP_QUEUE_NAME="usep"

echo "worker name: " $USEP_WORKER_NAME
echo "log filename: " $USEP_WORKER_LOG_FILENAME
echo "queue name: " $USEP_QUEUE_NAME

rqworker --name $USEP_WORKER_NAME $USEP_QUEUE_NAME >> $USEP_WORKER_LOG_FILENAME 2>&1 &
# rqworker --name $USEP_WORKER_NAME $USEP_QUEUE_NAME
