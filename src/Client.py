# Import socket module
import socket
import random
import string
import threading
from typing import Optional, Any
import signal
import sys
import argparse

from Transcation import BlockChain
import pickle

exit_flag = 0

# TODO: On multiple servers, how to stop mining from happening


# thread fuction
def threaded(blockchain):
    N = 25
    blockchain.new_block(''.join(random.choices(string.ascii_uppercase + string.digits, k=N)))


def signal_handler(sig, frame):
    global exit_flag
    print('Closing server')
    exit_flag = 1
    sys.exit(0)


def Main():
    global exit_flag

    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--ip", type=str, default="127.0.0.1", dest='host',
                        help="Server IP (default 127.0.0.1)")
    args = parser.parse_args()
    host = args.host

    # Define the port on which you want to connect
    port = 12345

    conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # connect to server on local computer
    conn.connect((host, port))

    conn.send("ACK".encode('ascii'))

    while True:
        try:
            if exit_flag is 0:
                break
            # Receive up-to-date blockchain
            length = int(conn.recv(64))
            data = b''
            while len(data) < length:
                # doing it in batches is generally better than trying
                # to do it all in one go, so I believe.
                to_read = length - len(data)
                data += conn.recv(
                    4096 if to_read > 4096 else to_read)
            blockchain: BlockChain = pickle.loads(data)
            # blockchain: BlockChain = pickle.loads(conn.recv(4096))

            # Start new thread to run the mining
            t = threading.Thread(target=threaded, args=(blockchain, ))
            t.daemon = True
            t.start()

            # Wait until block is calculated
            t.join()

            # Send last block to the server
            conn.send(pickle.dumps(blockchain.lookup_block_by_index(-1)))

            # Wait for server to check block and add it to main blockchain
            msg = conn.recv(1024)

            # If the block was incorrect remove it and try again
            if msg is not "OK":
                blockchain.remove_last_block()
                print("Error: Block generated was incorrect, trying again")
        except socket.error as e:
            print(e)
            exit_flag = 1
            break
    conn.close()
    sys.exit(exit_flag)


if __name__ == '__main__':
    Main()
