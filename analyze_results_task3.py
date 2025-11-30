#!/usr/bin/env python3
"""
Analyze Task 3 Results and Generate Plots

Usage: python analyze_results_task3.py

Reads transfer_stats.jsonl and generates:
- task3_results.txt (formatted table)
- task3_plot.png (delay vs loss probability plot)
"""

import json
import statistics
from collections import defaultdict
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend


def load_stats(filename='transfer_stats.jsonl'):
    """Load all statistics from JSONL file"""
    stats = []
    try:
        with open(filename, 'r') as f:
            for line in f:
                line = line.strip()
                if line:  # Skip empty lines
                    stats.append(json.loads(line))
    except FileNotFoundError:
        print(f"Error: {filename} not found!")
        print("Run the experiment first using Simple_ftp_client.py")
        return []

    return stats


def group_by_loss_prob(stats):
    """Group statistics by server probability"""
    grouped = defaultdict(list)
    for stat in stats:
        # Use server_probability field
        p = stat.get('server_probability', stat.get('loss_prob'))
        if p is not None:
            grouped[p].append(stat['elapsed_time'])
    return grouped


def generate_table(grouped_stats):
    """Generate formatted results table"""

    print("=" * 120)
    print("Task 3 Results: Effect of Loss Probability on Transfer Delay")
    print("=" * 120)

    if grouped_stats:
        sample = list(grouped_stats.values())[0]
        if sample:
            # Get metadata from first entry (should be same for all)
            stats = load_stats()
            if stats:
                print(f"File size: {stats[0]['file_size']} bytes ({stats[0]['file_size']/1024/1024:.2f} MB)")
                print(f"MSS: {stats[0]['mss']} bytes")
                print(f"Window size (N): {stats[0]['window_size']}")

    print("=" * 120)
    print()

    # Header - similar to task1 but with Probability instead of Window Size
    header = f"{'Probability (p)':<17} {'Trial 1':<12} {'Trial 2':<12} {'Trial 3':<12} {'Trial 4':<12} {'Trial 5':<12} {'Average':<12} {'Std Dev':<12}"
    print(header)
    print("-" * 120)

    output_lines = []

    # Sort by loss probability
    for p in sorted(grouped_stats.keys()):
        times = grouped_stats[p]

        # Format trials (pad with "N/A" if < 5 trials)
        trial_str = ""
        for i in range(5):
            if i < len(times):
                trial_str += f"{times[i]:<12.2f}"
            else:
                trial_str += "N/A".ljust(12)

        # Calculate statistics
        if len(times) > 0:
            avg = statistics.mean(times)
            std = statistics.stdev(times) if len(times) > 1 else 0
            avg_str = f"{avg:.2f}"
            std_str = f"{std:.2f}"
        else:
            avg_str = "N/A"
            std_str = "N/A"

        # Format probability column to match task1 style
        line = f"{p:<17.2f} {trial_str} {avg_str:<12} {std_str:<12}"
        print(line)
        output_lines.append((p, times, avg_str, std_str, line))

    print("-" * 120)

    return output_lines


def save_table(output_lines, filename='task3_results.txt'):
    """Save formatted table to file"""
    with open(filename, 'w') as f:
        f.write("Task 3 Results: Effect of Loss Probability on Transfer Delay\n")
        f.write("=" * 120 + "\n")

        stats = load_stats()
        if stats:
            f.write(f"File size: {stats[0]['file_size']} bytes ({stats[0]['file_size']/1024/1024:.2f} MB)\n")
            f.write(f"MSS: {stats[0]['mss']} bytes\n")
            f.write(f"Window size (N): {stats[0]['window_size']}\n")

        f.write("=" * 120 + "\n\n")

        header = f"{'Probability (p)':<17} {'Trial 1':<12} {'Trial 2':<12} {'Trial 3':<12} {'Trial 4':<12} {'Trial 5':<12} {'Average':<12} {'Std Dev':<12}"
        f.write(header + "\n")
        f.write("-" * 120 + "\n")

        for _, _, _, _, line in output_lines:
            f.write(line + "\n")

        f.write("-" * 120 + "\n")

    print(f"\nResults saved to {filename}")


def generate_plot(output_lines, filename='task3_plot.png'):
    """Generate plot of average delay vs loss probability"""

    # Extract data for plotting
    loss_probs = []
    averages = []
    std_devs = []

    for p, times, avg_str, std_str, _ in output_lines:
        if avg_str != "N/A" and len(times) > 0:
            loss_probs.append(p)
            averages.append(statistics.mean(times))
            std_devs.append(statistics.stdev(times) if len(times) > 1 else 0)

    if not loss_probs:
        print("No data to plot!")
        return

    # Create plot
    plt.figure(figsize=(12, 7))

    # Plot with error bars
    plt.errorbar(loss_probs, averages, yerr=std_devs,
                 fmt='o-', capsize=5, capthick=2,
                 markersize=8, linewidth=2,
                 label='Average Delay')

    plt.xlabel('Loss Probability (p)', fontsize=12, fontweight='bold')
    plt.ylabel('Average Delay (seconds)', fontsize=12, fontweight='bold')
    plt.title('Task 3: Effect of Loss Probability on Transfer Delay\n(N=64, MSS=500 bytes)',
              fontsize=14, fontweight='bold')
    plt.grid(True, alpha=0.3, linestyle='--')
    plt.legend(fontsize=10)

    # Set x-axis ticks to actual loss probabilities
    plt.xticks(loss_probs, [f"{p:.2f}" for p in loss_probs], rotation=0)

    plt.tight_layout()
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"Plot saved to {filename}")


def main():
    print("Loading statistics from transfer_stats.jsonl...")
    stats = load_stats()

    if not stats:
        return

    print(f"Found {len(stats)} transfer records\n")

    # Group by loss probability
    grouped = group_by_loss_prob(stats)

    print(f"Loss probabilities tested: {sorted(grouped.keys())}")
    print(f"Trials per loss probability:")
    for p in sorted(grouped.keys()):
        print(f"  p={p:.2f}: {len(grouped[p])} trials")
    print()

    # Generate table
    output_lines = generate_table(grouped)

    # Save table
    save_table(output_lines)

    # Generate plot
    generate_plot(output_lines)

    print("\nDone!")
    print()
    print("Summary:")
    total_trials = sum(len(times) for times in grouped.values())
    expected_probs = [round(p * 0.01, 2) for p in range(1, 11)]  # 0.01 to 0.10
    completed_probs = len(grouped)
    print(f"  Total transfers: {total_trials}")
    print(f"  Loss probabilities completed: {completed_probs}/{len(expected_probs)}")
    missing_probs = set(expected_probs) - set(grouped.keys())
    if missing_probs:
        print(f"  Missing probabilities: {sorted(missing_probs)}")


if __name__ == "__main__":
    main()
