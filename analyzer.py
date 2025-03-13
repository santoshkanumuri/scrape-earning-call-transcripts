import os
import json
import logging
import csv
from typing import Set
from pydantic import BaseModel, conint
from pydantic_ai import Agent
from pydantic_ai.models.gemini import GeminiModel
from gemini_model_rotator import ModelManager

# Configure logging for robust exception tracking
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Define a Pydantic model for each variable's analysis, now with a "present" flag.
class VariableAnalysis(BaseModel):
    score: conint(ge=0, le=10)
    reason_description: str
    present: bool

# Define the overall transcript analysis model that includes all three variables.
class TranscriptAnalysis(BaseModel):
    innovativeness: VariableAnalysis
    proactiveness: VariableAnalysis
    risk_taking: VariableAnalysis

# Detailed system prompt including definitions, characteristics, and examples.
SYSTEM_PROMPT = """
You are an AI assistant that analyzes transcript texts and earnings call transcripts to evaluate three strategic variables: innovativeness, proactiveness, and risk-taking.

For each variable, you must output:
- A score between 0 and 10.
- A reason_description explaining the score.
- A boolean value (true or false) under the key "present" that indicates whether the transcript exhibits that characteristic.

Definitions and Characteristics:

1. Innovativeness
   - Definition: Reflects “the predisposition to engage in creativity and experimentation through the introduction of new products/services as well as technological leadership via R&D in new processes.”
   - Characteristics:
       · Curiosity: An inherent desire to learn, explore, and question the status quo.
       · Creativity: The ability to think outside the box and generate unique ideas.
       · Vision: The capacity to envision future possibilities and trends.
       · Resourcefulness: Making the most of available resources and overcoming challenges.
       · Passion for Improvement: A deep drive to make things better.
       · Embracing Failure as Learning: Viewing failures as opportunities for growth.
   - Examples: Tesla reshaping automotive innovation; Amazon leveraging AI and data analytics.

2. Proactiveness
   - Definition: Involves “an opportunity-seeking, forward-looking perspective characterized by the introduction of new products and services ahead of the competition and acting in anticipation of future demand.”
   - Characteristics:
       · Initiative: Taking action and looking for opportunities.
       · Forward-thinking: Anticipating future trends and potential issues.
       · Adaptability: Adjusting strategies as circumstances change.
       · Long-term Thinking: Focusing on sustained, long-term outcomes.
   - Examples: Google’s continuous R&D investments; Starbucks adapting to local tastes.

3. Risk-taking
   - Definition: Is “taking bold actions by venturing into the unknown, borrowing heavily, and/or committing significant resources to ventures in uncertain environments.”
   - Characteristics:
       · Courage: Bravery in the face of uncertainty.
       · Optimism: Belief in favorable outcomes despite risks.
       · Tolerance for Uncertainty: Comfort with ambiguity.
       · Adventurousness: Willingness to step outside the comfort zone.
       · Calculated Risk: Weighing risks against potential rewards.
       · Willingness to Face Loss: Preparedness to lose something of value for potential gain.
   - Examples: Tesla’s commitment to EV technology; SpaceX’s reusable rockets; Netflix’s strategic pivots.

Instructions:
Given the transcript, evaluate each of these variables on a scale from 0 to 10, provide a detailed reason_description for each score, and also indicate with a boolean (true/false) whether the transcript demonstrates the respective characteristic.

Return your response as a JSON object following this schema:

{
  "innovativeness": {"score": int (0-10), "reason_description": "string", "present": bool},
  "proactiveness": {"score": int (0-10), "reason_description": "string", "present": bool},
  "risk_taking": {"score": int (0-10), "reason_description": "string", "present": bool}
}
"""

# GeminiClient uses the Pydantic AI Agent with the Gemini model.
class GeminiClient:
    def __init__(self):
        try:
            # Note: Replace the API key with your actual key as needed.
            self.model_manager = ModelManager('models.json')
            self.new_model = self.model_manager.get_available_model()
            self.model = GeminiModel(self.new_model.name, provider='google-gla', api_key='AIzaSyDbz6bYt35ig_HeMw06oHQecTOQY7kgh74')
            self.agent = Agent(self.model, result_type=TranscriptAnalysis)
        except Exception as e:
            logging.error("Error initializing GeminiClient: %s", e)
            raise

    def generate_response(self, prompt: str) -> str:
        try:
            response = self.agent.run_sync(prompt)
            self.new_model.increment_usage()
            return response
        except Exception as e:
            logging.error("Error generating response from agent: %s", e)
            self.new_model = self.model_manager.swap_model(self.new_model)
            logging.info("Swapped to model: %s", self.new_model.name)
            self.model = GeminiModel(self.new_model.name, provider='google-gla', api_key='AIzaSyDbz6bYt35ig_HeMw06oHQecTOQY7kgh74')
            self.agent = Agent(self.model, result_type=TranscriptAnalysis)
            raise

