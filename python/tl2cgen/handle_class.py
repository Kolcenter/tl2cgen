"""Internal classes to hold native handles"""
import ctypes
import json
import pathlib
from typing import Any, Dict, Optional, Union

import treelite

from .libloader import _LIB, _check_call
from .util import c_str


class _TreeliteModel:
    """Treelite model object"""

    def __init__(self, model: treelite.Model):
        model_bytes = model.serialize_bytes()
        model_bytes_len = len(model_bytes)
        buffer = ctypes.create_string_buffer(model_bytes, model_bytes_len)
        self.handle = ctypes.c_void_p()
        _check_call(
            _LIB.TL2cgenLoadTreeliteModelFromBytes(
                ctypes.pointer(buffer),
                ctypes.c_size_t(model_bytes_len),
                ctypes.byref(self.handle),
            )
        )

    def __del__(self):
        if self.handle:
            _check_call(_LIB.TL2cgenFreeTreeliteModel(self.handle))


class _Compiler:
    """Compiler object"""

    def __init__(
        self,
        params: Optional[Dict[str, Any]],
        compiler: str = "ast_native",
        verbose: bool = False,
    ):
        self.handle = ctypes.c_void_p()
        if params is None:
            params = {}
        if verbose:
            params["verbose"] = 1
        params_json_str = json.dumps(params)
        _check_call(
            _LIB.TL2cgenCompilerCreate(
                c_str(compiler), c_str(params_json_str), ctypes.byref(self.handle)
            )
        )

    def compile(self, model: _TreeliteModel, dirpath: Union[str, pathlib.Path]) -> None:
        """
        Generate prediction code

        Parameters
        ----------
        model :
            Model to convert to C code
        dirpath :
            Directory to store header and source files
        """
        dirpath = pathlib.Path(dirpath).expanduser().resolve()
        _check_call(
            _LIB.TL2cgenCompilerGenerateCode(
                self.handle, model.handle, c_str(str(dirpath))
            )
        )

    def __del__(self):
        if self.handle:
            _check_call(_LIB.TL2cgenCompilerFree(self.handle))
