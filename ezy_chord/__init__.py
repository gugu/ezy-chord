import json
from uuid import uuid4
import six


def _to_string(data):
    return data if isinstance(data, six.string_types) else data.decode('utf-8')


class EzyChord(object):
    def __init__(self, app, redis_instance):
        self.app = app
        self.redis = redis_instance

    def chord_init(self, tasks, next_task=None, next_args=None, next_task_kwargs=None, **options):
        if next_args is None:
            next_args = []
        if next_task_kwargs is None:
            next_task_kwargs = {}

        chord_id = str(uuid4())
        redis = self.redis
        redis.set(chord_id + ".count", len(tasks))
        redis.set(chord_id + ".completed", 0)
        if next_task:
            redis.set(chord_id + ".next", next_task)
            redis.set(chord_id + ".next_args", json.dumps(next_args))
            redis.set(chord_id + ".next_kwargs", json.dumps(next_task_kwargs))
        for task in tasks:
            task_id = str(uuid4())
            redis.sadd(chord_id + ".tasks_ids", task_id)
            task.apply_async(args=[chord_id], task_id=task_id, **options)
        redis.expire(chord_id + ".tasks_ids", 3600)
        return chord_id

    def chord_check(self, chord_id, task_id, result):
        if not chord_id:
            return
        assert task_id
        redis = self.redis
        total_count = redis.get(chord_id + ".count")
        if total_count is None:
            return
        if not redis.srem(chord_id + ".tasks_ids", task_id):
            return
        redis.lpush(chord_id + ".results", json.dumps(result))
        completed_count = redis.incr(chord_id + ".completed")
        if int(total_count) == completed_count:
            next_task_raw = redis.get(chord_id + ".next")
            if next_task_raw:
                next_task = _to_string(next_task_raw)
                next_args_raw = redis.get(chord_id + ".next_args")
                next_args = json.loads(_to_string(next_args_raw))
                next_kwargs_raw = redis.get(chord_id + ".next_kwargs")
                next_kwargs = json.loads(_to_string(next_kwargs_raw))
                results = list(map(json.loads, map(_to_string, redis.lrange(chord_id + ".results", 0, -1))))
                self.app.send_task(next_task, args=[results] + next_args, kwargs=next_kwargs)
                redis.delete(
                    chord_id + ".count", chord_id + ".completed", chord_id + ".results",
                    chord_id + ".next", chord_id + ".next_args", chord_id + ".next_kwargs")
