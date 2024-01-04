import pandas as pd
from pathlib import Path
from tqdm import tqdm
from dataclasses import dataclass

from ast import literal_eval

@dataclass
class DataEntry:
    """
    trace: ['candidate_id', 'route_id', 'chosen_for_proposition_flg', 'score']
    routes: ['route_id', 'claim_segment_uuid_list']
    """
    trace: pd.DataFrame
    route: pd.DataFrame


# TODO DataEntry, tqdm
def load_data(path):
    data = {}

    for path in tqdm(list(Path(path).iterdir())):
        trace = pd.read_csv(path / 'trace.csv', index_col=0)
        routes = pd.read_csv(path / 'routes.csv', index_col=0)
        routes.claim_segment_uuid_list = routes.claim_segment_uuid_list.apply(literal_eval) # bc read_csv doesn't know how to read tuples

        data[path.name] = {'trace': trace, 'routes': routes}
    
    return data
