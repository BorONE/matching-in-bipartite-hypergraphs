from __future__ import annotations

import pandas as pd


TCandidateKey = str
TRouteKey = str
TCustomerKey = str


# TODO fancy/optimized keys


class Trace:
    def __init__(
        self,
        *,
        candidates: dict[TCandidateKey, dict[TRouteKey, float]] = {},
        customers_by_route: dict[TRouteKey, set[TCandidateKey]] = {},
        yandex_score: float = 0,
    ) -> None:
        self.candidates = candidates
        self.customers_by_route = customers_by_route
        self.yandex_score = yandex_score

def from_df(trace: pd.DataFrame, routes: pd.DataFrame) -> Trace:
    return Trace(
        candidates=dict(trace.groupby('candidate_id').apply(lambda df: dict(zip(df['route_id'], df['score'])))),
        customers_by_route={row.route_id: set(row.claim_segment_uuid_list) for _, row in routes.iterrows()},
        yandex_score=trace[trace.chosen_for_proposition_flg].score.sum(),
    )
