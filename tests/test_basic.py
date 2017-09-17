from uuid import uuid4

from ezy_chord import EzyChord
from unittest import TestCase
from mock import Mock, ANY


class FakeApp(object):
    pass


class FakeRedis(object):
    def __init__(self):
        self.data = {}

    def get(self, key):
        return self.data.get(key)

    def set(self, key, value):
        self.data[key] = value

    def sadd(self, key, value):
        self.data.setdefault(key, set())
        self.data[key].add(value)

    def srem(self, key, value):
        self.data.setdefault(key, set())
        if value not in self.data[key]:
            return
        self.data[key].remove(value)
        if not self.data[key]:
            del self.data[key]
        return value

    def expire(self, key, interval):
        pass

    def lpush(self, key, value):
        self.data.setdefault(key, [])
        self.data[key].append(value)
        return value

    def lrange(self, key, start, stop):
        self.data.setdefault(key, [])
        return self.data[key][start:stop] + [self.data[key][stop]]  # Redis includes last element

    def incr(self, key):
        self.data[key] += 1
        return self.data[key]

    def delete(self, *args):
        for key in args:
            del self.data[key]


class BasicTest(TestCase):
    def test_chord_init(self):
        app = Mock()
        redis_instance = FakeRedis()
        subtask1 = Mock()
        subtask2 = Mock()
        chord = EzyChord(app, redis_instance=redis_instance)
        subtasks = [subtask1.s(1, 2, 3), subtask2.s(1, 2, 4)]
        chord_id = chord.chord_init(subtasks, next_task='myapp.test_task')
        self.assertEqual(redis_instance.data[chord_id + '.count'], 2)
        self.assertEqual(redis_instance.data[chord_id + '.completed'], 0)
        self.assertEqual(redis_instance.data[chord_id + '.next'], 'myapp.test_task')
        self.assertEqual(redis_instance.data[chord_id + '.next_args'], '[]')
        self.assertEqual(redis_instance.data[chord_id + '.next_kwargs'], '{}')
        self.assertEqual(len(redis_instance.data[chord_id + '.tasks_ids']), 2)
        subtasks[0].apply_async.assert_called_once_with(args=[chord_id], task_id=ANY)
        subtasks[1].apply_async.assert_called_once_with(args=[chord_id], task_id=ANY)

    def test_chord_check(self):
        app = Mock()
        redis_instance = FakeRedis()
        chord_id = str(uuid4())
        task1_id = str(uuid4())
        task2_id = str(uuid4())
        redis_instance.data = {
            chord_id + '.count': 2,
            chord_id + '.completed': 0,
            chord_id + '.tasks_ids': {task1_id, task2_id}
        }
        chord = EzyChord(app, redis_instance=redis_instance)
        chord.chord_check(chord_id, task1_id, 5)
        self.assertEqual(redis_instance.data[chord_id + '.count'], 2)
        self.assertEqual(redis_instance.data[chord_id + '.completed'], 1)
        self.assertEqual(redis_instance.data[chord_id + '.tasks_ids'], {task2_id})
        self.assertEqual(redis_instance.data[chord_id + '.results'], ['5'])

    def test_chord_check_last_task(self):
        app = Mock()
        redis_instance = FakeRedis()
        chord_id = str(uuid4())
        task2_id = str(uuid4())
        redis_instance.data = {
            chord_id + '.count': 2,
            chord_id + '.completed': 1,
            chord_id + '.tasks_ids': {task2_id},
            chord_id + '.results': ['5'],
            chord_id + '.next': 'myapp.test_task',
            chord_id + '.next_args': '[7]',
            chord_id + '.next_kwargs': '{}',
        }
        chord = EzyChord(app, redis_instance=redis_instance)
        chord.chord_check(chord_id, task2_id, 6)
        self.assertEqual(redis_instance.data, {})
        app.send_task.assert_called_once_with('myapp.test_task', args=[[5, 6], 7], kwargs={})
