"""The one walk over the physics functions that MT-04 and the N-09 unit checks share (REQ-N-09, U-D26 item 2).

A physics function is a public function of a public `embodic.physics` module. It sits at module level or in the body of
a public top-level class. A class that names `Protocol` as a base is skipped, because its members have the body `...`
and the function that runs belongs to the implementing class outside physics. Public means a name without a leading
underscore, so `__init__` and `__post_init__` stay out.
"""

import ast
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tests.static.conftest import SourceModule


@dataclass(frozen=True)
class PhysicsFunction:
    """One function to check: where it is, its qualified name and the parameters its docstring must list."""

    module: "SourceModule"
    node: ast.FunctionDef | ast.AsyncFunctionDef
    owner: str | None

    @property
    def name(self) -> str:
        """Return 'function' or 'Class.method'."""
        return self.node.name if self.owner is None else f"{self.owner}.{self.node.name}"

    @property
    def where(self) -> str:
        """Return 'path:line'."""
        return self.module.where(self.node)

    @property
    def docstring(self) -> str:
        """Return the cleaned docstring, empty when there is none."""
        return ast.get_docstring(self.node) or ""

    @property
    def parameters(self) -> list[str]:
        """Return the parameter names that need an entry: all of them, less `self` or `cls` of a method."""
        arguments = self.node.args
        names = [a.arg for a in (*arguments.posonlyargs, *arguments.args)]
        if self.owner is not None and not _is_static(self.node):
            names = names[1:]
        return [*names, *(a.arg for a in arguments.kwonlyargs)]


def _is_static(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    return any(_dotted_tail(decorator) == "staticmethod" for decorator in node.decorator_list)


def _dotted_tail(node: ast.expr) -> str | None:
    """Return the last name of `Name`, `a.Name` or `Name[...]`, the three ways a base or decorator is written."""
    if isinstance(node, ast.Subscript):
        return _dotted_tail(node.value)
    if isinstance(node, ast.Attribute):
        return node.attr
    return node.id if isinstance(node, ast.Name) else None


def _is_protocol(cls: ast.ClassDef) -> bool:
    return any(_dotted_tail(base) == "Protocol" for base in cls.bases)


def public_physics_functions(modules: "Iterable[SourceModule]") -> Iterator[PhysicsFunction]:
    """Yield every physics function of `modules`: module-level functions, then the methods of each public class."""
    for module in modules:
        if not module.in_package("embodic.physics") or module.name.rsplit(".", 1)[-1].startswith("_"):
            continue
        for node in module.tree.body:
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef) and not node.name.startswith("_"):
                yield PhysicsFunction(module, node, None)
            elif isinstance(node, ast.ClassDef) and not node.name.startswith("_") and not _is_protocol(node):
                for member in node.body:
                    if isinstance(member, ast.FunctionDef | ast.AsyncFunctionDef) and not member.name.startswith("_"):
                        yield PhysicsFunction(module, member, node.name)
