import re
from collections import Counter, defaultdict
import matplotlib
matplotlib.use("Qt5Agg")
import matplotlib.pyplot as plt

FILEPATH = "commits_after_2023.txt"

COMMIT_LINE = re.compile(r"^[0-9a-f]{40}\t")


def iter_commits(filepath):
    date_str = message = None
    files = []

    with open(filepath, "r", encoding="utf-16") as f:
        for raw in f:
            line = raw.strip()
            if not line:
                continue

            if COMMIT_LINE.match(line):
                # emit previous commit
                if date_str is not None:
                    yield date_str, message, files

                _, date_str, message = line.split("\t", 2)
                files = []
            else:
                files.append(line)

    # emit last commit
    if date_str is not None:
        yield date_str, message, files


def count_ncc_per_file(filepath):
    ncc_counts = Counter()
    per_file_month_counts = defaultdict(Counter)

    for date_str, message, files in iter_commits(filepath):
        month = date_str[:7]  # YYYY-MM
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


if __name__ == "__main__":
    anaylze_NCC()

