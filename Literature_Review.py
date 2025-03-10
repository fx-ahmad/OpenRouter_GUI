import os
import glob
import json
import argparse
from Open_router_basics import client
from openrouter_utils import extract_pdf_text, collect_full_response

def load_draft_text(draft_path):
    """
    Reads the main paper draft.
    
    If the file is in PDF format, extracts and compresses its text.
    Otherwise, reads it as a plain text file.
    """
    if draft_path.lower().endswith(".pdf"):
        try:
            # Use the PDF extraction functionality.
            return extract_pdf_text(draft_path)
        except Exception as e:
            print(f"Error reading draft PDF '{draft_path}': {e}")
            return ""
    else:
        with open(draft_path, "r", encoding="utf-8") as f:
            return f.read()

def stage_note_taking(draft_path, pdf_folder, output_json):
    """
    Stage 1: Note Taking.
    
    Reads the main paper draft and iterates over all PDFs in the provided folder.
    For each PDF, extracts and compresses its text, and sends a prompt to the OpenRouter API 
    to generate a condensed technical summary. The summary emphasizes those parts most relevant
    to the paper draft while noting influential cited literature.
    
    The resulting summaries are stored as a JSON mapping (pdf filename → summary).
    """
    # Load the main paper draft (handles both PDF and text formats).
    paper_draft_text = load_draft_text(draft_path)

    # Find all PDF files in the specified folder.
    pdf_files = glob.glob(os.path.join(pdf_folder, "*.pdf"))
    if not pdf_files:
        print(f"No PDF files found in folder: {pdf_folder}")
        return

    results = {}

    # Process each PDF file sequentially.
    for pdf_file in pdf_files:
        try:
            # Use the legacy extraction method from the utility.
            text = extract_pdf_text(pdf_file)
        except Exception as e:
            print(f"Error processing {pdf_file}: {e}")
            continue

        # Build the prompt: combine the main paper draft with the literature PDF content.
        prompt = (
            f"Given the following main paper draft and a literature PDF content, "
            f"generate a condensed technical summary of the literature. Parts that are most relevant "
            f"to the paper draft should be reproduced in greatest detail, while other parts should be summarized "
            f"at a higher level. Additionally, list any cited literature that appears highly relevant.\n\n"
            f"Main Paper Draft:\n{paper_draft_text}\n\n"
            f"Literature PDF content from file '{os.path.basename(pdf_file)}':\n{text}"
        )
        
        messages = [
            {"role": "system", "content": "You are an expert academic research assistant."},
            {"role": "user", "content": prompt}
        ]
        
        try:
            # Call the OpenRouter API using streaming mode and aggregate the response.
            response_stream = client.chat.completions.create(
                model="google/gemini-2.0-flash-001",
                messages=messages,
                stream=True,
            )
            summary = collect_full_response(response_stream)
        except Exception as e:
            print(f"Error during API call for {pdf_file}: {e}")
            summary = f"Error: {e}"

        results[os.path.basename(pdf_file)] = summary
        print(f"Processed {os.path.basename(pdf_file)}")

    # Save the gathered summaries to a JSON file.
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"Stage 1 summary results saved to {output_json}")


def stage_triangulation(draft_path, summaries_json, output_file):
    """
    Stage 2: Triangulation.
    
    Reads the main paper draft and the previously generated literature summaries (JSON file).
    The prompt instructs the model to perform analytical work:
      - Critically appraise the connection between each paper and the draft.
      - Cluster together relevant aspects of the literature.
      - Identify key themes and make cross-connections.
    
    The result is a set of analytical notes (triangulation) that capture this assessment.
    These notes are saved to the specified output file.
    """
    paper_draft_text = load_draft_text(draft_path)

    with open(summaries_json, "r", encoding="utf-8") as f:
        summaries = json.load(f)

    # Combine individual summaries into a single text block.
    summaries_text = "\n".join([f"From {filename}:\n{summary}" for filename, summary in summaries.items()])

    # Build the prompt for analytical triangulation.
    prompt = (
        f"Given the following main paper draft and the literature summaries, perform an in-depth analytical appraisal. "
        f"Critically assess how each literature piece connects to the paper draft, cluster together related aspects of the literature, "
        f"and highlight key themes and cross-connections. Do not produce a final polished review; instead, produce a set of analytical notes in high detail "
        f"that capture these insights, including any critical citations. Include doubts and open questions you have as well as disagreements you have with the literature.\n\n"
        f"Main Paper Draft:\n{paper_draft_text}\n\n"
        f"Literature Summaries:\n{summaries_text}"
    )

    messages = [
        {"role": "system", "content": "You are an expert academic research assistant skilled in critical analysis."},
        {"role": "user", "content": prompt}
    ]

    try:
        response_stream = client.chat.completions.create(
            model="openai/o3-mini-high",
            messages=messages,
            stream=True,
        )
        triangulation_notes = collect_full_response(response_stream)
    except Exception as e:
        print(f"Error during API call for triangulation: {e}")
        triangulation_notes = f"Error: {e}"

    # Write the analytical notes (triangulation) to the output file.
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(triangulation_notes)
    print(f"Stage 2 triangulation notes saved to {output_file}")


