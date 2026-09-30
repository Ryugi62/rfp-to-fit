"""클린 아키텍처 import 방향 검사 — 코드를 실행하지 않고 ast로 import 문만 읽는다.
domain ← application ← adapters ← infrastructure. 안쪽 레이어는 바깥 레이어·외부 패키지를 모른다."""
from __future__ import annotations

import ast
import sys
from pathlib import Path

PKG = Path(__file__).resolve().parents[1] / "src" / "rfp_to_fit"
STDLIB = set(sys.stdlib_module_names)


def imports_of(source: str, package: str) -> list[str]:
    """모듈 소스의 모든 import(함수 안 지연 import 포함)를 절대 모듈 이름으로 돌려준다."""
    out = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            out += [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                base = package.split(".")[: len(package.split(".")) - (node.level - 1)]
                out.append(".".join(base + ([node.module] if node.module else [])))
            else:
                out.append(node.module or "")
    return out


def violations(layer: str, allowed_internal: tuple[str, ...], allow_external: bool = False,
               forbidden: tuple[str, ...] = ()) -> list[str]:
    bad = []
    for path in sorted((PKG / layer).glob("*.py")):
        for mod in imports_of(path.read_text(encoding="utf-8"), f"rfp_to_fit.{layer}"):
            top = mod.split(".")[0]
            if any(mod == f or mod.startswith(f + ".") for f in forbidden):
                bad.append(f"{layer}/{path.name}: {mod}")
            elif top == "rfp_to_fit":
                if not any(mod == a or mod.startswith(a + ".") for a in allowed_internal):
                    bad.append(f"{layer}/{path.name}: {mod}")
            elif top not in STDLIB and not allow_external:
                bad.append(f"{layer}/{path.name}: {mod}")
    return bad


def test_checker_resolves_relative_imports_and_sees_lazy_imports():
    src = "from ..domain.model import X\nfrom .ports import LLM\ndef f():\n    import httpx\n"
    assert imports_of(src, "rfp_to_fit.application") == ["rfp_to_fit.domain.model", "rfp_to_fit.application.ports", "httpx"]


def test_every_layer_has_modules():
    for layer in ("domain", "application", "adapters", "infrastructure"):
        assert len([p for p in (PKG / layer).glob("*.py") if p.name != "__init__.py"]) >= 1


def test_domain_imports_only_stdlib_and_domain():
    assert violations("domain", ("rfp_to_fit.domain",)) == []


def test_application_imports_only_stdlib_domain_and_application():
    assert violations("application", ("rfp_to_fit.domain", "rfp_to_fit.application")) == []


def test_adapters_never_import_infrastructure():
    assert violations("adapters", ("rfp_to_fit.domain", "rfp_to_fit.application", "rfp_to_fit.adapters"),
                      allow_external=True, forbidden=("rfp_to_fit.infrastructure",)) == []
