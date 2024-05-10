import logging
import os
import unittest
from datetime import date

import transparentdemocracy
from transparentdemocracy.config import CONFIG
from transparentdemocracy.model import ReportItem, Motion, Vote, VoteType
from transparentdemocracy.plenaries.extraction import extract_from_html_plenary_reports, \
	extract_from_html_plenary_report, _read_plenary_html, _get_plenary_date, _extract_motion_report_items, \
	_extract_motions, _extract_votes
from transparentdemocracy.politicians.extraction import Politicians, load_politicians

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
logger.setLevel(logging.INFO)


class ReportItemExtractionTest(unittest.TestCase):

	@classmethod
	def setUpClass(cls):
		CONFIG.data_dir = os.path.join(os.path.dirname(transparentdemocracy.__file__), "..", "testdata")

	def test_extract_ip298_happy_case(self):
		report_items = self.extract_motion_report_items('ip298x.html')

		self.assertEqual(len(report_items), 14)  # motions 10 - 23 (?)

		self.assert_report_item(report_items[0],
								"10",
								"10 Moties ingediend",
								"10 Motions déposées en conclusion des interpellations de")

		self.assert_report_item(report_items[1],
								"11",
								"11 Wetsontwerp\nhoudende diverse wijzigingen van het Wetboek van strafvordering II, zoals\ngeamendeerd tijdens de plenaire vergadering van 28 maart 2024 (3515/10)",
								"11 Projet de loi portant diverses modifications du Code d'instruction\ncriminelle II, tel qu'amendé lors de la séance plénière du 28 mars 2024\n(3515/10)")

	def test_extract_ip280_has_1_naamstemming_but_no_identifiable_motion_title(self):
		report_items = self.extract_motion_report_items('ip280x.html')

		self.assertEqual(len(report_items), 0)

	def test_extract_ip271(self):
		report_items = self.extract_motion_report_items('ip271x.html')

		self.assertEqual(len(report_items), 14)  # todo: check manually

		self.assert_report_item(report_items[0],
								'14',
								'14 Moties ingediend tot besluit van de\ninterpellatie van mevrouw Barbara Pas',
								'14 Motions déposées en conclusion de l\'interpellation de Mme Barbara\nPas')

		# FIXME: Do we count 'Goedkeuring van de agenda' as a motion?
		# If we link the motions with their votes we could exclude motions without votes
		self.assert_report_item(report_items[-1],
								'27',
								'27 Wetsontwerp tot\nwijziging',
								'27 Projet de loi visant à modi')

	def test_extract_ip290_has_no_naamstemmingen(self):
		report_items = self.extract_motion_report_items('ip290x.html')

		self.assertEqual(report_items, [])

	def assert_report_item(self, report_item: ReportItem, label: str, nl_title_prefix: str, fr_title_prefix: str):
		self.assertEqual(label, report_item.label)
		self.assertEqual(report_item.nl_title[:len(nl_title_prefix)], nl_title_prefix)
		self.assertEqual(report_item.fr_title[:len(fr_title_prefix)], fr_title_prefix)

	def extract_motion_report_items(self, report_path):
		path = CONFIG.plenary_html_input_path(report_path)
		return _extract_motion_report_items(path, _read_plenary_html(path))

class MotionExtractionTest(unittest.TestCase):
	@classmethod
	def setUpClass(cls):
		CONFIG.data_dir = os.path.join(os.path.dirname(transparentdemocracy.__file__), "..", "testdata")

	def test_extract_motions(self):
		report_path = CONFIG.plenary_html_input_path("ip298x.html")
		motion_report_items, motions = _extract_motions("55_298", report_path, _read_plenary_html(report_path))

		self.assertEqual(28, len(motions))
		self.assertEqual(Motion("55_298_1","1","55_298_10",False), motions[0])


class VoteExtractionTest(unittest.TestCase):
	@classmethod
	def setUpClass(cls):
		CONFIG.data_dir = os.path.join(os.path.dirname(transparentdemocracy.__file__), "..", "testdata")

	def test_extract_votes_ip298x(self):
		report_path = CONFIG.plenary_html_input_path("ip298x.html")
		politicians = load_politicians()
		votes = _extract_votes("55_298", _read_plenary_html(report_path), politicians)

		# I Honestly didn't count this. This is just to make sure we notice if parsing changes
		self.assertEqual(3732, len(votes))
		self.assertEqual(133, len([v for v in votes if v.motion_id == "55_298_1"]))
		self.assertEqual(134, len([v for v in votes if v.motion_id == "55_298_2"]))
		self.assertEqual(132, len([v for v in votes if v.motion_id == "55_298_3"]))

		expected_vote = Vote(politicians[7124], motion_id="55_298_1", vote_type="YES")
		self.assertEqual(expected_vote, votes[0])