def load_processed_files(json_file: str) -> Set[str]:
    try:
        if os.path.exists(json_file):
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return set(data)
    except Exception as e:
        logging.error("Error loading processed files from %s: %s", json_file, e)
    return set()

def save_processed_files(json_file: str, processed_files: Set[str]) -> None:
    try:
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(list(processed_files), f)
    except Exception as e:
        logging.error("Error saving processed files to %s: %s", json_file, e)
        raise

def save_csv_row(csv_file: str, row: dict) -> None:
    # Check if CSV file already exists to write header if necessary
    file_exists = os.path.exists(csv_file)
    try:
        with open(csv_file, 'a', newline='', encoding='utf-8') as f:
            fieldnames = [
                "folder", "file",
                "innov_score", "innov_reason", "innov_present",
                "proact_score", "proact_reason", "proact_present",
                "risk_score", "risk_reason", "risk_present"
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            if not file_exists:
                writer.writeheader()
            writer.writerow(row)
            f.flush()
    except Exception as e:
        logging.error("Error writing row to CSV file %s: %s", csv_file, e)
        raise

# Process transcript files within a folder and save results to CSV periodically.
def process_transcripts(folder: str, num_files: int, json_file: str = 'processed.json', csv_file: str = 'analysis_output.csv') -> None:
    folder = os.path.abspath(folder)
    processed_files = load_processed_files(json_file)

    try:
        gemini_client = GeminiClient()
    except Exception as e:
        logging.error("Failed to initialize Gemini client: %s", e)
        return

    processed_count = 0

    for root, dirs, files in os.walk(folder):
        folder_name = os.path.basename(root)
        for file in files:
            if file.endswith('.md'):
                file_path = os.path.join(root, file)
                if file_path in processed_files:
                    logging.info("Skipping already processed file: %s", file_path)
                    continue

                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        transcript = f.read()
                except Exception as e:
                    logging.error("Error reading file %s: %s", file_path, e)
                    continue

                prompt = f"{SYSTEM_PROMPT}\n\nTranscript:\n{transcript}"
                try:
                    response = gemini_client.generate_response(prompt)
                except Exception as e:
                    logging.error("Error generating response for file %s: %s", file_path, e)
                    continue

                analysis = response.data

                logging.info("Successfully processed file: %s", file_path)
                # Prepare CSV row data
                csv_row = {
                    "folder": folder_name,
                    "file": file,
                    "innov_score": analysis.innovativeness.score,
                    "innov_reason": analysis.innovativeness.reason_description,
                    "innov_present": analysis.innovativeness.present,
                    "proact_score": analysis.proactiveness.score,
                    "proact_reason": analysis.proactiveness.reason_description,
                    "proact_present": analysis.proactiveness.present,
                    "risk_score": analysis.risk_taking.score,
                    "risk_reason": analysis.risk_taking.reason_description,
                    "risk_present": analysis.risk_taking.present
                }
                try:
                    save_csv_row(csv_file, csv_row)
                except Exception as e:
                    logging.error("Error saving CSV row for file %s: %s", file_path, e)
                    continue

                processed_files.add(file_path)
                try:
                    save_processed_files(json_file, processed_files)
                except Exception as e:
                    logging.error("Error updating processed files after processing %s: %s", file_path, e)
                    continue

                processed_count += 1
                if processed_count >= num_files:
                    return

    if processed_count < num_files:
        logging.info("Note: Only %d new file(s) were available to process.", processed_count)

def main():
    # Define folder and number of files to process.
    json_file = 'processed.json'
    csv_file = 'analysis_output.csv'
    files = './transcripts'
    num_files = 20

    process_transcripts(files, num_files, json_file, csv_file)

if __name__ == '__main__':
    main()
