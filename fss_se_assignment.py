import re
from collections import Counter, defaultdict
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS
import matplotlib

matplotlib.use("Qt5Agg")
import matplotlib.pyplot as plt
import os
from itertools import combinations
import networkx as nx

STOPWORDS = set(ENGLISH_STOP_WORDS)
FILEPATH = "commits_after_2023.txt"
COMMIT_LINE = re.compile(r"^[0-9a-f]{40}\t")
DEFECT_KEYWORDS = {"fix", "error", "bug", "issue"}

LOC_SLOC_INPUT_FILE = "loc_sloc_src.txt"

COMMIT_FILE = "commit_files_since_2023.txt"
TOP_N_PAIRS = 10
COMMIT_HASH_LENGTH = 40
NODE_SIZE = 250
FONT_SIZE = 5


def pretty_print_keywords(counts):
    print("\n=== Top Keywords in Commit Messages ===")
    print(f"{'Keyword':<20}Count")
    print("-" * 32)
    for word, count in counts:
        print(f"{word:<20}{count}")
    print("-" * 32)
    print(f"Total unique keywords: {len(counts)}\n")


def pretty_print_defects(defects_per_month):
    print("\n=== Defect-Related Commits Per Month ===")
    print(f"{'Month':<10}Count")
    print("-" * 20)
    for month in sorted(defects_per_month.keys()):
        print(f"{month:<10}{defects_per_month[month]}")
    print("-" * 20)
    print(f"Total months: {len(defects_per_month)}\n")


def analyse_for_keywords():
    tokens = []
    cleaner = re.compile(r"[^\w\s-]")

    with open(FILEPATH, "r", encoding="utf-16") as f:
        for line in f:
            line = line.strip()

            if not COMMIT_LINE.match(line):
                continue

            commit_hash, date_str, message = line.split("\t", 2)

            message = message.lower()
            message = cleaner.sub(" ", message)
            words = message.split()
            words = [w for w in words if w not in STOPWORDS]

            tokens.extend(words)

    counts = Counter(tokens).most_common(50)
    pretty_print_keywords(counts)
    return counts


def count_defects_per_month(filepath, defect_keywords):
    defects_per_month = Counter()

    with open(filepath, "r", encoding="utf-16") as f:
        for line in f:
            line = line.strip()

            if not COMMIT_LINE.match(line):
                continue

            commit_hash, date_str, message = line.split("\t", 2)
            msg = message.lower()

            if any(keyword in msg for keyword in defect_keywords):
                month = date_str[:7]
                defects_per_month[month] += 1

    pretty_print_defects(defects_per_month)
    return defects_per_month


def plot_defects_per_month(defects_per_month):
    months = sorted(defects_per_month.keys())
    counts = [defects_per_month[m] for m in months]

    plt.figure(figsize=(10, 5))
    plt.plot(months, counts, marker="o")
    plt.xticks(rotation=45)
    plt.xlabel("Month")
    plt.ylabel("Number of Defect Commits")
    plt.title("Defects per Month")
    plt.tight_layout()
    plt.show()


def loc_sloc_analysis_transformers():
    import os
    from radon.raw import analyze

    results = []

    for dirpath, _, filenames in os.walk("src"):
        for fn in filenames:
            if fn.endswith(".py"):
                path = os.path.join(dirpath, fn)

                try:
                    with open(path, "r", encoding="utf-8", errors="replace") as f:
                        content = f.read()
                except Exception:
                    continue

                raw = analyze(content)
                loc, sloc = raw.loc, raw.sloc
                results.append((loc, sloc, path))

    results.sort(key=lambda x: x[0], reverse=True)

    with open("loc_sloc_src.txt", "w", encoding="utf-8") as f:
        for loc, sloc, path in results:
            f.write(f"{loc} | {sloc} | {path}\n")


def count_defects_per_file_per_month(filepath, defect_keywords):
    file_defect_counts = Counter()
    per_file_month_counts = defaultdict(Counter)

    def iter_commits():
        date_str = message = None
        files = []

        with open(filepath, "r", encoding="utf-16") as f:
            for raw in f:
                line = raw.strip()
                if not line:
                    continue

                if COMMIT_LINE.match(line):
                    if date_str is not None:
                        yield date_str, message, files

                    _, date_str, message = line.split("\t", 2)
                    files = []
                else:
                    files.append(line)

        if date_str is not None:
            yield date_str, message, files

    for date_str, message, files in iter_commits():
        msg = message.lower()
        if any(k in msg for k in defect_keywords):
            month = date_str[:7]
            for file in files:
                file_defect_counts[file] += 1
                per_file_month_counts[file][month] += 1

    return file_defect_counts, per_file_month_counts


def plot_top2_files_defects_per_month(filepath, defect_keywords):
    file_defect_counts, per_file_month_counts = count_defects_per_file_per_month(
        filepath, defect_keywords
    )

    top2 = file_defect_counts.most_common(2)
    top_files = [fp for fp, _ in top2]

    print("\n=== Top 2 Files by Defect Commits ===")
    for i, (fp, c) in enumerate(top2, 1):
        print(f"{i}. {fp}  ->  {c} defect commits")
    print()

    all_months = set()
    for fp in top_files:
        for month in per_file_month_counts[fp]:
            all_months.add(month)

    all_months = sorted(all_months)

    plt.figure(figsize=(11, 5))
    for fp in top_files:
        y = [per_file_month_counts[fp].get(m, 0) for m in all_months]
        plt.plot(all_months, y, marker="o", label=fp)

    plt.xticks(rotation=45)
    plt.xlabel("Month")
    plt.ylabel("Defect-Related Commits")
    plt.title("Defect Commits per Month (Top 2 Files)")
    plt.legend()
    plt.tight_layout()
    plt.show()


