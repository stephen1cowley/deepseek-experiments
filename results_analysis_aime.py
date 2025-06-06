"""
This script analyzes the results of the experiments and saves the summary to a json file.
The results should be in json lists in `responses/` of ExperimentResults schema.
"""

from typing import List, Dict, Tuple
import re
import os
import json

files: List[str] = []

for file in os.listdir("responses"):
    if file.endswith(".json") and file.startswith("results_q"):
        files.append(file)


# question -> (doubt_injection_prob -> temperature -> (correct, total))
results_per_question: Dict[str, Dict[str, Dict[str, Tuple[int, int]]]] = {}

# question -> (doubt_injection_prob -> temperature -> (#exceeding 10k tokens, total))
exceeding_10k_tokens: Dict[str, Dict[str, Dict[str, Tuple[int, int]]]] = {}

# question -> (doubt_injection_prob -> temperature -> (#no answer, total))
no_answer: Dict[str, Dict[str, Dict[str, Tuple[int, int]]]] = {}


for file in files:
    if int(re.sub('[a-zA-Z]', '', file.split("_")[-1].split(".")[0])) < 1740940200:
        # Not interested if it was one of the old results (before 6:30pm 2nd March)
        continue
    print(file)
    with open(os.path.join(f"responses/{file}"), "r") as f:
        results: List[dict] = json.load(f)

        for result in results:
            # Handle case where doubt_injection_prob key doesn't exist  
            if "doubt_injection_prob" not in result:
                continue
            # Handle case where temperature key doesn't exist
            if "temperature" not in result:
                continue  # Skip this result if temperature is missing
            temperature = str(result["temperature"])
            doubt_injection_prob = str(result["doubt_injection_prob"])
            question_id = str(result["question_id"])

            # Initialize nested dictionaries for results_per_question
            if question_id not in results_per_question:
                results_per_question[question_id] = {}
            if doubt_injection_prob not in results_per_question[question_id]:
                results_per_question[question_id][doubt_injection_prob] = {}
            if temperature not in results_per_question[question_id][doubt_injection_prob]:
                results_per_question[question_id][doubt_injection_prob][temperature] = (0, 0)
            
            # Initialize nested dictionaries for exceeding_10k_tokens
            if question_id not in exceeding_10k_tokens:
                exceeding_10k_tokens[question_id] = {}
            if doubt_injection_prob not in exceeding_10k_tokens[question_id]:
                exceeding_10k_tokens[question_id][doubt_injection_prob] = {}
            if temperature not in exceeding_10k_tokens[question_id][doubt_injection_prob]:
                exceeding_10k_tokens[question_id][doubt_injection_prob][temperature] = (0, 0)

            # Initialize nested dictionaries for no_answer
            if question_id not in no_answer:
                no_answer[question_id] = {}
            if doubt_injection_prob not in no_answer[question_id]:
                no_answer[question_id][doubt_injection_prob] = {}
            if temperature not in no_answer[question_id][doubt_injection_prob]:
                no_answer[question_id][doubt_injection_prob][temperature] = (0, 0)

            # HARD CODED:
            # cap T=0.75,1.0 at 120
            # cap T=0.6, 0.9, 1.1 at 100
            # cap T=0.0, 0.25, 0.5, 1.25, 1.5 at 20
            if temperature in ["0.75", "1.0"] and results_per_question[question_id][doubt_injection_prob][temperature][1] >= 120:
                continue
            if temperature in ["0.6", "0.9", "1.1"] and results_per_question[question_id][doubt_injection_prob][temperature][1] >= 100:
                continue
            if temperature in ["0.0", "0.25", "0.5", "1.25", "1.5"] and results_per_question[question_id][doubt_injection_prob][temperature][1] >= 20:
                continue
            # Update counts
            if result["llm_answer"] == result["correct_answer"]:
                results_per_question[question_id][doubt_injection_prob][temperature] = (
                    results_per_question[question_id][doubt_injection_prob][temperature][0] + 1,
                    results_per_question[question_id][doubt_injection_prob][temperature][1] + 1
                )
            else:
                results_per_question[question_id][doubt_injection_prob][temperature] = (
                    results_per_question[question_id][doubt_injection_prob][temperature][0],
                    results_per_question[question_id][doubt_injection_prob][temperature][1] + 1
                )
            if result["response_length"] == 10000:
                exceeding_10k_tokens[question_id][doubt_injection_prob][temperature] = (
                    exceeding_10k_tokens[question_id][doubt_injection_prob][temperature][0] + 1,
                    exceeding_10k_tokens[question_id][doubt_injection_prob][temperature][1] + 1
                )
            else:
                exceeding_10k_tokens[question_id][doubt_injection_prob][temperature] = (
                    exceeding_10k_tokens[question_id][doubt_injection_prob][temperature][0],
                    exceeding_10k_tokens[question_id][doubt_injection_prob][temperature][1] + 1
                )

            if result["llm_answer"] == "X":
                no_answer[question_id][doubt_injection_prob][temperature] = (
                    no_answer[question_id][doubt_injection_prob][temperature][0] + 1,
                    no_answer[question_id][doubt_injection_prob][temperature][1] + 1
                )
            else:
                no_answer[question_id][doubt_injection_prob][temperature] = (
                    no_answer[question_id][doubt_injection_prob][temperature][0],
                    no_answer[question_id][doubt_injection_prob][temperature][1] + 1
                )

# Save results_summary to json
print(results_per_question)
with open("results_per_question.json", "w") as f:
    json.dump(results_per_question, f, indent=4)
