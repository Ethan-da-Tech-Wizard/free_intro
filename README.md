# Relayworks

A local automation showcase with workplace demos, spreadsheet and document imports, workflow examples, and illustrated guidebooks.

**Status:** Local workflow demonstration  
**Built with:** Python standard library, HTML/CSS/JavaScript, optional OCR tools

[Project guide](docs/PROJECT_GUIDE.md) · [Every file explained](docs/FILE_GUIDE.md) · [Licenses and dependencies](docs/LICENSE_REVIEW.md)

## Start here

- [START_HERE.html](START_HERE.html) — Browser document: Start here · Relayworks; provides page structure and may include inline styles or application logic.
- [PROJECT_NOTES.md](PROJECT_NOTES.md) — Preserved detailed setup, usage, architecture, and development notes from the earlier README.
- [app/server.py](app/server.py) — Relayworks: local portal + separately authenticated workplace HTTP API. Defines `Server`, `Handler`, `csv_bytes`, `scheduler`, `main`.
- [books/THE_WORKS.md](books/THE_WORKS.md) — Documentation: The Works. Covers 00. How to use this book; Your controls; The learning route.

The following commands are taken from this project’s source/configuration. Install its prerequisites first.

```sh
python3 app/server.py
# Tests:
python3 -m unittest discover -s tests -v
```

[Detailed setup, usage, and development notes](PROJECT_NOTES.md) preserve the previous project documentation.

## Repository layout

| Path | Role |
| --- | --- |
| [app/](app/) | Application modules and user interface (5 tracked entries). |
| [books/](books/) | Guidebooks, printable editions, and their supporting files (16 tracked entries). |
| [diagrams/](diagrams/) | Project-specific diagrams components (11 tracked entries). |
| [docs/](docs/) | Project documentation, decisions, and reference material (22 tracked entries). |
| [evidence/](evidence/) | Project-specific evidence components (136 tracked entries). |
| [fixtures/](fixtures/) | Project-specific fixtures components (4 tracked entries). |
| [free_intro_1/](free_intro_1/) | Project-specific free intro 1 components (925 tracked entries). |
| [practice_files/](practice_files/) | Practice input documents and spreadsheets (26 tracked entries). |
| [scripts/](scripts/) | Build, launch, maintenance, and verification commands (9 tracked entries). |
| [tests/](tests/) | Automated checks and test fixtures (4 tracked entries). |
| [web/](web/) | Browser application source (5 tracked entries). |

## Scope and current limits

Examples and practice records are demonstration material. Google Sheets and OpenF1 reads require their own network access and provider terms. Optional Poppler and Tesseract are installed separately.

## License

Original project code retains **MIT** terms in [LICENSE](LICENSE). Third-party libraries, media, data, models, and tools retain their own terms. See the [license review](docs/LICENSE_REVIEW.md) and [dependency inventory](docs/DEPENDENCIES.csv).
