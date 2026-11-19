# ==============================================================================
# Program: make_practice_files.py
# Programmer: Ethan-da-Tech-Wizard
# Last Modified: November 18, 2026
# Purpose: Educational automation and workflow orchestration module for free_intro.
#          Provides structured data generation, asset planning, and contracts.
# ==============================================================================
"""Create the tutorial's actual example files using the running app's generators."""
from pathlib import Path
import shutil
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'app'))
from config import DEFINITIONS
from data_tools import messy_matrix,xlsx_bytes,pdf_bytes
from server import csv_bytes

# Output folder for the generated tutorial files.
directory=ROOT/'practice_files';directory.mkdir(exist_ok=True)
# For every scenario write a deliberately messy XLSX, the same data as CSV, and a labelled intake PDF,
# reusing the app's own generators so the files match what the demo expects.
for key,scene in DEFINITIONS.items():
    matrix=messy_matrix(scene)
    (directory/(key+'-ugly.xlsx')).write_bytes(xlsx_bytes(matrix))
    (directory/(key+'-ugly.csv')).write_bytes(csv_bytes(matrix))
    (directory/(key+'-intake.pdf')).write_bytes(pdf_bytes(scene['company']+' / Intake',[f"{f['label']}: {f['default']}" for f in scene['fields']]))
# Optional: rasterise the HVAC PDF into a PNG for OCR practice. Skipped when Poppler is not installed.
if shutil.which('pdftoppm'):
    subprocess.run(['pdftoppm','-singlefile','-r','160','-png',str(directory/'hvac-intake.pdf'),str(directory/'hvac-scanned-intake')],check=True,capture_output=True,timeout=30)
# Plain-text note describing the files for the learner.
(directory/'READ_ME.txt').write_text('Relayworks practice files\n\nAll business data is synthetic. Each workflow has a labelled intake PDF and deliberately messy XLSX/CSV. hvac-scanned-intake.png is an actual raster rendering of the supplied PDF for local OCR practice. Upload a source through Sources & connections; keep your original alongside the extracted values. See THE_WORKS.html in the parent folder for the exact exercises.\n')
print('Created',len(list(directory.iterdir())),'practice files in',directory)