def iter_commits(filepath):
    date_str = message = None
    files = []

    with open(filepath, "r", encoding="utf-16") as f:
        for raw in f:
            line = raw.strip()
            if not line:
                continue

            if COMMIT_LINE.match(line):
                if date_str is not None:
                    yield date_str, message, files

                _, date_str, message = line.split("\t", 2)
                files = []
            else:
                files.append(line)

    if date_str is not None:
        yield date_str, message, files


def count_ncc_per_file(filepath):
    ncc_counts = Counter()
    per_file_month_counts = defaultdict(Counter)

    for date_str, message, files in iter_commits(filepath):
        month = date_str[:7]
        for file in set(files):
            if file.endswith(".py"):
                ncc_counts[file] += 1
                per_file_month_counts[file][month] += 1

    return ncc_counts, per_file_month_counts


def plot_top_ncc_files(ncc_counts, top_amount):
    top = ncc_counts.most_common(top_amount)
    files = [fp for fp, _ in reversed(top)]
    values = [c for _, c in reversed(top)]

    print("\n=== Top Files by NCC ===")
    for i, (fp, c) in enumerate(top, 1):
        print(f"{i}. {fp} -> {c} commits")

    plt.figure(figsize=(10, 6))
    plt.barh(files, values)
    plt.xlabel("Number of Code Changes (NCC)")
    plt.title(f"Top {top_amount} Python Files by NCC")
    plt.tight_layout()
    plt.show()


def plot_top_ncc_files_per_month(ncc_counts, per_file_month_counts, top_amount=5):
    top = ncc_counts.most_common(top_amount)
    top_files = [fp for fp, _ in top]

    all_months = sorted({
        m for fp in top_files for m in per_file_month_counts[fp].keys()
    })

    plt.figure(figsize=(11, 5))
    for fp in top_files:
        y = [per_file_month_counts[fp].get(m, 0) for m in all_months]
        plt.plot(all_months, y, marker="o", label=fp)

    plt.xticks(rotation=45)
    plt.xlabel("Month")
    plt.ylabel("NCC")
    plt.title(f"NCC per Month (Top {top_amount} Files)")
    plt.legend()
    plt.tight_layout()
    plt.show()


def anaylze_NCC():
    ncc_counts, per_file_month_counts = count_ncc_per_file(FILEPATH)

    print(f"Total commits parsed: {sum(ncc_counts.values())} (file-touches)")
    print(f"Total Python files with NCC: {len(ncc_counts)}")

    plot_top_ncc_files(ncc_counts, 20)
    plot_top_ncc_files_per_month(ncc_counts, per_file_month_counts, 5)


def read_loc_file(path):
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = [p.strip() for p in line.split("|")]
            if len(parts) < 3:
                continue
            try:
                loc = int(parts[0])
                sloc = int(parts[1])
                file_path = parts[2]
            except ValueError:
                continue

            dir_path = os.path.dirname(file_path)
            rows.append({
                "loc": loc,
                "sloc": sloc,
                "file": file_path,
                "dir": dir_path
            })
    return rows


def plot_top_files(rows, top_n):
    rows_sorted = sorted(rows, key=lambda r: r["sloc"], reverse=True)[:top_n]

    files = [r["file"] for r in rows_sorted][::-1]
    slocs = [r["sloc"] for r in rows_sorted][::-1]
    locs = [r["loc"] for r in rows_sorted][::-1]

    plt.figure(figsize=(12, 7))

    plt.barh(files, locs, label="LoC (total)", color="#d0d0d0", alpha=0.6)

    plt.barh(files, slocs, label="SLoC (source)", color="#2ca02c", alpha=0.9)

    plt.xlabel("Lines")
    plt.title(f"Top {top_n} Python Files by SLoC (with LoC Background)")
    plt.legend()
    plt.tight_layout()
    plt.show()


def analyze_SLoC_LoC():
    rows = read_loc_file(LOC_SLOC_INPUT_FILE)
    plot_top_files(rows, 25)


def initial_analyze_coupling(filepath, top_n):
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


def analyze_test_separated(filepath, top_n):
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


def run_test_placement_methods(filepath):
    if not os.path.isdir("tests"):
        print("\033[91m⚠️  WARNING: 'tests' directory not found — name-based placement disabled.\033[0m")
        return

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

    commit_files = {"tests": set(), "python": set()}

    for (f1, f2) in pair_counts:
        if is_python_file(f1):
            commit_files["python"].add(f1)
            if is_test_file(f1):
                commit_files["tests"].add(f1)
        if is_python_file(f2):
            commit_files["python"].add(f2)
            if is_test_file(f2):
                commit_files["tests"].add(f2)

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

    target = "src/transformers/generation/utils.py"

    nb = name_based_placement(target)
    print("name_based_placement: ", nb)

    cb = commit_based_placement(target, pair_counts, commit_files)
    print("commit_based_placement: ", cb)


if __name__ == "__main__":
    analyse_for_keywords()
    defects = count_defects_per_month(FILEPATH, DEFECT_KEYWORDS)
    plot_defects_per_month(defects)
    plot_top2_files_defects_per_month(FILEPATH, DEFECT_KEYWORDS)

    anaylze_NCC()
    analyze_SLoC_LoC()

    initial_analyze_coupling(COMMIT_FILE, TOP_N_PAIRS)
    analyze_test_separated(COMMIT_FILE, TOP_N_PAIRS)
    run_test_placement_methods(COMMIT_FILE)
