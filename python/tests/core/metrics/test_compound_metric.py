import numpy as np
import pytest

from whylogs.core import ColumnSchema
from whylogs.core.metrics.compound_metric import CompoundMetric
from whylogs.core.metrics.metrics import DistributionMetric
from whylogs.core.preprocessing import PreprocessedColumn


class GoodCM(CompoundMetric):
    """Trivial CompoundMetric subclass for unit testing"""

    @property
    def namespace(self) -> str:
        return "good"

    @classmethod
    def zero(cls, schema: ColumnSchema) -> "GoodCM":
        return GoodCM({})


def test_compound_metric() -> None:
    metric = GoodCM(
        {
            "Metric1": DistributionMetric.zero(ColumnSchema(dtype=int)),
            "Metric2": DistributionMetric.zero(ColumnSchema(dtype=int)),
        },
    )
    data = [10, 20, 30]
    arr = np.array(data)
    col = PreprocessedColumn.apply(arr)
    metric.columnar_update(col)

    assert metric.submetrics["Metric1"].kll.value.get_n() == 3
    assert metric.submetrics["Metric2"].mean.value == arr.mean()


# BadCM 1 and 2 are for testing invalid namespace


class BadCM1(CompoundMetric):
    @property
    def namespace(self) -> str:
        return "bad:namespace"

    @classmethod
    def zero(cls, schema: ColumnSchema) -> "BadCM1":
        return BadCM1({})


class BadCM2(CompoundMetric):
    @property
    def namespace(self) -> str:
        return "bad/namespace"

    @classmethod
    def zero(cls, schema: ColumnSchema) -> "BadCM2":
        return BadCM2({})


@pytest.mark.parametrize(
    "cls, metrics",
    [
        (GoodCM, {"bad:name": DistributionMetric.zero(ColumnSchema(dtype=int))}),
        (GoodCM, {"bad/name": DistributionMetric.zero(ColumnSchema(dtype=int))}),
        (BadCM1, {"good": DistributionMetric.zero(ColumnSchema(dtype=int))}),
        (BadCM2, {"good": DistributionMetric.zero(ColumnSchema(dtype=int))}),
        (GoodCM, {"good": GoodCM.zero(None)}),  # Nesting not allowed
    ],
)
def test_compound_metric_invalid_initialization(cls, metrics):
    with pytest.raises(ValueError):
        cls(metrics)


def test_compound_metric_serialization() -> None:
    metric = GoodCM(
        {
            "Metric1": DistributionMetric.zero(ColumnSchema(dtype=int)),
            "Metric2": DistributionMetric.zero(ColumnSchema(dtype=int)),
        },
    )
    data = [10, 20, 30]
    arr = np.array(data)
    col = PreprocessedColumn.apply(arr)
    metric.columnar_update(col)
    msg = metric.to_protobuf()
    deserialized = GoodCM.from_protobuf(msg)

    assert deserialized.namespace == metric.namespace
    assert deserialized.submetrics["Metric1"].kll.value.get_n() == 3
    assert deserialized.submetrics["Metric2"].mean.value == arr.mean()
    assert len(deserialized.submetrics) == 2


def test_compound_metric_summary() -> None:
    metric = GoodCM(
        {
            "Metric1": DistributionMetric.zero(ColumnSchema(dtype=int)),
            "Metric2": DistributionMetric.zero(ColumnSchema(dtype=int)),
        },
    )
    data = [10, 20, 30]
    arr = np.array(data)
    col = PreprocessedColumn.apply(arr)
    metric.columnar_update(col)
    summary = metric.to_summary_dict(None)

    assert "good/Metric1/mean" in summary
    assert "good/Metric1/stddev" in summary
    assert "good/Metric2/n" in summary
    assert "good/Metric2/median" in summary


def test_compound_metric_merge() -> None:
    metric1 = GoodCM(
        {
            "Metric1": DistributionMetric.zero(ColumnSchema(dtype=int)),
            "Metric2": DistributionMetric.zero(ColumnSchema(dtype=int)),
        },
    )
    data1 = [10, 20, 30]
    arr1 = np.array(data1)
    col = PreprocessedColumn.apply(arr1)
    metric1.columnar_update(col)
    d1 = DistributionMetric.zero(ColumnSchema(dtype=int))
    d1.columnar_update(col)

    metric2 = GoodCM(
        {
            "Metric1": DistributionMetric.zero(ColumnSchema(dtype=int)),
            "Metric2": DistributionMetric.zero(ColumnSchema(dtype=int)),
        },
    )
    data2 = [40, 50, 60]
    arr2 = np.array(data2)
    col = PreprocessedColumn.apply(arr2)
    metric2.columnar_update(col)
    d2 = DistributionMetric.zero(ColumnSchema(dtype=int))
    d2.columnar_update(col)

    merged = metric1 + metric2
    d_merged = d1 + d2

    assert merged.submetrics["Metric1"].kll.value.get_n() == d_merged.kll.value.get_n()
    assert merged.submetrics["Metric1"].mean.value == d_merged.mean.value
    assert merged.submetrics["Metric1"].stddev == d_merged.stddev
    assert merged.submetrics["Metric2"].kll.value.get_n() == d_merged.kll.value.get_n()
    assert merged.submetrics["Metric2"].mean.value == d_merged.mean.value
    assert merged.submetrics["Metric2"].stddev == d_merged.stddev
