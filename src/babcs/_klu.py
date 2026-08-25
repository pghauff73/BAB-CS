from __future__ import annotations

import ctypes
import ctypes.util
import math
import threading
import weakref
from collections import OrderedDict
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Sequence


MAXIMUM_KLU_WORKSPACES_PER_THREAD = 128
_KLU_WORKSPACES = threading.local()

_INT_POINTER = ctypes.POINTER(ctypes.c_int32)
_DOUBLE_POINTER = ctypes.POINTER(ctypes.c_double)
_VOID_POINTER_POINTER = ctypes.POINTER(ctypes.c_void_p)


class KluUnavailableError(RuntimeError):
    pass


class KluFactorizationError(RuntimeError):
    pass


class KluSingularError(KluFactorizationError):
    def __init__(self, pivot_index: int) -> None:
        super().__init__(f"singular matrix at KLU pivot {pivot_index}")
        self.pivot_index = pivot_index


class _KluCommon(ctypes.Structure):
    _fields_ = [
        ("tol", ctypes.c_double),
        ("memgrow", ctypes.c_double),
        ("initmem_amd", ctypes.c_double),
        ("initmem", ctypes.c_double),
        ("maxwork", ctypes.c_double),
        ("btf", ctypes.c_int),
        ("ordering", ctypes.c_int),
        ("scale", ctypes.c_int),
        ("user_order", ctypes.c_void_p),
        ("user_data", ctypes.c_void_p),
        ("halt_if_singular", ctypes.c_int),
        ("status", ctypes.c_int),
        ("nrealloc", ctypes.c_int),
        ("structural_rank", ctypes.c_int32),
        ("numerical_rank", ctypes.c_int32),
        ("singular_col", ctypes.c_int32),
        ("noffdiag", ctypes.c_int32),
        ("flops", ctypes.c_double),
        ("rcond", ctypes.c_double),
        ("condest", ctypes.c_double),
        ("rgrowth", ctypes.c_double),
        ("work", ctypes.c_double),
        ("memusage", ctypes.c_size_t),
        ("mempeak", ctypes.c_size_t),
    ]


class _KluNumericHeader(ctypes.Structure):
    _fields_ = [
        ("n", ctypes.c_int32),
        ("nblocks", ctypes.c_int32),
        ("lnz", ctypes.c_int32),
        ("unz", ctypes.c_int32),
        ("max_lnz_block", ctypes.c_int32),
        ("max_unz_block", ctypes.c_int32),
        ("Pnum", _INT_POINTER),
        ("Pinv", _INT_POINTER),
        ("Lip", _INT_POINTER),
        ("Uip", _INT_POINTER),
        ("Llen", _INT_POINTER),
        ("Ulen", _INT_POINTER),
        ("LUbx", ctypes.POINTER(ctypes.c_void_p)),
        ("LUsize", ctypes.POINTER(ctypes.c_size_t)),
        ("Udiag", _DOUBLE_POINTER),
    ]


@dataclass(frozen=True)
class KluLinearFactorization:
    size: int
    data: tuple[float, ...]
    row_indices: tuple[int, ...]
    column_pointers: tuple[int, ...]
    minimum_pivot: float
    token: object
    workspace_reference: Any
    workspace_thread_id: int

    @property
    def backend(self) -> str:
        return "klu"


@dataclass(frozen=True)
class _KluComponents:
    library: Any
    numpy: Any
    version: tuple[int, int, int]


def _configure_library(library: Any) -> None:
    common_pointer = ctypes.POINTER(_KluCommon)
    library.klu_version.argtypes = [ctypes.POINTER(ctypes.c_int)]
    library.klu_version.restype = None
    library.klu_defaults.argtypes = [common_pointer]
    library.klu_defaults.restype = ctypes.c_int
    library.klu_analyze.argtypes = [
        ctypes.c_int32,
        _INT_POINTER,
        _INT_POINTER,
        common_pointer,
    ]
    library.klu_analyze.restype = ctypes.c_void_p
    library.klu_factor.argtypes = [
        _INT_POINTER,
        _INT_POINTER,
        _DOUBLE_POINTER,
        ctypes.c_void_p,
        common_pointer,
    ]
    library.klu_factor.restype = ctypes.c_void_p
    library.klu_refactor.argtypes = [
        _INT_POINTER,
        _INT_POINTER,
        _DOUBLE_POINTER,
        ctypes.c_void_p,
        ctypes.c_void_p,
        common_pointer,
    ]
    library.klu_refactor.restype = ctypes.c_int
    library.klu_solve.argtypes = [
        ctypes.c_void_p,
        ctypes.c_void_p,
        ctypes.c_int32,
        ctypes.c_int32,
        _DOUBLE_POINTER,
        common_pointer,
    ]
    library.klu_solve.restype = ctypes.c_int
    library.klu_free_symbolic.argtypes = [_VOID_POINTER_POINTER, common_pointer]
    library.klu_free_symbolic.restype = ctypes.c_int
    library.klu_free_numeric.argtypes = [_VOID_POINTER_POINTER, common_pointer]
    library.klu_free_numeric.restype = ctypes.c_int


