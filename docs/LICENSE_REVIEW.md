# License review — Relayworks

Reviewed 2026-10-12. Original project code retains **MIT** terms in [LICENSE](../LICENSE).

The owner selected MIT for previously unlicensed original code. Existing licenses were preserved. This choice does not relicense copied code, dependencies, datasets, model weights, fonts, logos, or game assets.

## Preserved notices

- [LICENSE](../LICENSE)

## Dependency evidence

[DEPENDENCIES.csv](DEPENDENCIES.csv) lists 8 manifest and lockfile records. Repeated packages can appear under different manifests, versions, or development scopes. Registry metadata is evidence, not a replacement for the actual license text. For unpinned ranges, `metadata_version` is the version inspected and is not a claim about every install. Go and system/build tools can require notices beyond package-manager metadata.

| Component | Declared version | License evidence |
| --- | --- | --- |
| npm: @playwright/test | 1.63.0 | [Apache-2.0](https://registry.npmjs.org/%40playwright%2Ftest/1.63.0) |
| npm: @playwright/test | 1.63.0 | [Apache-2.0](https://registry.npmjs.org/%40playwright%2Ftest/1.63.0) |

## Project-specific considerations

Optional Poppler and Tesseract are external executables with their own licenses, not relicensed by this project. Playwright is a development dependency. Provider access to Google Sheets/OpenF1 is governed separately; demo documents are not a grant over real customer records.

## Remaining work before binary distribution

No unresolved registry-license lookup remains in the listed package records. System packages, downloaded tools/models, optional plugins, release binaries, and externally obtained assets need a build-specific inventory. This source review is not a blanket legal certification or a claim that every release artifact has been audited.
