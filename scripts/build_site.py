#!/usr/bin/env python3
"""Build the project index from TOML metadata and Markdown descriptions."""

from __future__ import annotations

import argparse
import html
import re
import tomllib
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parent.parent
LINK_PATTERN = re.compile(r"\[([^\]]+)]\((https?://[^\s)]+)\)")
PLACEHOLDERS = {
    "current": "{{ current_projects }}",
    "archive": "{{ archive_projects }}",
}
REQUIRED_FIELDS = {"name", "languages", "link", "description"}


def render_inline_markdown(text: str) -> str:
    """Render safe Markdown links while escaping all other HTML."""
    output: list[str] = []
    position = 0
    for match in LINK_PATTERN.finditer(text):
        output.append(html.escape(text[position : match.start()]))
        label, url = match.groups()
        output.append(
            f'<a href="{html.escape(url, quote=True)}">{html.escape(label)}</a>'
        )
        position = match.end()
    output.append(html.escape(text[position:]))
    return "".join(output)


def render_markdown(markdown: str) -> str:
    """Render paragraphs and links from a small, safe Markdown subset."""
    paragraphs = re.split(r"\n\s*\n", markdown.strip())
    return "\n".join(
        f"<p>{render_inline_markdown(' '.join(paragraph.splitlines()))}</p>"
        for paragraph in paragraphs
        if paragraph.strip()
    )


def resolve_description(relative_path: str) -> Path:
    path = (ROOT / relative_path).resolve()
    descriptions_root = (ROOT / "descriptions").resolve()
    if path.parent != descriptions_root or path.suffix.lower() != ".md":
        raise ValueError(
            f"Description must be a Markdown file directly inside descriptions/: "
            f"{relative_path}"
        )
    if not path.is_file():
        raise FileNotFoundError(f"Description file not found: {relative_path}")
    return path


def validate_project(project: dict[str, object], section: str) -> None:
    missing = REQUIRED_FIELDS - project.keys()
    extra = project.keys() - REQUIRED_FIELDS
    if missing or extra:
        raise ValueError(
            f"Invalid fields in {section} project {project!r}; "
            f"missing={sorted(missing)}, extra={sorted(extra)}"
        )

    if not isinstance(project["name"], str) or not project["name"].strip():
        raise ValueError(f"Project name must be a non-empty string: {project!r}")

    languages = project["languages"]
    if (
        not isinstance(languages, list)
        or not languages
        or not all(isinstance(language, str) and language.strip() for language in languages)
    ):
        raise ValueError(f"Project languages must be a non-empty string array: {project!r}")

    link = project["link"]
    if not isinstance(link, str) or urlparse(link).scheme != "https":
        raise ValueError(f"Project link must be an HTTPS URL: {project!r}")

    description = project["description"]
    if not isinstance(description, str):
        raise ValueError(f"Project description must be a Markdown file path: {project!r}")
    resolve_description(description)


def render_project(project: dict[str, object]) -> str:
    name = html.escape(str(project["name"]))
    link = html.escape(str(project["link"]), quote=True)
    languages = ", ".join(html.escape(str(item)) for item in project["languages"])
    description_path = resolve_description(str(project["description"]))
    description = render_markdown(description_path.read_text(encoding="utf-8"))
    return "\n".join(
        (
            "          <li>",
            '            <div class="project-heading">',
            f'              <a href="{link}">{name}</a>',
            f'              <span class="languages">{languages}</span>',
            "            </div>",
            f'            <div class="description">{description}</div>',
            "          </li>",
        )
    )


def build(output: Path) -> None:
    with (ROOT / "projects.toml").open("rb") as project_file:
        project_data = tomllib.load(project_file)

    if set(project_data) != set(PLACEHOLDERS):
        raise ValueError("projects.toml must contain only current and archive sections")

    template = (ROOT / "templates" / "index.html").read_text(encoding="utf-8")
    seen_links: set[str] = set()

    for section, placeholder in PLACEHOLDERS.items():
        projects = project_data[section]
        if not isinstance(projects, list):
            raise ValueError(f"{section} must be an array of projects")

        for project in projects:
            if not isinstance(project, dict):
                raise ValueError(f"Each {section} entry must be a TOML table")
            validate_project(project, section)
            link = str(project["link"])
            if link in seen_links:
                raise ValueError(f"Duplicate project link: {link}")
            seen_links.add(link)

        rendered = "\n".join(render_project(project) for project in projects)
        if template.count(placeholder) != 1:
            raise ValueError(f"Template must contain exactly one {placeholder} placeholder")
        template = template.replace(placeholder, rendered)

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(template, encoding="utf-8", newline="\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "_site" / "index.html",
        help="Path for the generated HTML file",
    )
    args = parser.parse_args()
    build(args.output.resolve())
    print(f"Built {args.output.resolve()}")


if __name__ == "__main__":
    main()
