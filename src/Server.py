# import socket programming library
import socket
from Transcation import BlockChain
import signal
import sys
import threading
import pickle
import argparse

print_lock = threading.Lock()
blockchain_lock = threading.Lock()
connection_list_lock = threading.Lock()

# TODO: How to stop mining from happening. Event on mine happen to all other thread. Non blocking recv


def signal_handler(sig, frame):
    print('Closing server')
    sys.exit(0)


# thread fuction
def threaded(conn, addr, blockchain, list_conections):
    while True:
        # Once connection is establish, send the full blockchain to the client
        blockchain_lock.acquire()
        conn.send(len(blockchain))
        conn.send(pickle.dumps(blockchain))
        blockchain_lock.release()

        # The client starts to mine, wait until it finishes
        block = pickle.loads(conn.recv(4096))
        if not block:
            break

        # Attempt to add block given to the chain
        blockchain_lock.acquire()
        if blockchain.add_block(block):
            conn.send("OK".encode('ascii'))
        else:
            conn.send("FAIL".encode('ascii'))
        blockchain_lock.release()

    # connection_list_lock.acquire()
    # index = [index for index, i in list_conections if i == conn]
    # del list_conections[index]
    # connection_list_lock.release()
    print_lock.acquire()
    print('Disconnecting from :', addr[0], ':', addr[1])
    print_lock.release()
    conn.close()


def Main():
    host = ""
    port = 12345

    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--conn", type=int, default=4, dest='max_connections',
                        help="Max number of collections allowed (default 4)")
    parser.add_argument("-d", "--difficulty", type=int, default=20, dest='difficulty',
                        help="Difficulty of mining (default 20)")
    parser.add_argument("-l", "--length", type=int, default=15, dest='max_length_chain',
                        help="Length of chain before program stops (default 15)")
    args = parser.parse_args()

    list_conections = []
    # Initialize the blockchain
    blockChain = BlockChain(args.difficulty)

    signal.signal(signal.SIGINT, signal_handler)

    #Initialize the socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((host, port))
    print("Socket binded to port ", port)

    # Put the socket into listening mode
    s.listen(5)
    print("socket is listening")

    while True:
        try:
            if blockChain.length_chain() > args.max_length_chain:
                print_lock.acquire()
                print('Blockchain completed')
                blockChain.save_chain('./')
                print_lock.release()
                break
            # establish connection with client
            while len(list_conections) > args.max_connections:
                continue
            c, addr = s.accept()

            # Lock acquired for safe printing
            print_lock.acquire()
            print('Connected to :', addr[0], ':', addr[1])
            print_lock.release()

            data = c.recv(1024)
            if not data:
                print_lock.acquire()
                print('Disconnecting from :', addr[0], ':', addr[1])
                print_lock.release()
                c.close()
            elif data is not "ACK":
                print_lock.acquire()
                print('Failed to establish a proper connection to :', addr[0], ':', addr[1])
                print_lock.release()
                c.close()
            else:
                connection_list_lock.acquire()
                list_conections.append(c)
                connection_list_lock.release()
                # Start a new thread and return its identifier
                t = threading.Thread(target=threaded, args=(c, addr, blockChain, list_conections))
                t.daemon = True
                t.start()
        except (KeyboardInterrupt, socket.error) as e:
            print('Process ended')
            blockChain.save_chain('./')
            print(e)
            break
    s.close()


if __name__ == '__main__':
    Main()