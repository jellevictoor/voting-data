import unittest

from transparentdemocracy.documents.references import parse_document_reference
from transparentdemocracy.model import DocumentsReference


class DocumentReferencesTest(unittest.TestCase):
	def test_parse_document_reference_without_subdocs(self):
		actual = parse_document_reference("1234")

		self.assertEqual(DocumentsReference(
			document_reference=1234,
			all_documents_reference="1234",
			main_document_reference=1,
			sub_document_references=[1]
		), actual)

		self.assertEqual(actual.sub_document_pdf_urls, [
			"https://www.dekamer.be/FLWB/PDF/55/1234/55K1234001.pdf"
		])

	def test_parse_document_reference_with_single_subdoc(self):
		actual = parse_document_reference("1234/5")

		self.assertEqual(DocumentsReference(
			document_reference=1234,
			all_documents_reference="1234/5",
			main_document_reference=5,
			sub_document_references=[5]
		), actual)

		self.assertEqual(actual.sub_document_pdf_urls, [
			"https://www.dekamer.be/FLWB/PDF/55/1234/55K1234005.pdf"
		])

	def test_parse_document_reference_with_subdoc_range(self):
		actual = parse_document_reference("1234/2-5")

		self.assertEqual(DocumentsReference(
			document_reference=1234,
			all_documents_reference="1234/2-5",
			main_document_reference=2,
			sub_document_references=[2, 3, 4, 5]
		), actual)

		self.assertEqual(actual.sub_document_pdf_urls, [
			"https://www.dekamer.be/FLWB/PDF/55/1234/55K1234002.pdf",
			"https://www.dekamer.be/FLWB/PDF/55/1234/55K1234003.pdf",
			"https://www.dekamer.be/FLWB/PDF/55/1234/55K1234004.pdf",
			"https://www.dekamer.be/FLWB/PDF/55/1234/55K1234005.pdf",
		])

	def test_parse_bad_doc_reference(self):
		actual = parse_document_reference("1234-2345")

		self.assertEqual(DocumentsReference(None, "1234-2345", None, []), actual)