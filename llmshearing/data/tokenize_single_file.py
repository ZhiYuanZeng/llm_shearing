from llama_tokenizer import Tokenizer
from tqdm import tqdm
import sys
import os
import json
import numpy as np
import argparse


parser = argparse.ArgumentParser()
parser.add_argument("--raw_dir", type=str, help="Directory for raw data")
parser.add_argument("--target_dir", type=str, help="Target directory to save tokenized numpy")
parser.add_argument("--seq_length", type=int, default=4096, help="Sequence length")
parser.add_argument("--tokenizer", type=str, default=None, help="Tokenizer path (sentencepiece)")
parser.add_argument("--text_key", type=str, default="content", help="the field name of content")
args = parser.parse_args()

index_id = int(os.environ.get("SLURM_ARRAY_TASK_ID"))
file_name = open("jsonl_list.txt").readlines()[index_id].strip()
if 'wanjuan' in file_name:
    args.text_key = 'content'

target_name = os.path.join(args.target_dir, os.path.splitext(file_name)[0] + ".npy")
file_name = os.path.join(args.raw_dir, file_name)
if os.path.exists(target_name):
    print(f"the file ({target_name}) is already processed")
    exit(0)

print("Raw file path:", file_name)
print("Target path:", target_name)

target_folder = os.path.dirname(target_name)
if not os.path.exists(target_folder):
    print("Make target folder:", target_folder)
    os.makedirs(target_folder)

print("Load tokenizer...")
if args.tokenizer is None:
    tokenizer_path = "./tokenizer.model"
else:
    tokenizer_path = args.tokenizer
tok = Tokenizer(tokenizer_path) # this is faster than the huggingface tokenizer
print("Done")

print("Loading file...")
lines = open(file_name).readlines()
print("Done")

buffer = []
data = []
for line in tqdm(lines):
    item = json.loads(line)
    tokens = buffer + tok.encode(item[args.text_key], bos=True, eos=True)
    buffer = []
    for start_id in range(0, len(tokens), args.seq_length):
        if start_id + args.seq_length < len(tokens):
            data.append(tokens[start_id:start_id+args.seq_length])
        else:
            buffer = tokens[start_id:]
            break

print("Stacking numpy...")
data = np.array(np.stack(data), dtype=np.uint32)
print("Done")

print(f"Saving to {target_name}...")
np.save(target_name, data)
print("Done")