def stage_writing(draft_path, summaries_json, triangulation_file, output_file):
    """
    Stage 3: Writing.
    
    Reads the main paper draft, the base literature summaries, and the analytical triangulation notes.
    The prompt instructs the model to compose a final polished literature review.
    In this stage, structure, citations, academic tone, and clear flow are emphasized. 
    The output is a cohesive narrative that integrates the original summaries and the analytical insights.
    
    The final literature review is saved to the specified output file.
    """
    paper_draft_text = load_draft_text(draft_path)

    with open(summaries_json, "r", encoding="utf-8") as f:
        summaries = json.load(f)
    summaries_text = "\n".join([f"From {filename}:\n{summary}" for filename, summary in summaries.items()])

    with open(triangulation_file, "r", encoding="utf-8") as f:
        triangulation_notes = f.read()

    # Build the prompt for final literature review writing.
    prompt = (
        f"Given the following main paper draft, the base literature summaries, and the analytical triangulation notes, "
        f"compose a final polished literature review from the perspective of the main paper draft author. The review should integrate all this material into a cohesive narrative "
        f"with a clear academic tone, proper citations, structured narrative and logical flow with critical analysis. Ensure all key themes and connections are clearly articulated."
        f"Use the triangulation notes to base your analysis on. And draw on the literature summaries to provide evidence for your points." 
        f"The length of the review should be at least 1500 words and you should include a list of references at the end." 
        f"Ideally there should be a maximum of 3 subsections(aside from the introduction and conclusion) which broadly cover the key themes and connections you have identified in the literature. "
        f"There should a clear motivation for the review through the introduction and a clear conclusion that ties everything together. "
        f" \n\n"
        f"Main Paper Draft:\n{paper_draft_text}\n\n"
        f"Literature Summaries:\n{summaries_text}\n\n"
        f"Analytical Triangulation Notes:\n{triangulation_notes}"
    )

    messages = [
        {"role": "system", "content": "You are an expert academic research assistant with strong academic writing skills."},
        {"role": "user", "content": prompt}
    ]

    try:
        response_stream = client.chat.completions.create(
            model="openai/o3-mini-high",
            messages=messages,
            stream=True,
        )
        final_review = collect_full_response(response_stream)
    except Exception as e:
        print(f"Error during API call for writing: {e}")
        final_review = f"Error: {e}"

    # Write the final polished literature review to the output file.
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(final_review)
    print(f"Stage 3 literature review saved to {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description="Literature Review Assistant using OpenRouter API"
    )
    subparsers = parser.add_subparsers(dest="stage", help="Stage of literature review process")

    # Subparser for Stage 1 (Note Taking)
    parser_note = subparsers.add_parser("note", help="Stage 1: Note Taking for PDFs")
    parser_note.add_argument("--draft", required=True, help="Path to main paper draft (PDF or text file)")
    parser_note.add_argument("--pdf_folder", required=True, help="Path to folder containing literature PDFs")
    parser_note.add_argument("--output", default="summaries.json", help="Output JSON file for summaries")

    # Subparser for Stage 2 (Triangulation)
    parser_tri = subparsers.add_parser("triangulate", help="Stage 2: Triangulation to produce analytical notes")
    parser_tri.add_argument("--draft", required=True, help="Path to main paper draft (PDF or text file)")
    parser_tri.add_argument("--summaries", required=True, help="JSON file containing summaries from Stage 1")
    parser_tri.add_argument("--output", default="triangulation_notes.txt", help="Output file for triangulation notes")

    # Subparser for Stage 3 (Writing)
    parser_write = subparsers.add_parser("write", help="Stage 3: Writing final literature review")
    parser_write.add_argument("--draft", required=True, help="Path to main paper draft (PDF or text file)")
    parser_write.add_argument("--summaries", required=True, help="JSON file containing summaries from Stage 1")
    parser_write.add_argument("--triangulation", required=True, help="File containing triangulation notes from Stage 2")
    parser_write.add_argument("--output", default="literature_review.txt", help="Output file for the final literature review")

    args = parser.parse_args()

    if args.stage == "note":
        stage_note_taking(args.draft, args.pdf_folder, args.output)
    elif args.stage == "triangulate":
        stage_triangulation(args.draft, args.summaries, args.output)
    elif args.stage == "write":
        stage_writing(args.draft, args.summaries, args.triangulation, args.output)
    else:
        parser.print_help()


if __name__ == "__main__":
    main() 
