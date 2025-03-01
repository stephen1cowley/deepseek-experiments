"""
This script graphs the results summary `results_summary.json`
First run `results_analysis.py` to generate the summary from all the lists of ExperimentResults.
"""

from typing import Dict, Tuple
from matplotlib import pyplot as plt
import json


plt.figure(figsize=(12, 8))

with open("results_summary.json", "r") as f:
    results_summary: Dict[str, Dict[str, Tuple[int, int]]] = json.load(f)

    # Sort doubt injection probabilities first
    sorted_probs = sorted(results_summary.keys(), key=float)

    for doubt_injection_prob in sorted_probs:
        temperatures = []
        accuracy = []
        for temperature in results_summary[doubt_injection_prob]:
            corr, tot = results_summary[doubt_injection_prob][temperature]
            temperatures.append(float(temperature))
            accuracy.append(corr / tot)

        # sort temperatures and accuracy
        temperatures, accuracy = zip(*sorted(zip(temperatures, accuracy)))

        plt.plot(temperatures, accuracy,
                 label=f"{float(doubt_injection_prob):.1f}",  # Simplified legend
                 color=plt.cm.jet(float(doubt_injection_prob)))  # pyright: ignore

plt.xlabel("Temperature")
plt.ylabel("Accuracy")
plt.title("Accuracy of LLM with Different Temperatures")
plt.legend()
plt.savefig("results_graph.png")
