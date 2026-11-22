"""Conversions from bhtypes to the computational packages' conventions, one module per package.

=================================  ==========================================================
:mod:`bhtypes.convert.pygfunction`  ``to_pygfunction``: keyword arguments for pygfunction's
                                     pipe models; ``pipe_type``: its ``pipe_type_str``
:mod:`bhtypes.convert.bhresist`     ``to_bhresist``: keyword arguments for bhresist's
                                     ``Borehole.init_*_borehole``; ``init_method``: which one
=================================  ==========================================================

Reading and writing an application's input files (e.g. GHEDesigner's) belongs to that
application, not here.

Import the functions rather than the modules, so the module names do not shadow the
packages themselves::

    from bhtypes.convert.pygfunction import to_pygfunction

Extending and replacing conversions
-----------------------------------
Every ``to_*`` function is a :func:`functools.singledispatch` function, so it can be
extended for new types without changing bhtypes::

    @to_bhresist.register
    def _(pipe: MyTripleUTube) -> dict: ...

Dispatch picks the most specific registered type, so a subclass of a bhtypes class can
get its own conversion without affecting the class it extends.

To convert *differently* -- for example when a package adopts bhtypes and maintains its
own mapping -- write your own function. Do not re-register an existing bhtypes type: the
registry is shared by every package in the process, so that would change the conversion
for all of them.
"""

from __future__ import annotations


def _unsupported(target: str, obj) -> TypeError:
    return TypeError(f"no {target} conversion for {type(obj).__name__}; register one with .register")
