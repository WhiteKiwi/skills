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

GENERATED_ROOTS = (Path("plugins"), Path("platforms/openclaw"))
GENERATED_FILES = (
    Path(".claude-plugin/marketplace.json"),
    Path(".agents/plugins/marketplace.json"),
)


class ValidationError(Exception):
    pass


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode()


def _openai_yaml(catalog: dict[str, Any], skill_name: str) -> bytes:
    info = catalog["skills"][skill_name]
    return (
        "interface:\n"
        f'  display_name: "{info["display_name"]}"\n'
        f'  short_description: "{info["short_description"]}"\n'
        f'  default_prompt: "{info["default_prompt"]}"\n'
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


def _validate_skill_tree(
    skill_dir: Path, *, openclaw: bool = False, required_bins: list[str] | None = None
) -> dict[str, Any]:
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
        if bins != required_bins:
            raise ValidationError(f"OpenClaw requires.bins must equal {required_bins!r}")

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


def load_project(root: Path) -> tuple[str, dict[str, Any], dict[str, dict[str, Any]]]:
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
    skills = catalog["skills"]
    if not isinstance(skills, dict) or not skills:
        raise ValidationError("catalog must contain at least one skill")
    authored_root = root / "skills"
    authored_names = {path.name for path in authored_root.iterdir() if path.is_dir()}
    if authored_names != set(skills):
        raise ValidationError(
            f"catalog/authored skill mismatch; catalog={sorted(skills)}, authored={sorted(authored_names)}"
        )
    skill_metadata: dict[str, dict[str, Any]] = {}
    required_info = {
        "display_name",
        "short_description",
        "category",
        "homepage",
        "required_bins",
        "capabilities",
        "default_prompt",
        "default_prompts",
        "keywords",
        "clawhub",
    }
    for skill_name, info in sorted(skills.items()):
        if not isinstance(info, dict) or not required_info.issubset(info):
            raise ValidationError(f"catalog metadata is incomplete for skill {skill_name!r}")
        if not NAME_RE.fullmatch(skill_name):
            raise ValidationError(f"invalid catalog skill name: {skill_name!r}")
        if not isinstance(info["required_bins"], list) or not info["required_bins"]:
            raise ValidationError(f"required_bins must be a non-empty list for {skill_name}")
        if not isinstance(info["capabilities"], list) or not info["capabilities"]:
            raise ValidationError(f"capabilities must be a non-empty list for {skill_name}")
        if not isinstance(info["default_prompts"], list) or not info["default_prompts"]:
            raise ValidationError(f"default_prompts must be a non-empty list for {skill_name}")
        metadata = _validate_skill_tree(authored_root / skill_name)
        if metadata["name"] != skill_name:
            raise ValidationError(f"skill name is missing from catalog metadata: {skill_name}")
        openai_yaml_path = authored_root / skill_name / "agents/openai.yaml"
        try:
            openai_yaml = openai_yaml_path.read_bytes()
        except FileNotFoundError as exc:
            raise ValidationError(f"missing OpenAI skill metadata: {openai_yaml_path}") from exc
        if openai_yaml != _openai_yaml(catalog, skill_name):
            raise ValidationError(f"OpenAI skill metadata differs for {skill_name}")
        if metadata.get("license") != "MIT-0":
            raise ValidationError(f"{skill_name} skill license must be MIT-0")
        skill_metadata[skill_name] = metadata
    if not (root / "LICENSE").is_file() or "MIT No Attribution" not in (root / "LICENSE").read_text():
        raise ValidationError("repository LICENSE must contain MIT-0 text")
    for script in sorted((root / "scripts").iterdir()):
        if script.is_file() and script.suffix in {".py", ".sh"} and not os.access(script, os.X_OK):
            raise ValidationError(f"repository script is not executable: {script.relative_to(root)}")
    return version, catalog, skill_metadata


def _source_files(root: Path, skill_name: str) -> dict[Path, bytes]:
    skill = root / "skills" / skill_name
    files: dict[Path, bytes] = {}
    for path in sorted(skill.rglob("*")):
        if path.is_file():
            files[path.relative_to(skill)] = path.read_bytes()
    return files


def _payload_mode(path: Path) -> int:
    return 0o755 if path.stat().st_mode & stat.S_IXUSR else 0o644


def _openclaw_skill(source: bytes, required_bins: list[str]) -> bytes:
    text = source.decode("utf-8")
    end = text.find("\n---\n", 4)
    if end < 0:
        raise ValidationError("cannot inject OpenClaw metadata into invalid frontmatter")
    bins = "".join(f"\n        - {name}" for name in required_bins)
    injection = "\nmetadata:\n  openclaw:\n    requires:\n      bins:" + bins
    return (text[:end] + injection + text[end:]).encode()


def expected_generated(root: Path) -> dict[Path, bytes]:
    version, catalog, skill_metadata = load_project(root)
    publisher = catalog["publisher"]
    repository = catalog["repository"]
    result: dict[Path, bytes] = {}
    claude_plugins = []
    codex_plugins = []
    for skill_name, metadata in sorted(skill_metadata.items()):
        info = catalog["skills"][skill_name]
        description = metadata["description"]
        claude_plugin = {
            "name": skill_name,
            "version": version,
            "description": description,
            "author": {"name": publisher["name"], "url": publisher["url"]},
            "homepage": info["homepage"],
            "repository": repository,
            "license": "MIT-0",
            "keywords": info["keywords"],
            "skills": "./skills/",
        }
        codex_plugin = {
            **claude_plugin,
            "interface": {
                "displayName": info["display_name"],
                "shortDescription": info["short_description"],
                "longDescription": description,
                "developerName": publisher["name"],
                "category": info["category"],
                "capabilities": info["capabilities"],
                "websiteURL": info["homepage"],
                "defaultPrompt": info["default_prompts"],
            },
        }
        result[Path(f"plugins/{skill_name}/.claude-plugin/plugin.json")] = _json_bytes(claude_plugin)
        result[Path(f"plugins/{skill_name}/.codex-plugin/plugin.json")] = _json_bytes(codex_plugin)
        for relative, content in _source_files(root, skill_name).items():
            result[Path(f"plugins/{skill_name}/skills/{skill_name}") / relative] = content
            openclaw = (
                _openclaw_skill(content, info["required_bins"])
                if relative == Path("SKILL.md")
                else content
            )
            result[Path(f"platforms/openclaw/{skill_name}") / relative] = openclaw
        claude_plugins.append(
            {
                "name": skill_name,
                "source": f"./plugins/{skill_name}",
                "description": info["short_description"],
                "version": version,
            }
        )
        codex_plugins.append(
            {
                "name": skill_name,
                "source": {"source": "local", "path": f"./plugins/{skill_name}"},
                "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
                "category": info["category"],
            }
        )

    claude_marketplace = {
        "name": catalog["marketplace"]["name"],
        "owner": {"name": publisher["name"], "url": publisher["url"]},
        "metadata": {"description": "Portable Agent Skills published by WhiteKiwi"},
        "plugins": claude_plugins,
    }
    codex_marketplace = {
        "name": catalog["marketplace"]["name"],
        "interface": {"displayName": catalog["marketplace"]["display_name"]},
        "plugins": codex_plugins,
    }
    result[Path(".claude-plugin/marketplace.json")] = _json_bytes(claude_marketplace)
    result[Path(".agents/plugins/marketplace.json")] = _json_bytes(codex_marketplace)
    return result


def _actual_generated_files(root: Path) -> set[Path]:
    actual: set[Path] = set()
    for directory in GENERATED_ROOTS:
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
    for skill_name in sorted(metadata):
        for manifest_path in (
            root / f"plugins/{skill_name}/.claude-plugin/plugin.json",
            root / f"plugins/{skill_name}/.codex-plugin/plugin.json",
        ):
            manifest = load_json(manifest_path)
            if manifest.get("name") != skill_name:
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
    if {item["name"] for item in claude_market["plugins"]} != set(metadata):
        raise ValidationError("Claude marketplace skill set mismatch")
    if {item["name"] for item in codex_market["plugins"]} != set(metadata):
        raise ValidationError("Codex marketplace skill set mismatch")
    for item in claude_market["plugins"]:
        path_value = item["source"]
        parts = PurePosixPath(path_value).parts
        if not path_value.startswith("./") or ".." in parts:
            raise ValidationError(f"marketplace path escape: {path_value}")
    for item in codex_market["plugins"]:
        path_value = item["source"]["path"]
        parts = PurePosixPath(path_value).parts
        if not path_value.startswith("./") or ".." in parts:
            raise ValidationError(f"marketplace path escape: {path_value}")

    for skill_name in sorted(metadata):
        info = catalog["skills"][skill_name]
        generated_root = root / f"plugins/{skill_name}/skills/{skill_name}"
        _validate_skill_tree(generated_root)
        _validate_skill_tree(
            root / f"platforms/openclaw/{skill_name}",
            openclaw=True,
            required_bins=info["required_bins"],
        )
        source = _source_files(root, skill_name)
        generated_skill = {
            path.relative_to(generated_root): path.read_bytes()
            for path in generated_root.rglob("*")
            if path.is_file()
        }
        if source != generated_skill:
            raise ValidationError(f"generated {skill_name} plugin is not byte-equivalent to authored source")
        for relative in source:
            source_mode = _payload_mode(root / "skills" / skill_name / relative)
            for payload_root in (generated_root, root / "platforms/openclaw" / skill_name):
                if _payload_mode(payload_root / relative) != source_mode:
                    raise ValidationError(f"generated executable mode drift: {payload_root / relative}")
        _, source_body, _ = parse_frontmatter(root / f"skills/{skill_name}/SKILL.md")
        _, claw_body, _ = parse_frontmatter(root / f"platforms/openclaw/{skill_name}/SKILL.md")
        if source_body != claw_body:
            raise ValidationError(f"OpenClaw Markdown body differs for {skill_name}")


def write_generated(root: Path) -> None:
    expected = expected_generated(root)
    for directory in GENERATED_ROOTS:
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
        target.chmod(0o644)

    catalog = load_json(root / "catalog.json")
    for skill_name in sorted(catalog["skills"]):
        source_root = root / "skills" / skill_name
        for source in sorted(source_root.rglob("*")):
            if source.is_file():
                relative = source.relative_to(source_root)
                mode = _payload_mode(source)
                for payload_root in (
                    root / "plugins" / skill_name / "skills" / skill_name,
                    root / "platforms/openclaw" / skill_name,
                ):
                    (payload_root / relative).chmod(mode)


def _copy_payload(source_files: Iterable[tuple[Path, Path]], destination: Path) -> None:
    for relative, source in source_files:
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        target.chmod(_payload_mode(source))


def _zip_tree(source: Path, archive: Path, root_name: str) -> None:
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
    marker_name = ".whitekiwi-skills-dist"
    if dist.exists():
        if dist.is_symlink() or not dist.is_dir():
            raise ValidationError(f"refusing to replace unsafe dist path: {dist}")
        if not (dist / marker_name).is_file():
            raise ValidationError(f"refusing to replace unmarked dist directory: {dist}")
        shutil.rmtree(dist)
    dist.mkdir(parents=True)
    (dist / marker_name).write_text("generated by whitekiwi/skills\n", encoding="utf-8")

    version, catalog, _ = load_project(root)
    archives: list[tuple[Path, Path, str]] = []
    for skill_name in sorted(catalog["skills"]):
        plugin_source = root / "plugins" / skill_name
        generated_skill = plugin_source / "skills" / skill_name
        shared_skill = [
            (path.relative_to(plugin_source), path)
            for path in sorted(generated_skill.rglob("*"))
            if path.is_file()
        ]
        claude_files = shared_skill + [
            (Path(".claude-plugin/plugin.json"), plugin_source / ".claude-plugin/plugin.json")
        ]
        codex_files = shared_skill + [
            (Path(".codex-plugin/plugin.json"), plugin_source / ".codex-plugin/plugin.json")
        ]
        _copy_payload(claude_files, dist / f"claude/{skill_name}")
        _copy_payload(codex_files, dist / f"codex/{skill_name}")
        openclaw_root = root / "platforms/openclaw" / skill_name
        _copy_payload(
            (
                (path.relative_to(openclaw_root), path)
                for path in sorted(openclaw_root.rglob("*"))
                if path.is_file()
            ),
            dist / f"openclaw/{skill_name}",
        )
        authored_root = root / "skills" / skill_name
        _copy_payload(
            (
                (path.relative_to(authored_root), path)
                for path in sorted(authored_root.rglob("*"))
                if path.is_file()
            ),
            dist / f"skill/{skill_name}",
        )
        archives.extend(
            [
                (dist / f"claude/{skill_name}", dist / f"{skill_name}-claude-{version}.zip", skill_name),
                (dist / f"openclaw/{skill_name}", dist / f"{skill_name}-openclaw-{version}.zip", skill_name),
                (dist / f"codex/{skill_name}", dist / f"{skill_name}-codex-{version}.zip", skill_name),
                (dist / f"skill/{skill_name}", dist / f"{skill_name}-skill-{version}.zip", skill_name),
            ]
        )
    for source, archive, skill_name in archives:
        _zip_tree(source, archive, skill_name)
    checksum_lines = []
    for _, archive, _ in sorted(archives, key=lambda item: item[1].name):
        digest = hashlib.sha256(archive.read_bytes()).hexdigest()
        checksum_lines.append(f"{digest}  {archive.name}")
    (dist / "SHA256SUMS").write_text("\n".join(checksum_lines) + "\n", encoding="utf-8")


def validate_dist(root: Path, dist: Path) -> None:
    if (dist / ".whitekiwi-skills-dist").read_text(encoding="utf-8") != "generated by whitekiwi/skills\n":
        raise ValidationError("dist marker is missing or invalid")
    version, catalog, _ = load_project(root)
    expected_names = {
        f"{skill_name}-{platform}-{version}.zip"
        for skill_name in catalog["skills"]
        for platform in ("claude", "openclaw", "codex", "skill")
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
