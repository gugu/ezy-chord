# ezy-chord
Celery chord implementation, which works with eventlet. 

## Why?

In celery 4 chord implementation is completely broken. It uses Redis PUBSUB functionality, which does not work with 
eventlet/gevent

## How does it work?

1. When you create a chord, it runs all subtasks at once and stores number of subtasks in Redis
2. Each time you complete a subtask you need to call `chord_check` method, which will store subtask result in Redis 
and decrement task counter
3. When last subtask is completed and task counter is 0, `chord_check` runs collection task and sends all results to 
this task
 

## Usage

In your app initializer:

```python
import redis
from ezy_chord import EzyChord
from celery import Celery

app = Celery('myapp')
app.ezy_chord = EzyChord(
    app,
    redis_instance=redis.StrictRedis(
        password='test',
        host='localhost',
        port=6379,
        db=0)
)
```

In your tasks.py:

```python

from myceleryapp import app

@app.task(bind=True)
def add(self, chord_id, first, second):
    res = first + second
    # You need to call chord_check in the end of your subtask
    app.ezy_chord.chord_check(chord_id, self.request.id, res)
    return res


@app.task(bind=True)
def my_task(self):
    r = app.ezy_chord.chord_init(
        [
            add.s(1, 2),
            add.s(3, 4),
            add.s(5, 6),
        ], next_task='myceleryapp.tasks.sum_task',
        next_task_kwargs=dict(initial=5))
        
@app.task(bind=True)
def sum_task(self, numbers, initial):
    return initial + sum(numbers)
```