@lru_cache(maxsize=1)
def _klu_components() -> _KluComponents | None:
    try:
        import numpy
    except ImportError:
        return None
    library_name = ctypes.util.find_library("klu")
    if library_name is None:
        return None
    try:
        library = ctypes.CDLL(library_name)
        _configure_library(library)
    except (AttributeError, OSError):
        return None
    version_values = (ctypes.c_int * 3)()
    library.klu_version(version_values)
    version = tuple(int(value) for value in version_values)
    if version[0] != 2:
        return None
    return _KluComponents(library, numpy, version)


def klu_available() -> bool:
    return _klu_components() is not None


def klu_version() -> tuple[int, int, int] | None:
    components = _klu_components()
    return None if components is None else components.version


def _int_pointer(values: Any) -> _INT_POINTER:
    return values.ctypes.data_as(_INT_POINTER)


def _double_pointer(values: Any) -> _DOUBLE_POINTER:
    return values.ctypes.data_as(_DOUBLE_POINTER)


def _singular_pivot(common: _KluCommon, size: int) -> int:
    if 0 <= common.singular_col < size:
        return int(common.singular_col)
    if 0 <= common.numerical_rank < size:
        return int(common.numerical_rank)
    return 0


class _KluSparseWorkspace:
    def __init__(
        self,
        components: _KluComponents,
        size: int,
        row_indices: tuple[int, ...],
        column_pointers: tuple[int, ...],
    ) -> None:
        self.components = components
        self.size = size
        self.closed = False
        self.symbolic = ctypes.c_void_p()
        self.numeric = ctypes.c_void_p()
        self.current_token: object | None = None
        self.source_row_indices = row_indices
        self.source_column_pointers = column_pointers
        self.row_indices = components.numpy.asarray(row_indices, dtype=components.numpy.int32)
        self.column_pointers = components.numpy.asarray(
            column_pointers,
            dtype=components.numpy.int32,
        )
        self.values = components.numpy.empty(len(row_indices), dtype=float)
        self.common = _KluCommon()
        if not components.library.klu_defaults(ctypes.byref(self.common)):
            raise KluFactorizationError("KLU defaults initialization failed")
        self.common.scale = 0
        self.common.halt_if_singular = 1
        symbolic = components.library.klu_analyze(
            size,
            _int_pointer(self.column_pointers),
            _int_pointer(self.row_indices),
            ctypes.byref(self.common),
        )
        if not symbolic:
            raise KluFactorizationError(
                f"KLU symbolic analysis failed with status {self.common.status}"
            )
        self.symbolic = ctypes.c_void_p(symbolic)

    def _free_numeric(self) -> None:
        if self.numeric.value:
            self.components.library.klu_free_numeric(
                ctypes.byref(self.numeric),
                ctypes.byref(self.common),
            )
        self.current_token = None

    def _check_pivots(self, minimum_pivot: float) -> None:
        if not self.numeric.value:
            raise KluFactorizationError("KLU numeric factorization is unavailable")
        header = ctypes.cast(
            self.numeric,
            ctypes.POINTER(_KluNumericHeader),
        ).contents
        if header.n != self.size or not header.Udiag:
            raise KluFactorizationError("KLU numeric factorization has an invalid layout")
        minimum_index = 0
        minimum_magnitude = math.inf
        for index in range(self.size):
            magnitude = abs(float(header.Udiag[index]))
            if not math.isfinite(magnitude):
                raise KluSingularError(index)
            if magnitude < minimum_magnitude:
                minimum_index = index
                minimum_magnitude = magnitude
        if minimum_magnitude <= minimum_pivot:
            raise KluSingularError(minimum_index)

    def factor(
        self,
        data: Sequence[float],
        minimum_pivot: float,
        token: object,
    ) -> None:
        if self.current_token is token:
            return
        self.values[:] = data
        if self.numeric.value:
            succeeded = self.components.library.klu_refactor(
                _int_pointer(self.column_pointers),
                _int_pointer(self.row_indices),
                _double_pointer(self.values),
                self.symbolic,
                self.numeric,
                ctypes.byref(self.common),
            )
            if not succeeded:
                pivot_index = _singular_pivot(self.common, self.size)
                status = self.common.status
                self._free_numeric()
                if status == 1:
                    raise KluSingularError(pivot_index)
                raise KluFactorizationError(
                    f"KLU numeric refactorization failed with status {status}"
                )
        else:
            numeric = self.components.library.klu_factor(
                _int_pointer(self.column_pointers),
                _int_pointer(self.row_indices),
                _double_pointer(self.values),
                self.symbolic,
                ctypes.byref(self.common),
            )
            if not numeric:
                if self.common.status == 1:
                    raise KluSingularError(_singular_pivot(self.common, self.size))
                raise KluFactorizationError(
                    f"KLU numeric factorization failed with status {self.common.status}"
                )
            self.numeric = ctypes.c_void_p(numeric)
        try:
            self._check_pivots(minimum_pivot)
        except KluSingularError:
            self.current_token = None
            raise
        self.current_token = token

    def solve(self, right_hand_sides: Any) -> Any:
        right_hand_side_count = len(right_hand_sides)
        if right_hand_side_count == 0:
            return self.components.numpy.empty((0, self.size), dtype=float)
        source = self.components.numpy.asarray(right_hand_sides, dtype=float)
        values = self.components.numpy.empty(
            (self.size, right_hand_side_count),
            dtype=float,
            order="F",
        )
        values[:] = source.transpose()
        if not self.components.library.klu_solve(
            self.symbolic,
            self.numeric,
            self.size,
            right_hand_side_count,
            _double_pointer(values),
            ctypes.byref(self.common),
        ):
            raise KluFactorizationError(f"KLU solve failed with status {self.common.status}")
        if not bool(self.components.numpy.all(self.components.numpy.isfinite(values))):
            raise KluSingularError(0)
        return values.transpose().copy()

    def close(self) -> None:
        if self.closed:
            return
        self.closed = True
        try:
            self._free_numeric()
            if self.symbolic.value:
                self.components.library.klu_free_symbolic(
                    ctypes.byref(self.symbolic),
                    ctypes.byref(self.common),
                )
        except Exception:
            pass

    def __del__(self) -> None:
        self.close()


