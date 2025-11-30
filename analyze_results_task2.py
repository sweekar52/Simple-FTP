#!/usr/bin/env python3
"""
Analyze Transfer Statistics for Task 2 (MSS Variation)

Usage: python analyze_task2.py

Reads task2_stats.jsonl and generates:
- task2_results.txt (formatted table)
- task2_plot.png (delay vs MSS plot)
"""

import json
import statistics
from collections import defaultdict
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend

def load_stats(filename='task2_stats.jsonl'):
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

def group_by_mss(stats):
    """Group statistics by MSS"""
    grouped = defaultdict(list)
    for stat in stats:
        mss = stat['mss']
        grouped[mss].append(stat['elapsed_time'])
    return grouped

def generate_table(grouped_stats):
    """Generate formatted results table"""
    
    print("=" * 120)
    print("Task 2 Results: Effect of MSS on Transfer Delay")
    print("=" * 120)
    
    if grouped_stats:
        sample = list(grouped_stats.values())[0]
        if sample:
            # Get metadata from first entry (should be same for all)
            stats = load_stats()
            if stats:
                print(f"File size: {stats[0]['file_size']} bytes ({stats[0]['file_size']/1024/1024:.2f} MB)")
                print(f"Window Size N: {stats[0]['window_size']}")
                print(f"Loss probability: 0.05")
    
    print("=" * 120)
    print()
    
    # Header
    header = f"{'MSS (bytes)':<15} {'Trial 1':<12} {'Trial 2':<12} {'Trial 3':<12} {'Trial 4':<12} {'Trial 5':<12} {'Average':<12} {'Std Dev':<12}"
    print(header)
    print("-" * 120)
    
    output_lines = []
    
    # Sort by MSS
    for mss in sorted(grouped_stats.keys()):
        times = grouped_stats[mss]
        
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
        
        line = f"{mss:<15} {trial_str} {avg_str:<12} {std_str:<12}"
        print(line)
        output_lines.append((mss, times, avg_str, std_str, line))
    
    print("-" * 120)
    
    return output_lines

def save_table(output_lines, filename='task2_results.txt'):
    """Save formatted table to file"""
    with open(filename, 'w') as f:
        f.write("Task 2 Results: Effect of MSS on Transfer Delay\n")
        f.write("=" * 120 + "\n")
        
        stats = load_stats()
        if stats:
            f.write(f"File size: {stats[0]['file_size']} bytes ({stats[0]['file_size']/1024/1024:.2f} MB)\n")
            f.write(f"Window Size N: {stats[0]['window_size']}\n")
            f.write(f"Loss probability: 0.05\n")
        
        f.write("=" * 120 + "\n\n")
        
        header = f"{'MSS (bytes)':<15} {'Trial 1':<12} {'Trial 2':<12} {'Trial 3':<12} {'Trial 4':<12} {'Trial 5':<12} {'Average':<12} {'Std Dev':<12}"
        f.write(header + "\n")
        f.write("-" * 120 + "\n")
        
        for _, _, _, _, line in output_lines:
            f.write(line + "\n")
        
        f.write("-" * 120 + "\n")
    
    print(f"\nResults saved to {filename}")

def generate_plot(output_lines, filename='task2_plot.png'):
    """Generate plot of average delay vs MSS"""
    
    # Extract data for plotting
    mss_values = []
    averages = []
    std_devs = []
    
    for mss, times, avg_str, std_str, _ in output_lines:
        if avg_str != "N/A" and len(times) > 0:
            mss_values.append(mss)
            averages.append(statistics.mean(times))
            std_devs.append(statistics.stdev(times) if len(times) > 1 else 0)
    
    if not mss_values:
        print("No data to plot!")
        return
    
    # Create plot
    plt.figure(figsize=(12, 7))
    
    # Plot with error bars
    plt.errorbar(mss_values, averages, yerr=std_devs, 
                 fmt='o-', capsize=5, capthick=2, 
                 markersize=8, linewidth=2, color='#2E86AB',
                 label='Average Delay')
    
    plt.xlabel('Maximum Segment Size (MSS) [bytes]', fontsize=12, fontweight='bold')
    plt.ylabel('Average Delay (seconds)', fontsize=12, fontweight='bold')
    plt.title('Task 2: Effect of MSS on Transfer Delay\n(N=64, p=0.05)', 
              fontsize=14, fontweight='bold')
    plt.grid(True, alpha=0.3, linestyle='--')
    plt.legend(fontsize=10)
    
    # Set x-axis ticks to actual MSS values
    plt.xticks(mss_values, [str(m) for m in mss_values], rotation=45)
    
    plt.tight_layout()
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"Plot saved to {filename}")

def analyze_segments(stats):
    """Analyze relationship between MSS and total segments"""
    print("\n" + "=" * 60)
    print("Additional Analysis: MSS vs Segments vs Timeouts")
    print("=" * 60)
    print(f"{'MSS':<10} {'Segments':<12} {'Avg Timeouts':<15} {'Avg Time':<12}")
    print("-" * 60)
    
    grouped = defaultdict(lambda: {'times': [], 'timeouts': [], 'segments': []})
    
    for stat in stats:
        mss = stat['mss']
        grouped[mss]['times'].append(stat['elapsed_time'])
        grouped[mss]['timeouts'].append(stat['timeout_count'])
        grouped[mss]['segments'].append(stat['total_segments'])
    
    for mss in sorted(grouped.keys()):
        data = grouped[mss]
        avg_time = statistics.mean(data['times'])
        avg_timeouts = statistics.mean(data['timeouts'])
        segments = data['segments'][0]  # Should be same for all
        
        print(f"{mss:<10} {segments:<12} {avg_timeouts:<15.1f} {avg_time:<12.2f}")
    
    print("-" * 60)

def main():
    print("Loading statistics from task2_stats.jsonl...")
    stats = load_stats()
    
    if not stats:
        return
    
    print(f"Found {len(stats)} transfer records\n")
    
    # Group by MSS
    grouped = group_by_mss(stats)
    
    print(f"MSS values tested: {sorted(grouped.keys())}")
    print(f"Trials per MSS:")
    for mss in sorted(grouped.keys()):
        print(f"  MSS={mss}: {len(grouped[mss])} trials")
    print()
    
    # Generate table
    output_lines = generate_table(grouped)
    
    # Save table
    save_table(output_lines)
    
    # Generate plot
    generate_plot(output_lines)
    
    # Additional analysis
    analyze_segments(stats)
    
    print("\nDone!")
    print()
    print("Summary:")
    total_trials = sum(len(times) for times in grouped.values())
    expected_mss_values = list(range(100, 1001, 100))
    completed_mss_values = len(grouped)
    print(f"  Total transfers: {total_trials}")
    print(f"  MSS values completed: {completed_mss_values}/{len(expected_mss_values)}")
    missing = set(expected_mss_values) - set(grouped.keys())
    if missing:
        print(f"  Missing MSS values: {sorted(missing)}")

if __name__ == "__main__":
    main()