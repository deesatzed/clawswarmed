"""Deterministic codebug task bank with hidden-test verification."""

from __future__ import annotations

import ast
from dataclasses import asdict, dataclass
from typing import Any, Callable


@dataclass(frozen=True)
class HiddenTest:
    args: tuple[Any, ...]
    expected: Any

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CodebugTask:
    id: str
    function_name: str
    parameters: tuple[str, ...]
    public_prompt: str
    correct_patch: str
    incorrect_patch: str
    hidden_tests: tuple[HiddenTest, ...]
    suite: str = "codebug"
    verifier: str = "hidden_tests"

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["hidden_tests"] = [test.to_dict() for test in self.hidden_tests]
        return payload

    def public_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "function_name": self.function_name,
            "parameters": list(self.parameters),
            "public_prompt": self.public_prompt,
            "suite": self.suite,
            "verifier": self.verifier,
            "hidden_test_count": len(self.hidden_tests),
        }


@dataclass(frozen=True)
class VerificationResult:
    passed: bool
    total: int
    failures: tuple[dict[str, Any], ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


_ALLOWED_AST_NODES = (
    ast.Expression,
    ast.BinOp,
    ast.UnaryOp,
    ast.BoolOp,
    ast.Compare,
    ast.IfExp,
    ast.Name,
    ast.Load,
    ast.Constant,
    ast.Subscript,
    ast.Slice,
    ast.Tuple,
    ast.List,
    ast.Add,
    ast.Sub,
    ast.Mult,
    ast.Div,
    ast.FloorDiv,
    ast.Mod,
    ast.Pow,
    ast.USub,
    ast.UAdd,
    ast.And,
    ast.Or,
    ast.Eq,
    ast.NotEq,
    ast.Lt,
    ast.LtE,
    ast.Gt,
    ast.GtE,
)


def _compile_patch(task: CodebugTask, patch_source: str) -> Callable[..., Any]:
    tree = ast.parse(patch_source, mode="eval")
    parameter_names = set(task.parameters)
    for node in ast.walk(tree):
        if not isinstance(node, _ALLOWED_AST_NODES):
            raise ValueError(f"disallowed patch syntax: {type(node).__name__}")
        if isinstance(node, ast.Name) and node.id not in parameter_names:
            raise ValueError(f"unknown patch name: {node.id}")
    code = compile(tree, f"<{task.id}:patch>", "eval")

    def repaired_function(*args: Any) -> Any:
        if len(args) != len(task.parameters):
            raise TypeError(f"{task.function_name} expected {len(task.parameters)} argument(s)")
        local_vars = dict(zip(task.parameters, args, strict=True))
        return eval(code, {"__builtins__": {}}, local_vars)

    return repaired_function


def verify_patch(task: CodebugTask, patch_source: str) -> VerificationResult:
    failures: list[dict[str, Any]] = []
    try:
        repaired_function = _compile_patch(task, patch_source)
    except Exception as exc:  # pragma: no cover - exercised through failure payloads
        return VerificationResult(
            passed=False,
            total=len(task.hidden_tests),
            failures=({"compile_error": str(exc)},),
        )

    for hidden_test in task.hidden_tests:
        try:
            observed = repaired_function(*hidden_test.args)
        except Exception as exc:  # pragma: no cover - exercised through failure payloads
            failures.append({"args": hidden_test.args, "error": str(exc), "expected": hidden_test.expected})
            continue
        if observed != hidden_test.expected:
            failures.append({"args": hidden_test.args, "observed": observed, "expected": hidden_test.expected})

    return VerificationResult(
        passed=not failures,
        total=len(task.hidden_tests),
        failures=tuple(failures),
    )


def _task(
    task_id: str,
    function_name: str,
    parameters: tuple[str, ...],
    prompt: str,
    correct_patch: str,
    incorrect_patch: str,
    tests: tuple[tuple[tuple[Any, ...], Any], ...],
) -> CodebugTask:
    return CodebugTask(
        id=task_id,
        function_name=function_name,
        parameters=parameters,
        public_prompt=prompt,
        correct_patch=correct_patch,
        incorrect_patch=incorrect_patch,
        hidden_tests=tuple(HiddenTest(args=args, expected=expected) for args, expected in tests),
    )


def _round_tasks(round_index: int) -> list[CodebugTask]:
    c = round_index + 2
    lo = c - 1
    hi = c + 3
    suffix = f"{round_index + 1:02d}"
    generic_prompt = "Repair the helper so it satisfies withheld verifier cases. No examples reveal the hidden outputs."
    return [
        _task(
            f"codebug_add_{suffix}",
            "repair_add",
            ("x",),
            generic_prompt,
            f"x + {c}",
            f"x - {c}",
            (((-c,), -c + c), ((0,), c), ((c + 2,), (c + 2) + c)),
        ),
        _task(
            f"codebug_multiply_{suffix}",
            "repair_multiply",
            ("x",),
            generic_prompt,
            f"x * {c}",
            f"x + {c}",
            (((-2,), -2 * c), ((3,), 3 * c), ((c,), c * c)),
        ),
        _task(
            f"codebug_multiple_{suffix}",
            "repair_multiple",
            ("n",),
            generic_prompt,
            f"n % {c} == 0",
            f"n % {c + 1} == 0",
            (((c,), True), ((c + 1,), False), ((c * 2,), True)),
        ),
        _task(
            f"codebug_floor_{suffix}",
            "repair_floor",
            ("x",),
            generic_prompt,
            f"x if x > {c} else {c}",
            f"x if x < {c} else {c}",
            (((c - 1,), c), ((c,), c), ((c + 2,), c + 2)),
        ),
        _task(
            f"codebug_bounds_{suffix}",
            "repair_bounds",
            ("x",),
            generic_prompt,
            f"{lo} <= x <= {hi}",
            f"{lo} < x < {hi}",
            (((lo,), True), ((lo + 1,), True), ((hi,), True)),
        ),
        _task(
            f"codebug_reverse_{suffix}",
            "repair_reverse",
            ("text",),
            generic_prompt,
            "text[::-1]",
            "text",
            (((f"ab{c}",), f"{c}ba"), ((f"xy{c}z",), f"z{c}yx"), ((f"cat{c}",), f"{c}tac")),
        ),
        _task(
            f"codebug_last_digit_{suffix}",
            "repair_last_digit",
            ("n",),
            generic_prompt,
            "n % 10",
            "n // 10",
            (((10 + c,), c), ((97 + c,), (97 + c) % 10), ((c,), c)),
        ),
        _task(
            f"codebug_abs_shift_{suffix}",
            "repair_abs_shift",
            ("x",),
            generic_prompt,
            f"((-x) if x < 0 else x) + {c}",
            f"x + {c}",
            (((-c,), c + c), ((-c - 2,), c + 2 + c), ((c,), c + c)),
        ),
        _task(
            f"codebug_parity_{suffix}",
            "repair_parity",
            ("n",),
            generic_prompt,
            '"even" if n % 2 == 0 else "odd"',
            '"odd" if n % 2 == 0 else "even"',
            (((c,), "even" if c % 2 == 0 else "odd"), ((c + 1,), "even" if (c + 1) % 2 == 0 else "odd"), ((c + 2,), "even" if (c + 2) % 2 == 0 else "odd")),
        ),
        _task(
            f"codebug_clip_upper_{suffix}",
            "repair_clip_upper",
            ("x",),
            generic_prompt,
            f"x if x < {hi} else {hi}",
            f"x if x > {hi} else {hi}",
            (((hi - 1,), hi - 1), ((hi,), hi), ((hi + 3,), hi)),
        ),
    ]


def load_codebug_tasks() -> list[CodebugTask]:
    tasks: list[CodebugTask] = []
    for round_index in range(3):
        tasks.extend(_round_tasks(round_index))
    return tasks
