#!/usr/bin/env python3
import sys
import socket
import struct
import random
import signal
import time

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
    if len(sys.argv) != 4:
        print("Usage: python3 Simple_ftp_server.py <port#> <file-name> <p>")
        sys.exit(1)
    
    port = int(sys.argv[1])
    filename = sys.argv[2]
    loss_prob = float(sys.argv[3])
    
    # Create UDP socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind(('', port))
    server_socket.settimeout(1.0)  # 1 second timeout to allow signal handling
    
    print(f"Server listening on port {port}...")
    print(f"Saving to file: {filename}")
    print(f"Packet loss probability: {loss_prob}")
    print("Press Ctrl+C to stop\n")
    
    expected_seq_num = 0
    output_file = None
    last_packet_time = time.time()
    received_any_packet = False  # Track if we've received at least one packet
    idle_timeout = 30  # Exit after 30 seconds of no packets (generous for retransmissions)
    
    # Setup signal handler for graceful shutdown
    def signal_handler(sig, frame):
        print("\n\nShutting down server gracefully...")
        if output_file:
            output_file.close()
        server_socket.close()
        sys.exit(130)  # Standard exit code for SIGINT (Ctrl+C)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        output_file = open(filename, 'wb')
        
        while True:
            try:
                # Receive packet
                packet, client_address = server_socket.recvfrom(65535)
            except socket.timeout:
                # Timeout is normal, just continue waiting
                # Flush the file periodically to avoid data loss
                output_file.flush()
                
                # Only check idle timeout if we've received at least one packet
                if received_any_packet and (time.time() - last_packet_time > idle_timeout):
                    print(f"\nNo data received for {idle_timeout} seconds. Transfer complete.")
                    break
                
                continue
            
            # Parse header (32-bit seq, 16-bit checksum, 16-bit type)
            if len(packet) < 8:
                continue
            
            seq_num = struct.unpack('!I', packet[0:4])[0]
            recv_checksum = struct.unpack('!H', packet[4:6])[0]
            packet_type = struct.unpack('!H', packet[6:8])[0]
            data = packet[8:]
            
            # Check if this is a data packet
            if packet_type != 0b0101010101010101:
                continue
            
            # Mark that we've received at least one data packet
            # and update timer (even if we drop it - client is still active)
            received_any_packet = True
            last_packet_time = time.time()
            
            # Probabilistic loss service
            r = random.random()
            if r <= loss_prob:
                print(f"Packet loss, sequence number = {seq_num}")
                continue
            
            # Compute checksum of data
            computed_checksum = compute_checksum(data)
            
            # Check if packet is in-sequence and checksum is correct
            if seq_num == expected_seq_num and computed_checksum == recv_checksum:
                # Write data to file
                output_file.write(data)
                
                # Send ACK
                ack_packet = struct.pack('!I', seq_num)  # 32-bit seq number
                ack_packet += struct.pack('!H', 0)  # 16-bit all zeros
                ack_packet += struct.pack('!H', 0b1010101010101010)  # 16-bit ACK type
                
                server_socket.sendto(ack_packet, client_address)
                
                expected_seq_num += 1
            # If out-of-sequence or checksum incorrect, do nothing (Go-back-N discards)
            
    except Exception as e:
        print(f"\nError: {e}")
    finally:
        if output_file:
            output_file.close()
        server_socket.close()
        print("Server closed.")

if __name__ == "__main__":
    main()