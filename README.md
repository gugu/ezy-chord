# ezy-chord
Celery chord implementation, which works with eventlet

## Usage

In your app initializer:

```
app = Celery('myapp')
app.ezy_chord = EzyChord(app)
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
