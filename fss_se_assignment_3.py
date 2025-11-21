from collections import defaultdict
from itertools import combinations
import networkx as nx
import matplotlib.pyplot as plt

COMMIT_FILE = "commit_files_since_2023.txt"
TOP_N_PAIRS = 10
COMMIT_HASH_LENGTH = 40
NODE_SIZE = 2000
FONT_SIZE = 10

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


if __name__ == "__main__":
    initial_analyze_coupling()
