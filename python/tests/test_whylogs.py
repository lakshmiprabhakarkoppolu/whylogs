import numpy
import pandas as pd

import whylogs as y


def test_basic_log() -> None:
    d = {"col1": [1, 2], "col2": [3.0, 4.0], "col3": ["a", "b"]}
    df = pd.DataFrame(data=d)

    results = y.log(df)

    profile = results.get_profile()

    assert profile._columns["col1"]._schema.dtype == numpy.int64
    assert profile._columns["col2"]._schema.dtype == numpy.float64
    assert profile._columns["col3"]._schema.dtype.name == "object"


def test_annotation() -> None:
    @y.profiling()
    def test_pdf() -> pd.DataFrame:
        d = {"col1": [1, 2], "col2": [3.0, 4.0], "col3": ["a", "b"]}
        df = pd.DataFrame(data=d)
        return df

    df = test_pdf()
    assert hasattr(df, "profiling_results")
    assert df.profiling_results is not None