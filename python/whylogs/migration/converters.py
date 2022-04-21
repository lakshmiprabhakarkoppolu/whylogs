from typing import Dict

import whylogs_datasketches as ds  # type: ignore

from whylogs.core import ColumnProfileView, DatasetProfileView
from whylogs.core.metrics import (
    ColumnCountsMetric,
    DistributionMetric,
    FrequentItemsMetric,
    IntsMetric,
    StandardMetric,
    TypeCountersMetric,
)
from whylogs.core.metrics.metric_components import (
    FractionalComponent,
    FrequentItemsComponent,
    IntegralComponent,
    KllComponent,
    MaxIntegralComponent,
    MinIntegralComponent,
)
from whylogs.core.proto.v0 import ColumnMessageV0, DatasetProfileMessageV0, InferredType


def v0_to_v1_view(msg: DatasetProfileMessageV0) -> DatasetProfileView:
    columns: Dict[str, ColumnProfileView] = {}

    for col_name, col_msg in msg.columns.items():
        dist_metric = _extract_dist_metric(col_msg)
        fi_metric = FrequentItemsMetric(
            fs=FrequentItemsComponent(ds.frequent_strings_sketch.deserialize(col_msg.frequent_items.sketch))
        )
        count_metrics = _extract_col_counts(col_msg)
        type_counters_metric = _extract_type_counts_metric(col_msg)
        int_metric = _extract_ints_metric(col_msg)

        columns[col_name] = ColumnProfileView(
            metrics={
                StandardMetric.dist.name: dist_metric,
                StandardMetric.fi.name: fi_metric,
                StandardMetric.cnt.name: count_metrics,
                StandardMetric.types.name: type_counters_metric,
                StandardMetric.card.name: type_counters_metric,
                StandardMetric.int.name: int_metric,
            }
        )

    return DatasetProfileView(columns=columns)


def _extract_ints_metric(msg: ColumnMessageV0) -> IntsMetric:
    int_max = msg.numbers.longs.max
    int_min = msg.numbers.longs.min
    return IntsMetric(max=MaxIntegralComponent(int_max), min=MinIntegralComponent(int_min))


def _extract_type_counts_metric(msg: ColumnMessageV0) -> TypeCountersMetric:
    int_count = msg.schema.typeCounts.get(InferredType.INTEGRAL)
    bool_count = msg.schema.typeCounts.get(InferredType.BOOLEAN)
    frac_count = msg.schema.typeCounts.get(InferredType.FRACTIONAL)
    string_count = msg.schema.typeCounts.get(InferredType.STRING)
    obj_count = msg.schema.typeCounts.get(InferredType.UNKNOWN)
    return TypeCountersMetric(
        integral=IntegralComponent(int_count),
        fractional=IntegralComponent(frac_count),
        boolean=IntegralComponent(bool_count),
        string=IntegralComponent(string_count),
        object=IntegralComponent(obj_count),
    )


def _extract_col_counts(msg: ColumnMessageV0) -> ColumnCountsMetric:
    count_n = msg.counters.count
    count_null = msg.counters.null_count
    return ColumnCountsMetric(n=IntegralComponent(count_n), null=IntegralComponent(count_null.value))


def _extract_dist_metric(msg: ColumnMessageV0) -> DistributionMetric:
    floats_sk = ds.kll_floats_sketch.deserialize(msg.numbers.histogram)
    doubles_sk: ds.kll_doubles_sketch = ds.kll_floats_sketch.float_to_doubles(floats_sk)
    dist_mean = msg.numbers.variance.mean
    dist_m2 = msg.numbers.variance.sum
    return DistributionMetric(
        kll=KllComponent(doubles_sk),
        mean=FractionalComponent(dist_mean),
        m2=FractionalComponent(dist_m2),
    )