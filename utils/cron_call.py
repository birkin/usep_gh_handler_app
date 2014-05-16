# -*- coding: utf-8 -*-

""" Triggers git pull job.
    Call like: /path/to/env/bin/python2.6 /path/to/usep_gh_handler_app/utils/cron_call.py
    Note that output is not logged to the normal application log, but to the rqworker log (assuming one exists). """

import redis, rq


q = rq.Queue( u'usep', connection=redis.Redis() )
job = q.enqueue_call (
    func=u'usep_gh_handler_app.utils.processor.run_call_git_pull',
    kwargs = {}
    )