def _klu_sparse_workspace(
    size: int,
    row_indices: tuple[int, ...],
    column_pointers: tuple[int, ...],
) -> _KluSparseWorkspace:
    components = _klu_components()
    if components is None:
        raise KluUnavailableError(
            "the KLU linear backend requires NumPy and a compatible SuiteSparse KLU 2 library"
        )
    key = (size, row_indices, column_pointers)
    identity_key = (size, id(row_indices), id(column_pointers))
    workspaces = getattr(_KLU_WORKSPACES, "values", None)
    if workspaces is None:
        workspaces = OrderedDict()
        _KLU_WORKSPACES.values = workspaces
    identities = getattr(_KLU_WORKSPACES, "identities", None)
    if identities is None:
        identities = OrderedDict()
        _KLU_WORKSPACES.identities = identities
    workspace = identities.pop(identity_key, None)
    if (
        workspace is not None
        and not workspace.closed
        and workspace.source_row_indices is row_indices
        and workspace.source_column_pointers is column_pointers
    ):
        identities[identity_key] = workspace
        return workspace
    workspace = workspaces.pop(key, None)
    if workspace is not None:
        workspaces[key] = workspace
        identities[identity_key] = workspace
        while len(identities) > MAXIMUM_KLU_WORKSPACES_PER_THREAD:
            identities.popitem(last=False)
        return workspace
    while len(workspaces) >= MAXIMUM_KLU_WORKSPACES_PER_THREAD:
        _, evicted = workspaces.popitem(last=False)
        for alias, candidate in tuple(identities.items()):
            if candidate is evicted:
                identities.pop(alias)
        evicted.close()
    workspace = _KluSparseWorkspace(
        components,
        size,
        row_indices,
        column_pointers,
    )
    workspaces[key] = workspace
    identities[identity_key] = workspace
    while len(identities) > MAXIMUM_KLU_WORKSPACES_PER_THREAD:
        identities.popitem(last=False)
    return workspace


def clear_klu_workspaces() -> None:
    workspaces = getattr(_KLU_WORKSPACES, "values", None)
    if workspaces is None:
        return
    for workspace in workspaces.values():
        workspace.close()
    workspaces.clear()
    identities = getattr(_KLU_WORKSPACES, "identities", None)
    if identities is not None:
        identities.clear()


def factor_sparse(
    size: int,
    data: tuple[float, ...],
    row_indices: tuple[int, ...],
    column_pointers: tuple[int, ...],
    minimum_pivot: float,
) -> KluLinearFactorization:
    token = object()
    workspace = _klu_sparse_workspace(size, row_indices, column_pointers)
    factorization = KluLinearFactorization(
        size,
        data,
        row_indices,
        column_pointers,
        minimum_pivot,
        token,
        weakref.ref(workspace),
        threading.get_ident(),
    )
    workspace.factor(data, minimum_pivot, token)
    return factorization


def solve_factorized_multiple(
    factorization: KluLinearFactorization,
    right_hand_sides: Sequence[Sequence[float]],
) -> Any:
    workspace = factorization.workspace_reference()
    if (
        workspace is None
        or workspace.closed
        or factorization.workspace_thread_id != threading.get_ident()
    ):
        workspace = _klu_sparse_workspace(
            factorization.size,
            factorization.row_indices,
            factorization.column_pointers,
        )
    workspace.factor(
        factorization.data,
        factorization.minimum_pivot,
        factorization.token,
    )
    return workspace.solve(right_hand_sides)
