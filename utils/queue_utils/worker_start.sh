#!/bin/bash

# Note:
# When an app setting is changed for code called by a worker, restart the worker from the `usep_github_handler_stuff` dir.
#
# Example...
#
# $ ps aux | grep "rq"
# (to find out worker PID)
#
# $ cd /path/to/usep_github_handler_stuff/
# $ source ./env_usep_gh/bin/activate
# $ kill PID
# $ bash ./usep_gh_handler_app/utils/queue_utils/worker_start.sh
#
# $ ps aux | grep "rq"
# (to confirm new worker is running)


USEP_WORKER_NAME=usep_worker_$RANDOM
# USEP_WORKER_LOG_FILENAME=$usep_gh__LOG_DIR/$USEP_WORKER_NAME.log
USEP_WORKER_LOG_FILENAME=$usep_gh__LOG_DIR/usep_worker.log
USEP_QUEUE_NAME="usep"

echo "worker name: " $USEP_WORKER_NAME
echo "log filename: " $USEP_WORKER_LOG_FILENAME
echo "queue name: " $USEP_QUEUE_NAME

# rqworker --name $USEP_WORKER_NAME --pid /var/run/rq_usep/PID $USEP_QUEUE_NAME >> $USEP_WORKER_LOG_FILENAME 2>&1 &
rqworker --name $USEP_WORKER_NAME $USEP_QUEUE_NAME >> $USEP_WORKER_LOG_FILENAME
