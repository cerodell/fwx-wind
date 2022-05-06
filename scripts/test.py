import context
from pathlib import Path

from context import data_dir

ubc_winds = ["%.2d" % i for i in range(1, 21)]

for id in ubc_winds:
    print(id)
    make_dir = Path(str(data_dir) + f"/wind{id}")
    make_dir.mkdir(parents=True, exist_ok=True)
