#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import redis
from bloom_filter import BloomFilter
import dill

reload(sys)
sys.setdefaultencoding('utf-8')


class Base(object):
    """Per-spider base queue class"""

    def __init__(self, task_id):
        self.task_id = task_id
        self._filter = BloomFilter(key=self.task_id)
        self._server = redis.StrictRedis()

    def __len__(self):
        """Return the length of the queue"""
        raise NotImplementedError

    def push(self, request):
        """Push a request"""
        raise NotImplementedError

    def pop(self):
        """Pop a request"""
        raise NotImplementedError

    def clear(self):
        """Clear queue/stack"""
        self.server.delete(self.key)


class PriorityQueue(Base):
    def push(self, request):
        score = -request.priority
        data = dill.dumps(request)
        if not request.duplicate_remove:
            self._server.execute_command('ZADD', self.task_id, score, data)
        else:
            if not self._filter.is_contains(data):
                self._server.execute_command('ZADD', self.task_id, score, data)
                self._filter.insert(data)

    def pop(self):
        pipe = self._server.pipeline()
        pipe.multi()
        pipe.zrange(self.task_id, 0, 0).zremrangebyrank(self.task_id, 0, 0)
        results, count = pipe.execute()
        if results:
            return dill.loads(results[0])
        else:
            return None

    def clear(self):
        self._server.delete(self.task_id)

    def __len__(self):
        return self._server.zcard(self.task_id)


if __name__ == '__main__':
    queue = PriorityQueue("test")
    print queue