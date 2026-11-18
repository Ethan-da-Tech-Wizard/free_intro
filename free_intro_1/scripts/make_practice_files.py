# Program: free_intro - make_practice_files.py
# Programmer: Ethan-da-Tech-Wizard (written with Claude, an AI assistant)
# Last Modified: 2026-11-18
# Purpose: Generates the tutorial practice files (messy XLSX and CSV, intake PDFs, and a scanned HVAC image) for every scenario using the app's own generators.

"""Create the tutorial's actual example files using the running app's generators."""
from pathlib import Path
import shutil
import subprocess
import sys

# Project root: the folder above scripts/.
ROOT=Path(__file__).resolve().parents[1]
# Make the app/ modules importable (they use plain, non-package imports).
sys.path.insert(0,str(ROOT/'app'))
from config import DEFINITIONS
from data_tools import messy_matrix,xlsx_bytes,pdf_bytes
from server import csv_bytes

# Output folder for the practice files.
directory=ROOT/'practice_files';directory.mkdir(exist_ok=True)
# For each scenario write an untidy workbook, the same data as CSV, and a labelled intake PDF.
for key,scene in DEFINITIONS.items():
    matrix=messy_matrix(scene)
    (directory/(key+'-ugly.xlsx')).write_bytes(xlsx_bytes(matrix))
    (directory/(key+'-ugly.csv')).write_bytes(csv_bytes(matrix))
    (directory/(key+'-intake.pdf')).write_bytes(pdf_bytes(scene['company']+' / Intake',[f"{f['label']}: {f['default']}" for f in scene['fields']]))
# If Poppler is installed, rasterise the HVAC intake PDF to a PNG so the OCR lesson has a "scanned" document.
if shutil.which('pdftoppm'):
    subprocess.run(['pdftoppm','-singlefile','-r','160','-png',str(directory/'hvac-intake.pdf'),str(directory/'hvac-scanned-intake')],check=True,capture_output=True,timeout=30)
# Write a short note explaining the files.
(directory/'READ_ME.txt').write_text('Relayworks practice files\n\nAll business data is synthetic. Each workflow has a labelled intake PDF and deliberately messy XLSX/CSV. hvac-scanned-intake.png is an actual raster rendering of the supplied PDF for local OCR practice. Upload a source through Sources & connections; keep your original alongside the extracted values. See THE_WORKS.html in the parent folder for the exact exercises.\n')
print('Created',len(list(directory.iterdir())),'practice files in',directory)
