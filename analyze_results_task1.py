#!/usr/bin/env python3
"""
Analyze Transfer Statistics and Generate Results

Usage: python analyze_results.py

Reads transfer_stats.jsonl and generates:
- task1_results.txt (formatted table)
- task1_plot.png (delay vs window size plot)
"""

import json
import statistics
from collections import defaultdict
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend

def load_stats(filename='task1_stats.jsonl'):
    """Load all statistics from JSONL file"""
    stats = []
    try:
        with open(filename, 'r') as f:
            for line in f:
                stats.append(json.loads(line.strip()))
    except FileNotFoundError:
        print(f"Error: {filename} not found!")
        print("Run some transfers first using Simple_ftp_client.py")
        return []
    
    return stats

def group_by_window_size(stats):
    """Group statistics by window size"""
    grouped = defaultdict(list)
    for stat in stats:
        N = stat['window_size']
        grouped[N].append(stat['elapsed_time'])
    return grouped

def generate_table(grouped_stats):
    """Generate formatted results table"""
    
    print("=" * 120)
    print("Task 1 Results: Effect of Window Size N on Transfer Delay")
    print("=" * 120)
    
    if grouped_stats:
        sample = list(grouped_stats.values())[0]
        if sample:
            # Get metadata from first entry (should be same for all)
            stats = load_stats()
            if stats:
                print(f"File size: {stats[0]['file_size']} bytes ({stats[0]['file_size']/1024/1024:.2f} MB)")
                print(f"MSS: {stats[0]['mss']} bytes")
                print(f"Loss probability: 0.05")
    
    print("=" * 120)
    print()
    
    # Header
    header = f"{'Window Size (N)':<15} {'Trial 1':<12} {'Trial 2':<12} {'Trial 3':<12} {'Trial 4':<12} {'Trial 5':<12} {'Average':<12} {'Std Dev':<12}"
    print(header)
    print("-" * 120)
    
    output_lines = []
    
    # Sort by window size
    for N in sorted(grouped_stats.keys()):
        times = grouped_stats[N]
        
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
        
        line = f"{N:<15} {trial_str} {avg_str:<12} {std_str:<12}"
        print(line)
        output_lines.append((N, times, avg_str, std_str, line))
    
    print("-" * 120)
    
    return output_lines

def save_table(output_lines, filename='task1_results.txt'):
    """Save formatted table to file"""
    with open(filename, 'w') as f:
        f.write("Task 1 Results: Effect of Window Size N on Transfer Delay\n")
        f.write("=" * 120 + "\n")
        
        stats = load_stats()
        if stats:
            f.write(f"File size: {stats[0]['file_size']} bytes ({stats[0]['file_size']/1024/1024:.2f} MB)\n")
            f.write(f"MSS: {stats[0]['mss']} bytes\n")
            f.write(f"Loss probability: 0.05\n")
        
        f.write("=" * 120 + "\n\n")
        
        header = f"{'Window Size (N)':<15} {'Trial 1':<12} {'Trial 2':<12} {'Trial 3':<12} {'Trial 4':<12} {'Trial 5':<12} {'Average':<12} {'Std Dev':<12}"
        f.write(header + "\n")
        f.write("-" * 120 + "\n")
        
        for _, _, _, _, line in output_lines:
            f.write(line + "\n")
        
        f.write("-" * 120 + "\n")
    
    print(f"\nResults saved to {filename}")

def generate_plot(output_lines, filename='task1_plot.png'):
    """Generate plot of average delay vs window size"""
    
    # Extract data for plotting
    window_sizes = []
    averages = []
    std_devs = []
    
    for N, times, avg_str, std_str, _ in output_lines:
        if avg_str != "N/A" and len(times) > 0:
            window_sizes.append(N)
            averages.append(statistics.mean(times))
            std_devs.append(statistics.stdev(times) if len(times) > 1 else 0)
    
    if not window_sizes:
        print("No data to plot!")
        return
    
    # Create plot
    plt.figure(figsize=(12, 7))
    
    # Plot with error bars
    plt.errorbar(window_sizes, averages, yerr=std_devs, 
                 fmt='o-', capsize=5, capthick=2, 
                 markersize=8, linewidth=2,
                 label='Average Delay')
    
    plt.xscale('log', base=2)  # Log scale for x-axis (base 2 for window sizes)
    plt.xlabel('Window Size N', fontsize=12, fontweight='bold')
    plt.ylabel('Average Delay (seconds)', fontsize=12, fontweight='bold')
    plt.title('Task 1: Effect of Window Size N on Transfer Delay\n(MSS=500 bytes, p=0.05)', 
              fontsize=14, fontweight='bold')
    plt.grid(True, alpha=0.3, linestyle='--')
    plt.legend(fontsize=10)
    
    # Set x-axis ticks to actual window sizes
    plt.xticks(window_sizes, [str(n) for n in window_sizes], rotation=45)
    
    plt.tight_layout()
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"Plot saved to {filename}")

def main():
    print("Loading statistics from task1_stats.jsonl...")
    stats = load_stats()
    
    if not stats:
        return
    
    print(f"Found {len(stats)} transfer records\n")
    
    # Group by window size
    grouped = group_by_window_size(stats)
    
    print(f"Window sizes tested: {sorted(grouped.keys())}")
    print(f"Trials per window size:")
    for N in sorted(grouped.keys()):
        print(f"  N={N}: {len(grouped[N])} trials")
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
    expected_window_sizes = [1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024]
    completed_window_sizes = len(grouped)
    print(f"  Total transfers: {total_trials}")
    print(f"  Window sizes completed: {completed_window_sizes}/{len(expected_window_sizes)}")
    print(f"  Missing window sizes: {set(expected_window_sizes) - set(grouped.keys())}")

if __name__ == "__main__":
    main()