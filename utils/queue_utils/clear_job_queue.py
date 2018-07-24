# -*- coding: utf-8 -*-

import os, pprint
import redis, rq


queue_name = 'usep'
q = rq.Queue( queue_name, connection=redis.Redis() )

print( '- initial number of jobs in queue `%s`: %s' % (queue_name, len(q.jobs)) )

for job in q.jobs:
    job_d = {
        'args': job._args,
        'kwargs': job._kwargs,
        'function': job._func_name,
        'description': job.description,
        'dt_created': job.created_at,
        'dt_enqueued': job.enqueued_at,
        'dt_ended': job.ended_at,
        'origin': job.origin,
        'id': job._id,
        'traceback': job.exc_info
        }
    print( '- job info...' )
    pprint.pprint( job_d )
    job.delete()
    print( '- deleted' )
    print( '---' )

print( '- current number of jobs in queue `%s`: %s' % (queue_name, len(q.jobs)) )
