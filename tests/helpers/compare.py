import re

import numpy as np

# A header column is `<index>:<name>`; the name may contain spaces (e.g.
# "Ki [M]"), so split on the index markers rather than on whitespace.
_HEADER_COL = re.compile(r"\d+:(.*?)(?=\s+\d+:|\s*$)")


def read_trace(path):
    """Parse a CellModelTest -outfile trace.

    Line 1 is a header of `idx:name` tokens; the remaining lines are
    whitespace-separated floats. Returns (names, data) with data shape
    (rows, cols).
    """
    path = str(path)
    with open(path) as f:
        header = f.readline()
    names = _HEADER_COL.findall(header)
    data = np.loadtxt(path, skiprows=1)
    if data.ndim == 1:
        data = data.reshape(1, -1)
    assert data.shape[1] == len(names), (
        f"{path}: {len(names)} header columns but {data.shape[1]} data columns"
    )
    return names, data


def read_table(path):
    """Parse a whitespace-delimited table whose first line is plain column names.

    Used for outputs like CardioMechanics Pressure.dat
    (`time pressure130 volume130`). Returns (names, data).
    """
    path = str(path)
    with open(path) as f:
        names = f.readline().split()
    data = np.loadtxt(path, skiprows=1)
    if data.ndim == 1:
        data = data.reshape(1, -1)
    assert data.shape[1] == len(names), (
        f"{path}: {len(names)} header columns but {data.shape[1]} data columns"
    )
    return names, data


def read_vtu_points(path):
    """Deformed point coordinates from a VTU, ordered by PointID.

    CardioMechanics stores no explicit displacement field; the mesh point
    coordinates are the deformed geometry. Sorting by PointID makes the order
    independent of MPI partitioning. Returns (pointid, points) with points
    shape (N, 3). Requires meshio.
    """
    import meshio

    m = meshio.read(str(path))
    pts = m.points
    pid = m.point_data.get("PointID")
    if pid is None:
        return np.arange(len(pts)), pts
    pid = np.asarray(pid).ravel()
    order = np.argsort(pid, kind="stable")
    return pid[order], pts[order]


def write_golden(path, names, data):
    # CellModelTest writes ~7 significant figures; %.8e keeps that faithfully
    # without storing re-expansion noise, and stays well above the compare rtol.
    np.savetxt(str(path), data, fmt="%.8e", delimiter=",", header=",".join(names), comments="")


def read_golden(path):
    path = str(path)
    with open(path) as f:
        names = f.readline().strip().split(",")
    data = np.loadtxt(path, delimiter=",", skiprows=1)
    if data.ndim == 1:
        data = data.reshape(1, -1)
    return names, data


def compare_columns(actual, golden, rtol, atol=0.0):
    """Assert two (names, data) traces match within tolerance, column by column.

    Raises AssertionError naming the offending column, row, and delta.
    """
    a_names, a = actual
    g_names, g = golden
    assert a_names == g_names, f"column names differ:\n actual={a_names}\n golden={g_names}"
    assert a.shape == g.shape, f"shape mismatch: actual={a.shape} golden={g.shape}"
    for j, name in enumerate(g_names):
        if not np.allclose(a[:, j], g[:, j], rtol=rtol, atol=atol, equal_nan=True):
            diff = np.abs(a[:, j] - g[:, j])
            i = int(np.nanargmax(diff))
            raise AssertionError(
                f"column '{name}' differs beyond rtol={rtol} atol={atol}: "
                f"row {i} actual={a[i, j]:.6e} golden={g[i, j]:.6e} "
                f"|delta|={diff[i]:.3e}"
            )
