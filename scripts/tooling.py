#!/usr/bin/env python3
"""Deterministic build and validation helpers for the WhiteKiwi skill catalog."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import stat
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any, Iterable


SEMVER_RE = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$")
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
LINK_RE = re.compile(r"(?<!!)\[[^\]]*\]\(([^)]+)\)")
SCRIPT_REF_RE = re.compile(r"(?<![A-Za-z0-9_.-])(scripts/[A-Za-z0-9_./-]+)")
MAX_CLAWHUB_BYTES = 50 * 1024 * 1024
ZIP_TIME = (1980, 1, 1, 0, 0, 0)

GENERATED_DIRS = (
    Path("plugins/locron"),
    Path("platforms/openclaw/locron"),
)
GENERATED_FILES = (
    Path(".claude-plugin/marketplace.json"),
    Path(".agents/plugins/marketplace.json"),
)


class ValidationError(Exception):
    pass


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode()


def _openai_yaml(catalog: dict[str, Any]) -> bytes:
    info = catalog["skills"]["locron"]
    return (
        "interface:\n"
        f'  display_name: "{info["display_name"]}"\n'
        f'  short_description: "{info["short_description"]}"\n'
        '  default_prompt: "Use $locron to explain why this Locron job did not run."\n'
    ).encode()


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValidationError(f"missing JSON file: {path}") from exc
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValidationError(f"invalid JSON in {path}: {exc}") from exc


def parse_frontmatter(path: Path) -> tuple[dict[str, Any], str, str]:
    """Parse the deliberately small YAML subset used by this repository."""
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise ValidationError(f"missing SKILL.md: {path}") from exc
    except UnicodeDecodeError as exc:
        raise ValidationError(f"SKILL.md is not UTF-8: {path}") from exc
    if not text.startswith("---\n"):
        raise ValidationError(f"invalid YAML frontmatter in {path}: opening delimiter must be first")
    end = text.find("\n---\n", 4)
    if end < 0:
        raise ValidationError(f"invalid YAML frontmatter in {path}: missing closing delimiter")
    raw = text[4:end]
    body = text[end + 5 :]
    lines = raw.splitlines()

    def scalar(value: str, line_no: int) -> Any:
        value = value.strip()
        if not value:
            return None
        if value.startswith(("[", "{")):
            try:
                return json.loads(value)
            except json.JSONDecodeError as exc:
                raise ValidationError(f"invalid YAML frontmatter in {path}:{line_no}: {exc}") from exc
        if value[0:1] in {"'", '"'}:
            if len(value) < 2 or value[-1] != value[0]:
                raise ValidationError(f"invalid YAML frontmatter in {path}:{line_no}: unclosed quote")
            if value[0] == '"':
                try:
                    return json.loads(value)
                except json.JSONDecodeError as exc:
                    raise ValidationError(f"invalid YAML frontmatter in {path}:{line_no}: {exc}") from exc
            return value[1:-1].replace("''", "'")
        if value in {"true", "false"}:
            return value == "true"
        if value in {"null", "~"}:
            return None
        return value

    def block(index: int, indent: int) -> tuple[Any, int]:
        mapping: dict[str, Any] = {}
        sequence: list[Any] | None = None
        while index < len(lines):
            raw_line = lines[index]
            line_no = index + 2
            if not raw_line.strip() or raw_line.lstrip().startswith("#"):
                index += 1
                continue
            if "\t" in raw_line:
                raise ValidationError(f"invalid YAML frontmatter in {path}:{line_no}: tabs are not allowed")
            current = len(raw_line) - len(raw_line.lstrip(" "))
            if current < indent:
                break
            if current > indent:
                raise ValidationError(f"invalid YAML frontmatter in {path}:{line_no}: unexpected indentation")
            content = raw_line.strip()
            if content.startswith("- "):
                if mapping:
                    raise ValidationError(f"invalid YAML frontmatter in {path}:{line_no}: mixed map and list")
                if sequence is None:
                    sequence = []
                sequence.append(scalar(content[2:], line_no))
                index += 1
                continue
            if sequence is not None:
                raise ValidationError(f"invalid YAML frontmatter in {path}:{line_no}: mixed list and map")
            if ":" not in content:
                raise ValidationError(f"invalid YAML frontmatter in {path}:{line_no}: expected key: value")
            key, value = content.split(":", 1)
            if not re.fullmatch(r"[A-Za-z0-9_-]+", key):
                raise ValidationError(f"invalid YAML frontmatter in {path}:{line_no}: invalid key {key!r}")
            if key in mapping:
                raise ValidationError(f"invalid YAML frontmatter in {path}:{line_no}: duplicate key {key!r}")
            index += 1
            if value.strip():
                mapping[key] = scalar(value, line_no)
            else:
                child, index = block(index, indent + 2)
                if child == {}:
                    raise ValidationError(f"invalid YAML frontmatter in {path}:{line_no}: empty value for {key!r}")
                mapping[key] = child
        return (sequence if sequence is not None else mapping), index

    metadata, consumed = block(0, 0)
    if consumed != len(lines) or not isinstance(metadata, dict):
        raise ValidationError(f"invalid YAML frontmatter in {path}")
    return metadata, body, raw


def _validate_skill_tree(skill_dir: Path, *, openclaw: bool = False) -> dict[str, Any]:
    if skill_dir.is_symlink():
        raise ValidationError(f"path containment violation: skill directory is a symlink: {skill_dir}")
    metadata, body, _ = parse_frontmatter(skill_dir / "SKILL.md")
    name = metadata.get("name")
    description = metadata.get("description")
    if not isinstance(name, str) or not NAME_RE.fullmatch(name) or len(name) > 64:
        raise ValidationError(f"invalid skill name in {skill_dir / 'SKILL.md'}: {name!r}")
    if skill_dir.name != name:
        raise ValidationError(f"parent/name invariant failed: directory {skill_dir.name!r} != name {name!r}")
    if not isinstance(description, str) or not (1 <= len(description) <= 1024):
        raise ValidationError(f"description must be 1..1024 characters in {skill_dir / 'SKILL.md'}")
    if "when" not in description.lower() and "use" not in description.lower():
        raise ValidationError("description must state when the skill should be used")
    if not body.strip():
        raise ValidationError(f"SKILL.md body is empty: {skill_dir / 'SKILL.md'}")
    if openclaw:
        try:
            bins = metadata["metadata"]["openclaw"]["requires"]["bins"]
        except (KeyError, TypeError) as exc:
            raise ValidationError("OpenClaw metadata.openclaw.requires.bins is missing") from exc
        if bins != ["locron"]:
            raise ValidationError("OpenClaw requires.bins must equal ['locron']")

    total_size = 0
    for path in sorted(skill_dir.rglob("*")):
        if path.is_symlink():
            raise ValidationError(f"path containment violation: symlink is not allowed: {path}")
        if path.is_dir():
            continue
        if not path.is_file():
            raise ValidationError(f"unsupported filesystem entry: {path}")
        total_size += path.stat().st_size
        relative = path.relative_to(skill_dir)
        if relative.parts[0] == "scripts" and not os.access(path, os.X_OK):
            raise ValidationError(f"referenced or packaged script is not executable: {relative}")
        if path.suffix.lower() == ".md":
            text = path.read_text(encoding="utf-8")
            for target in LINK_RE.findall(text):
                target = target.split("#", 1)[0].strip()
                if not target or target.startswith(("https://", "http://", "mailto:")):
                    continue
                decoded = PurePosixPath(target)
                if decoded.is_absolute() or ".." in decoded.parts:
                    raise ValidationError(f"path containment violation in link {target!r} from {relative}")
                resolved = (path.parent / target).resolve()
                try:
                    resolved.relative_to(skill_dir.resolve())
                except ValueError as exc:
                    raise ValidationError(f"path containment violation in link {target!r} from {relative}") from exc
                if not resolved.exists():
                    raise ValidationError(f"broken relative reference {target!r} from {relative}")
            for target in SCRIPT_REF_RE.findall(text):
                clean = target.rstrip(".,;:)")
                script = skill_dir / clean
                if not script.is_file():
                    raise ValidationError(f"referenced script does not exist: {clean}")
                if not os.access(script, os.X_OK):
                    raise ValidationError(f"referenced script is not executable: {clean}")
    if total_size > MAX_CLAWHUB_BYTES:
        raise ValidationError(f"ClawHub package exceeds 50MB: {total_size} bytes")
    return metadata


def load_project(root: Path) -> tuple[str, dict[str, Any], dict[str, Any]]:
    version_path = root / "VERSION"
    try:
        version = version_path.read_text(encoding="utf-8").strip()
    except FileNotFoundError as exc:
        raise ValidationError("missing VERSION") from exc
    if not SEMVER_RE.fullmatch(version):
        raise ValidationError(f"VERSION is not semantic versioning: {version!r}")
    catalog = load_json(root / "catalog.json")
    required_catalog = {"schema", "repository", "publisher", "marketplace", "skills"}
    if not isinstance(catalog, dict) or not required_catalog.issubset(catalog):
        raise ValidationError("catalog.json is missing required keys")
    if catalog["schema"] != "whitekiwi.skills/v1":
        raise ValidationError("catalog.json schema must be whitekiwi.skills/v1")
    if catalog["repository"] != "https://github.com/whitekiwi/skills":
        raise ValidationError("catalog repository URL is invalid")
    if set(catalog["skills"]) != {"locron"}:
        raise ValidationError("catalog must contain exactly the locron skill for this release")
    skill_metadata = _validate_skill_tree(root / "skills/locron")
    if skill_metadata["name"] not in catalog["skills"]:
        raise ValidationError("skill name is missing from catalog metadata")
    openai_yaml_path = root / "skills/locron/agents/openai.yaml"
    try:
        openai_yaml = openai_yaml_path.read_bytes()
    except FileNotFoundError as exc:
        raise ValidationError(f"missing OpenAI skill metadata: {openai_yaml_path}") from exc
    if openai_yaml != _openai_yaml(catalog):
        raise ValidationError("OpenAI skill metadata differs from catalog or default prompt")
    if skill_metadata.get("license") != "MIT-0":
        raise ValidationError("Locron skill license must be MIT-0")
    if not (root / "LICENSE").is_file() or "MIT No Attribution" not in (root / "LICENSE").read_text():
        raise ValidationError("repository LICENSE must contain MIT-0 text")
    for script in sorted((root / "scripts").iterdir()):
        if script.is_file() and script.suffix in {".py", ".sh"} and not os.access(script, os.X_OK):
            raise ValidationError(f"repository script is not executable: {script.relative_to(root)}")
    return version, catalog, skill_metadata


def _source_files(root: Path) -> dict[Path, bytes]:
    skill = root / "skills/locron"
    files: dict[Path, bytes] = {}
    for path in sorted(skill.rglob("*")):
        if path.is_file():
            files[path.relative_to(skill)] = path.read_bytes()
    return files


def _openclaw_skill(source: bytes) -> bytes:
    text = source.decode("utf-8")
    end = text.find("\n---\n", 4)
    if end < 0:
        raise ValidationError("cannot inject OpenClaw metadata into invalid frontmatter")
    injection = "\nmetadata:\n  openclaw:\n    requires:\n      bins:\n        - locron"
    return (text[:end] + injection + text[end:]).encode()


def expected_generated(root: Path) -> dict[Path, bytes]:
    version, catalog, skill_metadata = load_project(root)
    info = catalog["skills"]["locron"]
    publisher = catalog["publisher"]
    repository = catalog["repository"]
    description = skill_metadata["description"]
    keywords = info["keywords"]

    claude_plugin = {
        "name": "locron",
        "version": version,
        "description": description,
        "author": {"name": publisher["name"], "url": publisher["url"]},
        "homepage": "https://github.com/whitekiwi/locron",
        "repository": repository,
        "license": "MIT-0",
        "keywords": keywords,
        "skills": "./skills/",
    }
    codex_plugin = {
        "name": "locron",
        "version": version,
        "description": description,
        "author": {"name": publisher["name"], "url": publisher["url"]},
        "homepage": "https://github.com/whitekiwi/locron",
        "repository": repository,
        "license": "MIT-0",
        "keywords": keywords,
        "skills": "./skills/",
        "interface": {
            "displayName": info["display_name"],
            "shortDescription": info["short_description"],
            "longDescription": description,
            "developerName": publisher["name"],
            "category": info["category"],
            "capabilities": ["Scheduling", "Diagnostics"],
            "websiteURL": "https://github.com/whitekiwi/locron",
            "defaultPrompt": [
                "Preview and safely create a Locron schedule.",
                "Diagnose why a Locron job did not run.",
            ],
        },
    }
    claude_marketplace = {
        "name": catalog["marketplace"]["name"],
        "owner": {"name": publisher["name"], "url": publisher["url"]},
        "metadata": {"description": "Portable Agent Skills published by WhiteKiwi"},
        "plugins": [
            {
                "name": "locron",
                "source": "./plugins/locron",
                "description": info["short_description"],
                "version": version,
            }
        ],
    }
    codex_marketplace = {
        "name": catalog["marketplace"]["name"],
        "interface": {"displayName": catalog["marketplace"]["display_name"]},
        "plugins": [
            {
                "name": "locron",
                "source": {"source": "local", "path": "./plugins/locron"},
                "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
                "category": info["category"],
            }
        ],
    }

    result: dict[Path, bytes] = {
        Path("plugins/locron/.claude-plugin/plugin.json"): _json_bytes(claude_plugin),
        Path("plugins/locron/.codex-plugin/plugin.json"): _json_bytes(codex_plugin),
        Path(".claude-plugin/marketplace.json"): _json_bytes(claude_marketplace),
        Path(".agents/plugins/marketplace.json"): _json_bytes(codex_marketplace),
    }
    for relative, content in _source_files(root).items():
        result[Path("plugins/locron/skills/locron") / relative] = content
        openclaw = _openclaw_skill(content) if relative == Path("SKILL.md") else content
        result[Path("platforms/openclaw/locron") / relative] = openclaw
    return result


def _actual_generated_files(root: Path) -> set[Path]:
    actual: set[Path] = set()
    for directory in GENERATED_DIRS:
        full = root / directory
        if full.exists():
            actual.update(path.relative_to(root) for path in full.rglob("*") if path.is_file())
    actual.update(path for path in GENERATED_FILES if (root / path).is_file())
    return actual


def validate_generated(root: Path) -> None:
    expected = expected_generated(root)
    actual = _actual_generated_files(root)
    if actual != set(expected):
        missing = sorted(str(path) for path in set(expected) - actual)
        extra = sorted(str(path) for path in actual - set(expected))
        raise ValidationError(f"generated file set drift; missing={missing}, extra={extra}")
    for relative, content in expected.items():
        if (root / relative).read_bytes() != content:
            raise ValidationError(f"generated file drift: {relative}; run ./scripts/build.sh")

    version, catalog, metadata = load_project(root)
    for manifest_path in (
        root / "plugins/locron/.claude-plugin/plugin.json",
        root / "plugins/locron/.codex-plugin/plugin.json",
    ):
        manifest = load_json(manifest_path)
        if manifest.get("name") != metadata["name"]:
            raise ValidationError(f"manifest name mismatch: {manifest_path}")
        if manifest.get("version") != version:
            raise ValidationError(f"manifest version mismatch: {manifest_path}")
        skills_path = manifest.get("skills")
        if not isinstance(skills_path, str) or not skills_path.startswith("./") or ".." in PurePosixPath(skills_path).parts:
            raise ValidationError(f"invalid contained skills path: {manifest_path}")
    claude_market = load_json(root / ".claude-plugin/marketplace.json")
    codex_market = load_json(root / ".agents/plugins/marketplace.json")
    if claude_market.get("name") != catalog["marketplace"]["name"]:
        raise ValidationError("Claude marketplace name mismatch")
    if codex_market.get("name") != catalog["marketplace"]["name"]:
        raise ValidationError("Codex marketplace name mismatch")
    for path_value in (
        claude_market["plugins"][0]["source"],
        codex_market["plugins"][0]["source"]["path"],
    ):
        parts = PurePosixPath(path_value).parts
        if not path_value.startswith("./") or ".." in parts:
            raise ValidationError(f"marketplace path escape: {path_value}")
    _validate_skill_tree(root / "plugins/locron/skills/locron")
    _validate_skill_tree(root / "platforms/openclaw/locron", openclaw=True)

    source = _source_files(root)
    generated_skill = {
        path.relative_to(root / "plugins/locron/skills/locron"): path.read_bytes()
        for path in (root / "plugins/locron/skills/locron").rglob("*")
        if path.is_file()
    }
    if source != generated_skill:
        raise ValidationError("generated plugin skill is not byte-equivalent to authored source")
    _, source_body, _ = parse_frontmatter(root / "skills/locron/SKILL.md")
    _, claw_body, _ = parse_frontmatter(root / "platforms/openclaw/locron/SKILL.md")
    if source_body != claw_body:
        raise ValidationError("OpenClaw Markdown body differs from authored source")


def write_generated(root: Path) -> None:
    expected = expected_generated(root)
    for directory in GENERATED_DIRS:
        target = root / directory
        if target.exists():
            if target.is_symlink() or not target.is_dir():
                raise ValidationError(f"refusing to replace unsafe generated path: {target}")
            shutil.rmtree(target)
    for relative in GENERATED_FILES:
        target = root / relative
        if target.is_symlink():
            raise ValidationError(f"refusing to replace symlinked generated file: {target}")
    for relative, content in expected.items():
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)


def _copy_payload(source_files: Iterable[tuple[Path, bytes]], destination: Path) -> None:
    for relative, content in source_files:
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)


def _zip_tree(source: Path, archive: Path, root_name: str = "locron") -> None:
    archive.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as output:
        for path in sorted(item for item in source.rglob("*") if item.is_file()):
            relative = path.relative_to(source).as_posix()
            info = zipfile.ZipInfo(f"{root_name}/{relative}", ZIP_TIME)
            info.create_system = 3
            executable = bool(path.stat().st_mode & stat.S_IXUSR)
            info.external_attr = ((0o755 if executable else 0o644) & 0xFFFF) << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            output.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)


def build(root: Path, dist: Path) -> None:
    write_generated(root)
    validate_generated(root)
    marker_name = ".locron-skill-dist"
    if dist.exists():
        if dist.is_symlink() or not dist.is_dir():
            raise ValidationError(f"refusing to replace unsafe dist path: {dist}")
        if not (dist / marker_name).is_file():
            raise ValidationError(f"refusing to replace unmarked dist directory: {dist}")
        shutil.rmtree(dist)
    dist.mkdir(parents=True)
    (dist / marker_name).write_text("generated by whitekiwi/skills\n", encoding="utf-8")

    plugin_source = root / "plugins/locron"
    shared_skill = [
        (path.relative_to(plugin_source), path.read_bytes())
        for path in sorted((plugin_source / "skills/locron").rglob("*"))
        if path.is_file()
    ]
    claude_files = shared_skill + [
        (Path(".claude-plugin/plugin.json"), (plugin_source / ".claude-plugin/plugin.json").read_bytes())
    ]
    codex_files = shared_skill + [
        (Path(".codex-plugin/plugin.json"), (plugin_source / ".codex-plugin/plugin.json").read_bytes())
    ]
    _copy_payload(claude_files, dist / "claude/locron")
    _copy_payload(codex_files, dist / "codex/locron")
    _copy_payload(
        (
            (path.relative_to(root / "platforms/openclaw/locron"), path.read_bytes())
            for path in sorted((root / "platforms/openclaw/locron").rglob("*"))
            if path.is_file()
        ),
        dist / "openclaw/locron",
    )
    _copy_payload(
        ((path.relative_to(root / "skills/locron"), path.read_bytes()) for path in sorted((root / "skills/locron").rglob("*")) if path.is_file()),
        dist / "skill/locron",
    )

    version = (root / "VERSION").read_text().strip()
    archives = [
        (dist / "claude/locron", dist / f"locron-claude-{version}.zip"),
        (dist / "openclaw/locron", dist / f"locron-openclaw-{version}.zip"),
        (dist / "codex/locron", dist / f"locron-codex-{version}.zip"),
        (dist / "skill/locron", dist / f"locron-skill-{version}.zip"),
    ]
    for source, archive in archives:
        _zip_tree(source, archive)
    checksum_lines = []
    for _, archive in sorted(archives, key=lambda item: item[1].name):
        digest = hashlib.sha256(archive.read_bytes()).hexdigest()
        checksum_lines.append(f"{digest}  {archive.name}")
    (dist / "SHA256SUMS").write_text("\n".join(checksum_lines) + "\n", encoding="utf-8")


def validate_dist(root: Path, dist: Path) -> None:
    if (dist / ".locron-skill-dist").read_text(encoding="utf-8") != "generated by whitekiwi/skills\n":
        raise ValidationError("dist marker is missing or invalid")
    version = (root / "VERSION").read_text().strip()
    expected_names = {
        f"locron-claude-{version}.zip",
        f"locron-openclaw-{version}.zip",
        f"locron-codex-{version}.zip",
        f"locron-skill-{version}.zip",
    }
    checksum_path = dist / "SHA256SUMS"
    entries: dict[str, str] = {}
    for line in checksum_path.read_text(encoding="utf-8").splitlines():
        digest, name = line.split("  ", 1)
        entries[name] = digest
    if set(entries) != expected_names:
        raise ValidationError("SHA256SUMS does not list exactly the release archives")
    for name, digest in entries.items():
        actual = hashlib.sha256((dist / name).read_bytes()).hexdigest()
        if actual != digest:
            raise ValidationError(f"checksum mismatch: {name}")
        with zipfile.ZipFile(dist / name) as archive:
            members = archive.namelist()
            if not members or any(PurePosixPath(member).is_absolute() or ".." in PurePosixPath(member).parts for member in members):
                raise ValidationError(f"unsafe or empty archive: {name}")
            manifest_kinds = {
                ".claude-plugin/plugin.json": any(member.endswith("/.claude-plugin/plugin.json") for member in members),
                ".codex-plugin/plugin.json": any(member.endswith("/.codex-plugin/plugin.json") for member in members),
            }
            if "claude" in name and manifest_kinds != {".claude-plugin/plugin.json": True, ".codex-plugin/plugin.json": False}:
                raise ValidationError("Claude archive contains the wrong platform manifest")
            if "codex" in name and manifest_kinds != {".claude-plugin/plugin.json": False, ".codex-plugin/plugin.json": True}:
                raise ValidationError("Codex archive contains the wrong platform manifest")
            if ("openclaw" in name or "skill" in name) and any(manifest_kinds.values()):
                raise ValidationError(f"{name} contains an unrelated plugin manifest")


def validate_all(root: Path, *, require_dist: bool = False) -> None:
    load_project(root)
    validate_generated(root)
    if require_dist:
        validate_dist(root, root / "dist")
