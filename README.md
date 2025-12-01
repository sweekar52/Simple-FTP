# CSC/ECE 573 - Project 2: Go-back-N ARQ Protocol Implementation

## Project Overview

This project implements a Go-back-N Automatic Repeat Request (ARQ) protocol for reliable file transfer over UDP. The system consists of a client (sender) and server (receiver) that transfer a 1MB file between hosts while simulating packet loss. Three experiments were conducted to evaluate how window size (N), maximum segment size (MSS), and packet loss probability (p) affect transfer delay.

## Implementation Details

### System Architecture

**Client (Sender):**
- Reads file data and segments it according to MSS (Maximum Segment Size)
- Implements Go-back-N sliding window protocol
- Maintains window of size N for outstanding (unACKed) segments
- Handles timeout-based retransmissions
- Each segment header contains:
  - 32-bit sequence number
  - 16-bit UDP-style checksum (data only)
  - 16-bit packet type identifier (0101010101010101 for data)

**Server (Receiver):**
- Listens on port 7735
- Implements receiver side of Go-back-N protocol
- Validates sequence numbers and checksums
- Sends cumulative ACKs for in-sequence packets
- Implements probabilistic packet loss service for testing
- ACK header contains:
  - 32-bit sequence number being ACKed
  - 16-bit field of zeros
  - 16-bit packet type identifier (1010101010101010 for ACK)

### Experimental Setup

- **File Size:** ~1 MB
- **Network Path:** Client (home network ) → Server (VCL machine)
- **Timeout Value:** 1.0 second
- **Test Methodology:** 5 trials per configuration, averaged results

---

## Task 1: Effect of Window Size N on Transfer Delay

### Experimental Parameters
- **MSS:** 500 bytes
- **Loss Probability (p):** 0.05
- **Window Sizes (N):** 1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024
- **Total Segments:** 2,099

### Results Summary

| Window Size (N) | Average Delay (s) | Std Dev (s) | Improvement vs N=1 |
|-----------------|-------------------|-------------|--------------------|
| 1               | 129.00            | 4.71        | Baseline           |
| 2               | 113.95            | 9.52        | 11.7%              |
| 4               | 111.56            | 15.45       | 13.5%              |
| 8               | 124.84            | 8.56        | 3.2%               |
| 16              | 115.25            | 5.86        | 10.7%              |
| 32              | 115.43            | 4.82        | 10.5%              |
| 64              | 112.42            | 9.47        | 12.9%              |
| 128             | 107.26            | 5.77        | **16.9%**          |
| 256             | 109.83            | 12.07       | 14.9%              |
| 512             | 108.56            | 8.35        | 15.8%              |
| 1024            | 116.24            | 14.02       | 9.9%               |

![Task 1 Results](task1_plot.png)

### Analysis and Discussion

Small windows underutilize the network pipeline. Medium windows balance pipeline utilization with manageable retransmission overhead. Large windows suffer because Go-back-N retransmits the entire window on timeout - at N=1024, one timeout means resending 1,024 packets, creating a cascade of additional losses (expected 51 more drops at 5% loss rate). The plateau shows Go-back-N's fundamental limitation under packet loss.

---

## Task 2: Effect of MSS on Transfer Delay

### Experimental Parameters
- **Window Size (N):** 64
- **Loss Probability (p):** 0.05
- **MSS Values:** 100, 200, 300, 400, 500, 600, 700, 800, 900, 1000 bytes

### Results Summary

| MSS (bytes) | Segments | Average Delay (s) | Std Dev (s) | Avg Timeouts | Improvement vs MSS=100 |
|-------------|----------|-------------------|-------------|--------------|------------------------|
| 100         | 10,493   | 548.21            | 28.32       | 540.0        | Baseline               |
| 200         | 5,247    | 276.82            | 20.94       | 272.6        | 49.5%                  |
| 300         | 3,498    | 184.46            | 15.70       | 182.4        | 66.4%                  |
| 400         | 2,624    | 142.18            | 14.21       | 140.0        | 74.1%                  |
| 500         | 2,099    | 116.23            | 10.69       | 114.2        | 78.8%                  |
| 600         | 1,749    | 96.49             | 7.37        | 94.8         | 82.4%                  |
| 700         | 1,499    | 87.09             | 5.07        | 85.4         | 84.1%                  |
| 800         | 1,312    | 71.87             | 9.44        | 70.8         | **86.9%**              |
| 900         | 1,166    | 65.28             | 6.63        | 64.2         | 88.1%                  |
| 1000        | 1,050    | 63.45             | 6.70        | 62.2         | **88.4%**              |

