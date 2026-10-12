# Relayworks

A local automation showcase with workplace demos, spreadsheet and document imports, workflow examples, and illustrated guidebooks.

**Status:** Local workflow demonstration  
**Built with:** Python standard library, HTML/CSS/JavaScript, optional OCR tools

## Reading order

1. Read the root README for project purpose and setup navigation.
2. Follow the entry points below to find the implementation.
3. Use the file guide to locate individual modules, tests, assets, and configuration.
4. Check component licenses before redistributing dependencies or assets.

## Important paths

- [START_HERE.html](../START_HERE.html) — Browser document: Start here · Relayworks; provides page structure and may include inline styles or application logic.
- [PROJECT_NOTES.md](../PROJECT_NOTES.md) — Preserved detailed setup, usage, architecture, and development notes from the earlier README.
- [app/server.py](../app/server.py) — Relayworks: local portal + separately authenticated workplace HTTP API. Defines `Server`, `Handler`, `csv_bytes`, `scheduler`, `main`.
- [books/THE_WORKS.md](../books/THE_WORKS.md) — Documentation: The Works. Covers 00. How to use this book; Your controls; The learning route.

## Structure

| Path | Role |
| --- | --- |
| [app/](../app/) | Application modules and user interface (5 tracked entries). |
| [books/](../books/) | Guidebooks, printable editions, and their supporting files (16 tracked entries). |
| [diagrams/](../diagrams/) | Project-specific diagrams components (11 tracked entries). |
| [docs/](../docs/) | Project documentation, decisions, and reference material (22 tracked entries). |
| [evidence/](../evidence/) | Project-specific evidence components (136 tracked entries). |
| [fixtures/](../fixtures/) | Project-specific fixtures components (4 tracked entries). |
| [free_intro_1/](../free_intro_1/) | Project-specific free intro 1 components (925 tracked entries). |
| [practice_files/](../practice_files/) | Practice input documents and spreadsheets (26 tracked entries). |
| [scripts/](../scripts/) | Build, launch, maintenance, and verification commands (9 tracked entries). |
| [tests/](../tests/) | Automated checks and test fixtures (4 tracked entries). |
| [web/](../web/) | Browser application source (5 tracked entries). |

## Useful commands

Run from the repository root after following the documented prerequisites.

```sh
python3 app/server.py
# Tests:
python3 -m unittest discover -s tests -v
```

## Scope

Examples and practice records are demonstration material. Google Sheets and OpenF1 reads require their own network access and provider terms. Optional Poppler and Tesseract are installed separately.

## Maintaining the guide

The file catalog is a source-inspection snapshot, not proof that every runtime path works. Update it when moving files or changing module responsibilities. The 2026-10-12 documentation review did not run every application, deploy services, or validate all historical performance claims.
