from typing import List
import json
import time
from transformers import AutoTokenizer, AutoModelForCausalLM, DynamicCache
import torch


llm_name = "deepseek-ai/DeepSeek-R1-Distill-Qwen-32B"
temperature = 1.2
max_length = 20000
num_responses = 1
# llm_name = "Qwen/Qwen2.5-1.5B"

tokenizer = AutoTokenizer.from_pretrained(llm_name)
model = AutoModelForCausalLM.from_pretrained(llm_name, torch_dtype=torch.bfloat16)
model = model.to("cuda" if torch.cuda.is_available() else "cpu")  # Move model to GPU if available

# Check model's dtype
print(f"Model dtype: {model.dtype}")
print(f"First layer dtype: {next(model.parameters()).dtype}")

# question = """
# A farmer with a wolf, a goat, and a cabbage must cross a river by boat.
# The boat can carry only the farmer and a single item.
# If left unattended together, the wolf would eat the goat, or the goat would eat the cabbage.
# How can they cross the river without anything being eaten?
# """

# question = """
# A farmer and a goat are on the left side of a river and must cross by boat.
# On the right side of the river, there is a wolf and a cabbage.
# The boat can carry only the farmer and a single item.
# If left unattended together, the wolf would eat the goat, or the goat would eat the cabbage.
# How can the farmer get the goat to the right side of the river without anything being eaten?
# """

# question = """
# The following is a classic puzzle:
# A man and a goat are on one side of a river.
# There is a wolf and a cabbage on the other side.
# The man has a boat.
# The boat can carry only the farmer and a single item.
# If left unattended together, the wolf would eat the goat, or the goat would eat the cabbage.
# How can the farmer get the goat to the other side of the river without anything being eaten?
# """

# Prompt used in first test of 100 runs
# question = """
# User: A man and a goat are on one side of a river.
# There is a wolf and a cabbage on the other side.
# The man has a boat.
# The boat can carry only the farmer and a single item.
# How can the farmer get the goat to the other side of the river?
# Assistant: """

# Prompt used in second test of 100 runs
# question = """
# A man and a goat are on the left side of a river.
# There is a wolf and a cabbage on the right side of the river.
# The man has a boat.
# The boat can carry only the farmer and a single item.
# How can the farmer get the goat to the other side of the river? """

# Prompt used in third test of 100 runs
question = """
A conversation between User and Assistant. The user asks a question, and the Assistant solves it. The assistant first thinks about the reasoning process in the mind and then provides the user with the answer. The reasoning process and answer are enclosed within <think> </think> and <answer> </answer> tags, respectively, i.e., <think> reasoning process here </think> <answer> answer here </answer>. User:
Solve the following puzzle: A man and a goat are on the left side of a river.
There is a wolf and a cabbage on the right side of the river.
The man has a boat.
The boat can carry only the farmer and a single item.
How can the farmer get the goat to the right side of the river?
Assistant: """


responses: List[str] = []


for i in range(num_responses):
    start_time = time.time()
    # Prepare initial input
    input_ids = tokenizer.encode(f"{question}", return_tensors="pt").to(model.device)
    cache = None

    # Generate one token at a time
    while True:
        # Generate next token using forward pass

        with torch.no_grad():
            outputs = model(
                input_ids=input_ids if cache is None else input_ids[:, -1:],
                past_key_values=cache,
                use_cache=True,
            )

        # Get logits and updated past key values
        if cache is None:
            print("\n--------------------------------\n")
        next_token_logits = outputs.logits[:, -1, :]
        cache = DynamicCache.from_legacy_cache(outputs.past_key_values)

        # Sample next token
        probs = torch.nn.functional.softmax(next_token_logits / temperature, dim=-1)

        # Sort probabilities in descending order
        sorted_probs, sorted_indices = torch.sort(probs, descending=True)
        cumulative_probs = torch.cumsum(sorted_probs, dim=-1)

        # Create nucleus mask
        nucleus_mask = cumulative_probs <= 0.95
        nucleus_mask[..., 1:] = nucleus_mask[..., :-1].clone()
        nucleus_mask[..., 0] = True

        # Apply mask and renormalize
        sorted_probs[~nucleus_mask] = 0
        sorted_probs = sorted_probs / sorted_probs.sum()

        # Sample from filtered distribution
        next_token_idx = torch.multinomial(sorted_probs, num_samples=1)
        next_token = sorted_indices[0, next_token_idx]

        # Print the new token

        print(tokenizer.decode(next_token[0], skip_special_tokens=True), end='', flush=True)

        # Break if we hit the end token or max length
        if next_token[0] == tokenizer.eos_token_id or input_ids.shape[1] >= max_length:
            break

        # Update input_ids for next iteration
        input_ids = torch.cat([input_ids, next_token], dim=-1)

    responses.append(tokenizer.decode(input_ids[0], skip_special_tokens=True))

    print(f"\nTime taken for response {i + 1}: {time.time() - start_time} seconds\n\n")

with open(f"responses/responses_7B_10k_{time.time()}.json", "w") as f:
    json.dump(responses, f)
