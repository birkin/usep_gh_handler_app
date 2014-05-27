# -*- coding: utf-8 -*-

import os, pprint
import redis, rq


queue_name = u'usep'
q = rq.Queue( queue_name, connection=redis.Redis() )

print u'- number of jobs in queue `%s`: %s' % ( queue_name, len(q.jobs) )

for job in q.jobs:
    job_d = {
        u'args': job._args,
        u'kwargs': job._kwargs,
        u'function': job._func_name,
        u'dt_created': job.created_at,
        u'dt_enqueued': job.enqueued_at,
        u'dt_ended': job.ended_at,
        u'origin': job.origin,
        u'id': job._id,
        u'traceback': job.exc_info
        }
    print u'- job info...'; pprint.pprint( job_d )
    print u'---'
