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

        self.candidates_linear, self.sorted_scores = dict(), dict()
        for candidate, routes in candidates.items():
            sorted_routes_n_scores = sorted(routes.items(), key=lambda item: item[1], reverse=True)
            self.candidates_linear[candidate] = sorted_routes_n_scores
            _, self.sorted_scores[candidate] = zip(*sorted_routes_n_scores)


def from_df(trace: pd.DataFrame, routes: pd.DataFrame) -> Trace:
    return Trace(
        candidates=dict(trace.groupby('candidate_id').apply(lambda df: dict(zip(df['route_id'], df['score'])))),
        customers_by_route={row.route_id: set(row.claim_segment_uuid_list) for _, row in routes.iterrows()},
        yandex_score=trace[trace.chosen_for_proposition_flg].score.sum(),
    )
