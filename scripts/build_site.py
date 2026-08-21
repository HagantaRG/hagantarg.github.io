#!/usr/bin/env python3
"""Build the project index from TOML metadata and Markdown descriptions."""

from __future__ import annotations

import argparse
import html
import shutil
import tomllib
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

import markdown


ROOT = Path(__file__).resolve().parent.parent
PLACEHOLDERS = {
    "current": "{{ current_projects }}",
    "archive": "{{ archive_projects }}",
}
ABOUT_SECTION = "About Myself"
ABOUT_PLACEHOLDER = "{{ about_myself }}"
REQUIRED_FIELDS = {"name", "languages", "link", "description"}
DIARY_FIELDS = {"title", "date", "content"}
DIARY_PLACEHOLDER = "{{ diary_entries }}"
DIARY_IMAGE_SUFFIXES = {".gif", ".jpeg", ".jpg", ".png", ".svg", ".webp"}


def render_markdown(markdown_text: str) -> str:
    """Render repository-controlled Markdown into HTML."""
    return markdown.markdown(
        markdown_text,
        extensions=["extra", "sane_lists"],
        output_format="html5",
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


def resolve_diary_content(relative_path: str) -> Path:
    path = (ROOT / relative_path).resolve()
    diary_root = (ROOT / "diary").resolve()
    if path.parent != diary_root or path.suffix.lower() != ".md":
        raise ValueError(
            f"Diary content must be a Markdown file directly inside diary/: "
            f"{relative_path}"
        )
    if not path.is_file():
        raise FileNotFoundError(f"Diary content file not found: {relative_path}")
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
            "            <details>",
            '              <summary class="project-heading">',
            f'                <span class="project-name">{name}</span>',
            f'                <span class="languages">{languages}</span>',
            "              </summary>",
            f'              <div class="description">{description}</div>',
            f'              <a class="project-link" href="{link}">View project →</a>',
            "            </details>",
            "          </li>",
        )
    )


def validate_diary_entry(entry: dict[str, object]) -> None:
    missing = DIARY_FIELDS - entry.keys()
    extra = entry.keys() - DIARY_FIELDS
    if missing or extra:
        raise ValueError(
            f"Invalid diary entry fields; missing={sorted(missing)}, "
            f"extra={sorted(extra)}"
        )

    if not isinstance(entry["title"], str) or not entry["title"].strip():
        raise ValueError(f"Diary title must be a non-empty string: {entry!r}")
    if type(entry["date"]) is not date:
        raise ValueError(f"Diary date must be a TOML local date: {entry!r}")
    if not isinstance(entry["content"], str):
        raise ValueError(f"Diary content must be a Markdown file path: {entry!r}")
    resolve_diary_content(entry["content"])


def render_diary_entry(entry: dict[str, object]) -> str:
    title = html.escape(str(entry["title"]))
    entry_date = entry["date"]
    if type(entry_date) is not date:
        raise TypeError("Validated diary date is not a date")
    machine_date = entry_date.isoformat()
    display_date = f"{entry_date.strftime('%B')} {entry_date.day}, {entry_date.year}"
    content_path = resolve_diary_content(str(entry["content"]))
    content = render_markdown(content_path.read_text(encoding="utf-8"))
    return "\n".join(
        (
            '        <article class="diary-entry">',
            "          <header>",
            f"            <h2>{title}</h2>",
            f'            <time datetime="{machine_date}">{display_date}</time>',
            "          </header>",
            f'          <div class="description">{content}</div>',
            "        </article>",
        )
    )


def build_projects_page() -> str:
    with (ROOT / "projects.toml").open("rb") as project_file:
        project_data = tomllib.load(project_file)

    expected_sections = set(PLACEHOLDERS) | {ABOUT_SECTION}
    if set(project_data) != expected_sections:
        raise ValueError(
            "projects.toml must contain only About Myself, current, and archive sections"
        )

    template = (ROOT / "templates" / "index.html").read_text(encoding="utf-8")
    seen_links: set[str] = set()

    about_entries = project_data[ABOUT_SECTION]
    if not isinstance(about_entries, list) or len(about_entries) != 1:
        raise ValueError("About Myself must contain exactly one TOML table")
    about = about_entries[0]
    if not isinstance(about, dict) or set(about) != {"description"}:
        raise ValueError("About Myself must contain only a description field")
    about_path_value = about["description"]
    if not isinstance(about_path_value, str):
        raise ValueError("About Myself description must be a Markdown file path")
    about_path = resolve_description(about_path_value)
    about_html = render_markdown(about_path.read_text(encoding="utf-8"))
    if template.count(ABOUT_PLACEHOLDER) != 1:
        raise ValueError(
            f"Template must contain exactly one {ABOUT_PLACEHOLDER} placeholder"
        )
    template = template.replace(ABOUT_PLACEHOLDER, about_html)

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

    return template


def build_diary_page() -> str:
    with (ROOT / "diary.toml").open("rb") as diary_file:
        diary_data = tomllib.load(diary_file)

    if set(diary_data) != {"entry"}:
        raise ValueError("diary.toml must contain only entry tables")
    entries = diary_data["entry"]
    if not isinstance(entries, list) or not entries:
        raise ValueError("diary.toml must contain at least one entry")

    seen_content: set[str] = set()
    for entry in entries:
        if not isinstance(entry, dict):
            raise ValueError("Each diary entry must be a TOML table")
        validate_diary_entry(entry)
        content_path = str(entry["content"])
        if content_path in seen_content:
            raise ValueError(f"Duplicate diary content path: {content_path}")
        seen_content.add(content_path)

    template = (ROOT / "templates" / "diary.html").read_text(encoding="utf-8")
    if template.count(DIARY_PLACEHOLDER) != 1:
        raise ValueError(
            f"Template must contain exactly one {DIARY_PLACEHOLDER} placeholder"
        )
    newest_entries_first = sorted(
        entries,
        key=lambda entry: entry["date"],
        reverse=True,
    )
    rendered = "\n".join(render_diary_entry(entry) for entry in newest_entries_first)
    return template.replace(DIARY_PLACEHOLDER, rendered)


def copy_diary_images(output_dir: Path) -> None:
    diary_output_dir = output_dir / "diary"
    diary_output_dir.mkdir(parents=True, exist_ok=True)

    for source_path in (ROOT / "diary").iterdir():
        is_supported_image = (
            source_path.is_file()
            and source_path.suffix.lower() in DIARY_IMAGE_SUFFIXES
        )
        if is_supported_image:
            shutil.copyfile(source_path, diary_output_dir / source_path.name)


def build(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "index.html").write_text(
        build_projects_page(), encoding="utf-8", newline="\n"
    )
    (output_dir / "diary.html").write_text(
        build_diary_page(), encoding="utf-8", newline="\n"
    )
    shutil.copyfile(ROOT / "assets" / "styles.css", output_dir / "styles.css")
    copy_diary_images(output_dir)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "_site",
        help="Directory for the generated site",
    )
    args = parser.parse_args()
    output_dir = args.output.resolve()
    build(output_dir)
    print(f"Built {output_dir}")


if __name__ == "__main__":
    main()