class PlenaryExtractionTest(unittest.TestCase):

	@classmethod
	def setUpClass(cls):
		CONFIG.data_dir = os.path.join(os.path.dirname(transparentdemocracy.__file__), "..", "testdata")

	@unittest.skipIf(os.environ.get("SKIP_SLOW", None) is not None, "skipping slow tests")
	def test_extract_from_all_plenary_reports_does_not_throw(self):
		CONFIG.data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
		plenaries, all_votes = extract_from_html_plenary_reports(CONFIG.plenary_html_input_path("*.html"))

		self.assertEqual(len(plenaries), 300)

		all_motions = [motion for plenary in plenaries for motion in plenary.motions]
		self.assertEqual(len(all_motions), 2842)

		motions_with_problems = list(filter(lambda m: len(m.parse_problems) > 0, all_motions))

		# TODO: Improve how we handle parsing problems
		self.assertEqual(len(motions_with_problems), 17)

	def test_extract_from_html_plenary_report__ip298x_html__go_to_example_report(self):
		# Plenary report 298 has long been our first go-to example plenary report to test our extraction against.
		# Arrange
		report_file_name = CONFIG.plenary_html_input_path("ip298x.html")

		# Act
		plenary, votes = extract_from_html_plenary_report(report_file_name)

		# Assert
		# The plenary info is extracted correctly:
		self.assertEqual(plenary.id, "55_298")
		self.assertEqual(plenary.number, 298)
		self.assertEqual(plenary.date, date(2024, 4, 4))
		self.assertEqual(plenary.legislature, 55)
		self.assertEqual(plenary.pdf_report_url, "https://www.dekamer.be/doc/PCRI/pdf/55/ip298.pdf")
		self.assertEqual(plenary.html_report_url, "https://www.dekamer.be/doc/PCRI/html/55/ip298x.html")

		# The proposals are extracted correctly:
		self.assertEqual(len(plenary.proposal_discussions), 6)
		self.assertEqual(plenary.proposal_discussions[0].id, "55_298_d01")
		self.assertEqual(plenary.proposal_discussions[0].plenary_id, "55_298")
		self.assertEqual(plenary.proposal_discussions[0].plenary_agenda_item_number, 1)
		self.assertTrue(
			plenary.proposal_discussions[0].description_nl.startswith("Wij vatten de bespreking van de artikelen aan."))
		self.assertTrue(plenary.proposal_discussions[0].description_nl.endswith(
			"De bespreking van de artikelen is gesloten. De stemming over het geheel zal later plaatsvinden."))
		self.assertTrue(
			plenary.proposal_discussions[0].description_fr.startswith("Nous passons à la discussion des articles."))
		self.assertTrue(plenary.proposal_discussions[0].description_fr.endswith(
			"La discussion des articles est close. Le vote sur l'ensemble aura lieu ultérieurement."))
		self.assertEqual(plenary.proposal_discussions[0].proposals[0].title_nl,
						 "Wetsontwerp houdende optimalisatie van de werking van het Centraal Orgaan voor de Inbeslagneming en de Verbeurdverklaring en het Overlegorgaan voor de coördinatie van de invordering van niet-fiscale schulden in strafzaken en houdende wijziging van de Wapenwet")
		self.assertEqual(plenary.proposal_discussions[0].proposals[0].title_fr,
						 "Projet de loi optimisant le fonctionnement de l'Organe central pour la Saisie et la Confiscation et de l'Organe de concertation pour la coordination du recouvrement des créances non fiscales en matière pénale et modifiant la loi sur les armes")
		self.assertEqual(plenary.proposal_discussions[0].proposals[0].document_reference, "3849/1-4")

		# The motions are extracted correctly:
		self.assertEqual(28, len(plenary.motions))
		self.assertEqual(plenary.motions[0].id,
						 "55_298_1")  # TODO modify id creation so it doesn't clash with proposals and sections
		self.assertEqual(False, plenary.motions[0].cancelled)
		self.assertEqual(True, plenary.motions[11].cancelled)

		# The votes are extracted correctly:
		yes_voters = [vote.politician.full_name for vote in votes if
					  vote.vote_type == "YES" and vote.motion_id == "55_298_1"]
		no_voters = [vote.politician.full_name for vote in votes if
					 vote.vote_type == "NO" and vote.motion_id == "55_298_1"]
		abstention_voters = [vote.politician.full_name for vote in votes if
							 vote.vote_type == "ABSTENTION" and vote.motion_id == "55_298_1"]

		count_yes = len(yes_voters)
		count_no = len(no_voters)
		count_abstention = len(abstention_voters)

		self.assertEqual(79, count_yes)
		self.assertEqual(['Aouasti Khalil', 'Bacquelaine Daniel'], yes_voters[:2])

		self.assertEqual(50, count_no)
		self.assertEqual(["Anseeuw Björn", "Bruyère Robin"], no_voters[:2])

		self.assertEqual(4, count_abstention)
		self.assertEqual(['Arens Josy', 'Daems Greet'], abstention_voters[:2])

	def test_extract_from_html_plenary_report__ip261x_html__different_proposals_header(self):
		# This example proposal has "Projets de loi et propositions" as proposals header, rather than "Projets de loi".
		# Also, the proposal description header ("Bespreking van de artikelen") cannot be found, so we fall back to 
		# taking the entire text after the proposal header in a best-effort as the description, both for Dutch and 
		# French.
		# Arrange
		report_file_name = CONFIG.plenary_html_input_path("ip261x.html")

		# Act
		plenary, votes = extract_from_html_plenary_report(report_file_name)

		# Assert
		# The plenary info is extracted correctly:
		self.assertEqual(plenary.id, "55_261")
		self.assertEqual(plenary.number, 261)
		self.assertEqual(plenary.date, date(2023, 10, 5))
		self.assertEqual(plenary.legislature, 55)
		self.assertEqual(plenary.pdf_report_url, "https://www.dekamer.be/doc/PCRI/pdf/55/ip261.pdf")
		self.assertEqual(plenary.html_report_url, "https://www.dekamer.be/doc/PCRI/html/55/ip261x.html")

		# The proposals are extracted correctly:
		self.assertEqual(len(plenary.proposal_discussions), 4)
		self.assertEqual(plenary.proposal_discussions[0].id, "55_261_d20")
		self.assertEqual(plenary.proposal_discussions[0].plenary_id, "55_261")
		self.assertEqual(plenary.proposal_discussions[0].plenary_agenda_item_number, 20)
		self.assertTrue(plenary.proposal_discussions[0].description_nl.startswith(
			"20.01  Peter De Roover (N-VA): Mevrouw de voorzitster, "))
		self.assertTrue(plenary.proposal_discussions[0].description_nl.endswith(
			"Bijgevolg zal de voorzitster het advies van de Raad van State vragen met toepassing van artikel 98.3 van het Reglement."))
		self.assertTrue(plenary.proposal_discussions[0].description_fr.startswith(
			"20.01  Peter De Roover (N-VA): Mevrouw de voorzitster, "))
		self.assertTrue(plenary.proposal_discussions[0].description_fr.endswith(
			"Bijgevolg zal de voorzitster het advies van de Raad van State vragen met toepassing van artikel 98.3 van het Reglement."))
		self.assertEqual(plenary.proposal_discussions[0].proposals[0].title_nl,
						 "Verzoek om advies van de Raad van State")
		self.assertEqual(plenary.proposal_discussions[0].proposals[0].title_fr, "Demande d'avis du Conseil d'État")
		self.assertEqual(plenary.proposal_discussions[0].proposals[0].document_reference, None)

	@unittest.skip(
		"suppressed for now - we can't make the distinction between 'does not match voters' problem and actually having 0 votes right now")
	def test_extract_ip67(self):
		actual, votes = extract_from_html_plenary_report(CONFIG.plenary_html_input_path('ip067x.html'))

		vote_types_motion_1 = set([v.vote_type for v in votes if v.motion_id == "55_067_1"])
		self.assertTrue("NO" in vote_types_motion_1)

	@unittest.skip(
		"todo - broke since the refactoring of proposal description extraction"
	)
	def test_extract_ip72(self):
		"""vote 2 has an extra '(' in the vote result indicator"""
		actual, votes = extract_from_html_plenary_report(CONFIG.plenary_html_input_path('ip072x.html'))

		self.assertEqual(len(actual.motions), 5)

	def test_voter_dots_are_removed_from_voter_names(self):
		actual, votes = extract_from_html_plenary_report(CONFIG.plenary_html_input_path('ip182x.html'))

		names = [v.politician.full_name for v in votes]

		names_with_dots = [name for name in names if "." in name]
		self.assertEqual([], names_with_dots)

	@unittest.skipIf(os.environ.get("SKIP_SLOW", None) is not None, "skipping slow tests")
	def test_votes_must_have_politician(self):
		CONFIG.data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
		actual, votes = extract_from_html_plenary_reports()

		for vote in votes:
			self.assertIsNotNone(vote.politician)

	def test_plenary_date1(self):
		plenary_date = self.get_plenary_date("ip123x.html")

		self.assertEqual(plenary_date, date.fromisoformat("2021-07-19"))

	def test_plenary_date2(self):
		plenary_date = self.get_plenary_date("ip007x.html")

		self.assertEqual(plenary_date, date.fromisoformat("2019-10-03"))

	def get_plenary_date(self, filename):
		path = CONFIG.plenary_html_input_path(filename)
		return _get_plenary_date(path, _read_plenary_html(path))