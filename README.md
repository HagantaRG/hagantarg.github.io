# hagantarg.github.io

## Updating projects

Project cards are generated from [`projects.toml`](projects.toml). Add a project
to either the `[[current]]` or `[[archive]]` array with these fields:

```toml
[[current]]
name = "project-name"
languages = ["Python", "HTML"]
link = "https://github.com/HagantaRG/project-name"
description = "descriptions/project-name.md"
```

The `description` value must point to a Markdown file directly inside the
`descriptions` directory. The renderer supports paragraphs and Markdown links.

Build the site locally with:

```powershell
python scripts/build_site.py
```

The generated page is written to `_site/index.html`. GitHub Actions runs this
command and deploys `_site` automatically whenever `main` changes.
