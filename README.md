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
`descriptions` directory. Python-Markdown renders headings, emphasis, lists,
links, blockquotes, code blocks, tables, and other standard Markdown formatting.
Project descriptions are displayed in collapsed disclosure panels on the site.

The About Myself section uses a quoted TOML table name because it contains a
space:

```toml
[["About Myself"]]
description = "descriptions/ABOUTME.md"
```

Edit `descriptions/ABOUTME.md` to update the biography displayed above the
project sections. Exactly one `About Myself` table is required.

Build the site locally with:

```powershell
python -m pip install --requirement requirements.txt
python scripts/build_site.py
```

The generated page is written to `_site/index.html`. GitHub Actions runs this
command and deploys `_site` automatically whenever `main` changes.
