from collections import defaultdict
from itertools import combinations
import networkx as nx
import matplotlib.pyplot as plt
import os

COMMIT_FILE = "commit_files_since_2023.txt"
TOP_N_PAIRS = 10
COMMIT_HASH_LENGTH = 40
NODE_SIZE = 250
FONT_SIZE = 5

def initial_analyze_coupling(filepath=COMMIT_FILE, top_n=TOP_N_PAIRS):
    with open(filepath, "r") as f:
        lines = [line.strip() for line in f if line.strip()]

    commits = []
    current_commit = []
    for line in lines:
        if len(line) == COMMIT_HASH_LENGTH:
            if current_commit:
                commits.append(current_commit)
            current_commit = []
        else:
            current_commit.append(line)
    if current_commit:
        commits.append(current_commit)

    pair_counts = defaultdict(int)
    for commit in commits:
        for f1, f2 in combinations(sorted(set(commit)), 2):
            pair_counts[(f1, f2)] += 1

    top_pairs = sorted(pair_counts.items(), key=lambda x: x[1], reverse=True)[:top_n]

    for pair, count in top_pairs:
        print(pair, count)

    G = nx.Graph()
    for (f1, f2), weight in top_pairs:
        G.add_edge(f1, f2, weight=weight)

    pos = nx.spring_layout(G)
    nx.draw(G, pos, with_labels=True, node_size=NODE_SIZE, font_size=FONT_SIZE)
    plt.show()

def analyze_test_separated(filepath=COMMIT_FILE, top_n=TOP_N_PAIRS):
    with open(filepath, "r") as f:
        lines = [line.strip() for line in f if line.strip()]

    commits = []
    current_commit = []
    for line in lines:
        if len(line) == COMMIT_HASH_LENGTH:
            if current_commit:
                commits.append(current_commit)
            current_commit = []
        else:
            current_commit.append(line)
    if current_commit:
        commits.append(current_commit)

    def is_test_file(file_path):
        return os.path.basename(file_path).startswith("test") and file_path.endswith(".py")

    def is_python_file(file_path):
        return file_path.endswith(".py")

    pair_counts = defaultdict(int)
    for commit in commits:
        py_files = [f for f in commit if is_python_file(f)]
        for f1, f2 in combinations(sorted(set(py_files)), 2):
            if (is_test_file(f1) and not is_test_file(f2)) or (is_test_file(f2) and not is_test_file(f1)):
                pair_counts[(f1, f2)] += 1

    top_pairs = sorted(pair_counts.items(), key=lambda x: x[1], reverse=True)[:top_n]

    for (f1, f2), count in top_pairs:
        print((f1, f2), count)

    G = nx.Graph()
    for (f1, f2), weight in top_pairs:
        G.add_edge(f1, f2, weight=weight)

    pos = nx.spring_layout(G)
    nx.draw(G, pos, with_labels=True, node_size=NODE_SIZE, font_size=FONT_SIZE)
    plt.show()

def name_based_placement(target_file, test_dir="tests"):
    base = os.path.basename(target_file).replace(".py", "")
    candidates = [f for f in os.listdir(test_dir) if f.endswith(".py")]
    for test_file in candidates:
        if base in test_file:
            return os.path.join(test_dir, test_file)
    return None

def commit_based_placement(target_file, commit_pairs, test_files):
    coupling_scores = defaultdict(int)
    for (f1, f2), count in commit_pairs.items():
        if target_file in (f1, f2):
            other = f2 if f1 == target_file else f1
            if other in test_files:
                coupling_scores[other] += count
    if not coupling_scores:
        return None
    return max(coupling_scores, key=coupling_scores.get)

if __name__ == "__main__":
    # initial_analyze_coupling()
    analyze_test_separated()
