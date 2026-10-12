"""Regression checks for issues discovered while following the operator book."""
from pathlib import Path
import shutil,subprocess,sys,tempfile,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
from config import DEFINITIONS
from data_tools import normalize_table,messy_matrix,pdf_bytes

class RehearsalFixes(unittest.TestCase):
    def test_legal_and_sports_dirty_emails_are_held_at_source_review(self):
        for name,label,date in [('legal','CLIENT EMAIL','APPOINTMENT'),('sports','DELIVERY ADDRESS','EVENT DATE')]:
            with self.subTest(name=name):
                table=normalize_table(messy_matrix(DEFINITIONS[name]),name,'test')
                good,bad,duplicate=table['rows']
                self.assertFalse(good['issues'])
                self.assertEqual(good['values'][label],good['values'][label].lower())
                self.assertIn(label+': Email needs correction',bad['issues'])
                self.assertIn(date+': Slash date is ambiguous; choose an ISO date',bad['issues'])
                self.assertTrue(duplicate['duplicate'])
        postal=normalize_table([['Item','Delivery address'],['Desk','10 Example Terrace']],'shipping','test',header_index=0)
        self.assertFalse(postal['rows'][0]['issues'])

    @unittest.skipUnless(shutil.which('pdftotext'),'Poppler is not available')
    def test_pdf_preserves_supported_accent_and_middle_dot(self):
        values=['Equipment: Outdoor condenser · Unit A','Session: Repair café','Name: Renée Example']
        with tempfile.TemporaryDirectory() as directory:
            file=Path(directory)/'sample.pdf';file.write_bytes(pdf_bytes('Sample',values))
            text=subprocess.check_output(['pdftotext',str(file),'-']).decode()
            for value in values:self.assertIn(value,text)

if __name__=='__main__':unittest.main()
