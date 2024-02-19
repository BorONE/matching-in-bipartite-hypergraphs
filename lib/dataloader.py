import pandas as pd
from pathlib import Path
from collections import Counter

from ast import literal_eval


DEBUG = False


def dict_wrap(trace, routes):
    """
    For given `trace` converts 'chosen_for_proposition_flg' to bool
    For given `routes` converts 'claim_segment_uuid_list' to tuple, drops_duplicates
    """

    result = {'trace': trace.copy(deep=True), 'routes': routes.copy(deep=True)}

    result['trace'].chosen_for_proposition_flg = trace.chosen_for_proposition_flg.apply(lambda f : bool(f))
    
    result['routes'].claim_segment_uuid_list = routes.claim_segment_uuid_list.apply(lambda l : tuple(literal_eval(l)))
    result['routes'].drop_duplicates(inplace=True)

    if DEBUG:
        route_ids = trace[trace.chosen_for_proposition_flg].route_id
        candidates_by_route = {row.route_id: set(row.claim_segment_uuid_list) for _, row in routes.iterrows()}

        counter = Counter()
        for route_id in route_ids:
            counter.update(candidates_by_route[route_id])
        assert len(counter.values()) == 0 or max(counter.values()) == 1

    return result


def load_data(path, wrap=dict_wrap):
    data = {}

    for path in list(Path(path).iterdir()):
        data[path.name] = wrap(
            trace=pd.read_csv(path / 'trace.csv', index_col=0),
            routes=pd.read_csv(path / 'routes.csv', index_col=0),
        )
    
    return data


def load_synthetic(path, wrap=dict_wrap):
    data = {}

    csv = pd.read_csv(path)
    csv.rename(columns={'assigned_flg': 'chosen_for_proposition_flg'}, inplace=True)

    for trace_id in csv.trace_id.unique():
        trace_entry = csv[csv.trace_id == trace_id]
        data[trace_id] = wrap(
            trace=trace_entry[['candidate_id', 'route_id', 'chosen_for_proposition_flg', 'score']],
            routes=trace_entry[['route_id', 'claim_segment_uuid_list']],
        )

    return data
