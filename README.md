# Projet Othello — dev A setup

Colab: upload the .py files (or clone repo) then:
```python
import sys; sys.path.insert(0,'/content')
from engine import initial_state, perft
from tests import test_perft; test_perft()
```

Run tests: `python tests.py`
Play: `python cli.py mixed`