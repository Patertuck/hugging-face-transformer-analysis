import re
from collections import Counter, defaultdict
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS
import matplotlib
matplotlib.use("Qt5Agg")
import matplotlib.pyplot as plt

STOPWORDS = set(ENGLISH_STOP_WORDS)
FILEPATH = "commits_after_2023.txt"
COMMIT_LINE = re.compile(r"^[0-9a-f]{40}\t")

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
                month = date_str[:7]  # YYYY-MM
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




if __name__ == "__main__":
    analyse_for_keywords()
    defect_keywords = {"fix", "error", "bug", "issue"} # Identified because of the analysis above

    defects = count_defects_per_month(FILEPATH, defect_keywords)
    plot_defects_per_month(defects)

    plot_top2_files_defects_per_month(FILEPATH, defect_keywords)
