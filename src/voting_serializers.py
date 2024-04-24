import json
from typing import List

from src.model import Motion, Plenary


class PlenaryReportToMarkdownSerializer:
    def serialize(self, plenary: Plenary, output_file_path: str) -> None:
        plenary_markdown = f"# Plenary gathering {plenary.id}\n\n"
        plenary_markdown += f"Source (HTML report): {plenary.pdf_report_url}\n\n"
        plenary_markdown += f"PDF-formatted alternative: {plenary.html_report_url}\n\n"
        
        for motion in plenary.motions:
            plenary_markdown += self.__serialize(motion)
        
        with open(output_file_path, "w", encoding="utf-8") as output_file:
            output_file.write(plenary_markdown)
    
    def __serialize(self, motion: Motion) -> None:
        motion_markdown = f"## Motion {motion.proposal.number}\n\n"
        motion_markdown += motion.proposal.description
        motion_markdown += "\n\n"

        motion_markdown += f"### Yes votes ({motion.num_votes_yes})\n"
        motion_markdown += "\n"
        motion_markdown += ", ".join(motion.vote_names_yes)
        motion_markdown += "\n\n"

        motion_markdown += f"### No votes ({motion.num_votes_no})\n"
        motion_markdown += "\n"
        motion_markdown += ", ".join(motion.vote_names_no)
        motion_markdown += "\n\n"

        motion_markdown += f"### Abstentions ({motion.num_votes_abstention})\n"
        motion_markdown += "\n"
        motion_markdown += ", ".join(motion.vote_names_abstention)
        motion_markdown += "\n\n\n"

        return motion_markdown


class PlenaryReportToJsonSerializer:
    def serialize(self, plenary: Plenary, output_file_path: str) -> None:
        plenary_json = json.dumps(
            plenary, 
            default=lambda o: o.__dict__, 
            indent=4)
        with open(output_file_path, "w", encoding="utf-8") as output_file:
            output_file.write(plenary_json)
