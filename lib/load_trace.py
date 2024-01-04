import pickle
from pathlib import Path
from lib.trace import Trace

def save(obj, filename):
    with open(filename, 'wb') as handle:
        pickle.dump(obj, handle, protocol=pickle.HIGHEST_PROTOCOL)

def load(filename):
    with open(filename, 'rb') as handle:
        return pickle.load(handle)

def save_trace(trace: Trace, dir):
    path = Path(dir)
    path.mkdir(parents=True, exist_ok=True)
    save(trace.candidates, path / "candidates")
    save(trace.customers_by_route, path / "routes")

def load_trace(dir) -> Trace:
    path = Path(dir)
    return Trace(
        candidates=load(path / "candidates"),
        customers_by_route=load(path / "routes"),
    )