![Task 2 Results](task2_plot.png)

### Analysis and Discussion

Larger MSS means fewer segments to transmit. MSS=100 requires 10,493 segments (≈525 expected losses), while MSS=1000 needs only 1,050 segments (≈52 expected losses). Fewer segments = fewer loss opportunities = fewer timeouts. The 10× MSS increase yields 8.7× speedup because timeout count directly tracks segment count. Curve flattens at large MSS because network delay becomes dominant and header overhead (<1%) is already negligible.

---

## Task 3: Effect of Loss Probability on Transfer Delay

### Experimental Parameters
- **Window Size (N):** 64
- **MSS:** 500 bytes
- **Loss Probability (p):** 0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.10
- **Total Segments:** 2,099

### Results Summary

| Loss Prob (p) | Average Delay (s) | Std Dev (s) | Avg Timeouts | Increase vs p=0.01 |
|---------------|-------------------|-------------|--------------|---------------------|
| 0.01          | 21.93             | 4.16        | 21.0         | Baseline            |
| 0.02          | 42.88             | 5.60        | 42.2         | 95.6%               |
| 0.03          | 65.91             | 9.02        | 65.0         | 200.5%              |
| 0.04          | 99.82             | 11.49       | 98.6         | 355.1%              |
| 0.05          | 116.23            | 14.41       | 114.8        | 430.0%              |
| 0.06          | 141.61            | 24.40       | 139.6        | 545.7%              |
| 0.07          | 172.50            | 11.87       | 170.2        | 686.6%              |
| 0.08          | 195.59            | 15.15       | 193.0        | 791.9%              |
| 0.09          | 228.95            | 23.70       | 226.0        | 944.0%              |
| 0.10          | 262.96            | 18.88       | 259.6        | **1099.2%**         |

![Task 3 Results](task3_plot.png)

### Analysis and Discussion

Each lost packet causes a 1-second timeout. With 2,099 segments, p=0.01 causes ≈21 timeouts (actual: 21), p=0.05 causes ≈105 timeouts (actual: 115), p=0.10 causes ≈210 timeouts (actual: 260). The linear relationship is direct: more loss = more timeouts = more delay. Upward curvature occurs because retransmitted packets also get lost - at p=0.10 with N=64, each timeout retransmits 64 packets which generates 6.4 more losses, creating secondary timeouts. This 24% amplification explains why actual timeouts exceed expected losses.
 
---

## Files and Scripts

### Core Implementation
- `Simple_ftp_client.py` - Go-back-N sender with built-in statistics tracking
- `Simple_ftp_server.py` - Go-back-N receiver with probabilistic loss service

### Analysis Scripts
- `analyze_results.py` - Task 1 analysis (Window Size N)
- `analyze_task2.py` - Task 2 analysis (MSS variation)
- `analyze_task3.py` - Task 3 analysis (Loss Probability)

### Data Files
- `task1_stats.jsonl` - Raw data for Task 1
- `task2_stats.jsonl` - Raw data for Task 2  
- `task3_stats.jsonl` - Raw data for Task 3

### Results
- `task1_results.txt` - Formatted results table for Task 1
- `task2_results.txt` - Formatted results table for Task 2
- `task3_results.txt` - Formatted results table for Task 3
- `task1_plot.png` - Window size vs delay plot
- `task2_plot.png` - MSS vs delay plot
- `task3_plot.png` - Loss probability vs delay plot

---

## Usage

### System Requirements: python, matplotlib

### Running the Server
```bash
python Simple_ftp_server.py 7735 output.txt 0.05
```

### Running the Client
```bash
python Simple_ftp_client.py <server-ip> 7735 testfile.txt 64 500
```

### Analyzing Results
```bash
# For each task, run the corresponding analysis script:
python analyze_results.py     # Task 1
python analyze_task2.py        # Task 2
python analyze_task3.py        # Task 3
```
