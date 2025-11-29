#!/usr/bin/env python3
import sys
import socket
import struct
import time
import json
import os

def compute_checksum(data):
    """Compute 16-bit checksum similar to UDP checksum"""
    if len(data) % 2 == 1:
        data += b'\x00'
    
    checksum = 0
    for i in range(0, len(data), 2):
        word = (data[i] << 8) + data[i + 1]
        checksum += word
        checksum = (checksum & 0xFFFF) + (checksum >> 16)
    
    return ~checksum & 0xFFFF

def main():
    if len(sys.argv) != 6:
        print("Usage: python Simple_ftp_client.py <server-host-name> <server-port#> <file-name> <N> <MSS>")
        sys.exit(1)
    
    server_host = sys.argv[1]
    server_port = int(sys.argv[2])
    filename = sys.argv[3]
    window_size = int(sys.argv[4])
    mss = int(sys.argv[5])
    
    # Create UDP socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.settimeout(1.0)  # 1 second timeout
    
    def create_segment(data, seq_num):
        """Create a segment with header for given data and sequence number"""
        # Compute checksum
        checksum = compute_checksum(data)
        
        # Create segment header
        header = struct.pack('!I', seq_num)  # 32-bit sequence number
        header += struct.pack('!H', checksum)  # 16-bit checksum
        header += struct.pack('!H', 0b0101010101010101)  # 16-bit data packet type
        
        return header + data
    
    # Read file data upfront
    with open(filename, 'rb') as f:
        file_data = f.read()
    
    total_segments = (len(file_data) + mss - 1) // mss
    
    def create_segment_from_data(seq_num):
        """Create segment for given sequence number from file data"""
        start = seq_num * mss
        end = min(start + mss, len(file_data))
        data = file_data[start:end]
        return create_segment(data, seq_num)
    
    # Go-back-N protocol with sliding window buffer
    base = 0
    next_seq_num = 0
    window_buffer = {}  # Dictionary to store sent but unACKed segments
    
    # Statistics tracking
    timeout_count = 0
    start_time = time.time()
    
    while True:
        # Send new packets within window
        while next_seq_num < base + window_size and next_seq_num < total_segments:
            # Create and send segment
            segment = create_segment_from_data(next_seq_num)
            client_socket.sendto(segment, (server_host, server_port))
            
            # Buffer the segment for potential retransmission
            window_buffer[next_seq_num] = segment
            next_seq_num += 1
        
        # Check if we're done - all segments sent AND all ACKed
        if base == total_segments:
            break
        
        # Wait for ACK
        try:
            ack_packet, _ = client_socket.recvfrom(1024)
            
            # Parse ACK
            if len(ack_packet) >= 8:
                ack_seq_num = struct.unpack('!I', ack_packet[0:4])[0]
                zeros = struct.unpack('!H', ack_packet[4:6])[0]
                ack_type = struct.unpack('!H', ack_packet[6:8])[0]
                
                # Verify it's an ACK packet
                if ack_type == 0b1010101010101010 and zeros == 0:
                    # Remove ACKed segments from buffer
                    for seq in range(base, ack_seq_num + 1):
                        if seq in window_buffer:
                            del window_buffer[seq]
                    
                    # Move window
                    base = ack_seq_num + 1
        
        except socket.timeout:
            # Timeout - retransmit all packets in window
            print(f"Timeout, sequence number = {base}")
            timeout_count += 1
            
            # Retransmit all segments in the window
            for seq in range(base, next_seq_num):
                if seq in window_buffer:
                    client_socket.sendto(window_buffer[seq], (server_host, server_port))
    
    end_time = time.time()
    elapsed_time = end_time - start_time
    
    client_socket.close()
    
    # Save statistics to JSON file
    stats = {
        'window_size': window_size,
        'mss': mss,
        'file_size': len(file_data),
        'total_segments': total_segments,
        'elapsed_time': elapsed_time,
        'timeout_count': timeout_count,
        'server': f"{server_host}:{server_port}",
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
    }
    
    # Append to stats file
    stats_file = 'transfer_stats.jsonl'
    with open(stats_file, 'a') as f:
        f.write(json.dumps(stats) + '\n')
    
    print(f"\nTransfer complete!")
    print(f"Time: {elapsed_time:.2f} seconds")
    print(f"Timeouts: {timeout_count}")
    print(f"Stats saved to {stats_file}")

if __name__ == "__main__":
    main()