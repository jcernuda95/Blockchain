# import socket programming library
import socket
from Transcation import BlockChain
import signal
import sys
import threading
import pickle
import argparse
from struct import pack, unpack

print_lock = threading.Lock()
blockchain_lock = threading.Lock()
connection_list_lock = threading.Lock()
brutal_lock = threading.Lock()

blockChain = 10
max_index = 0

# TODO: How to stop mining from happening. Event on mine happen to all other thread. Non blocking recv
# TODO: Add logic to delete conections lost and allow more miners to enter.


def signal_handler(sig, frame):
    print('Closing server')
    sys.exit(0)


# thread fuction
def threaded(conn, addr, max_length_chain):
    global blockChain
    global max_index
    while True:
        print_lock.acquire()
        print("Blockchain length:" + str(blockChain.length_chain()))
        print_lock.release()

        # Once connection is establish, send the full blockchain to the client
        blockchain_lock.acquire()
        data = pickle.dumps(blockChain)
        length_chain = pack('>Q', len(data))
        conn.sendall(length_chain)
        conn.sendall(data)
        blockchain_lock.release()

        print_lock.acquire()
        print("Blockchain sended")
        print_lock.release()

        # The client starts to mine, wait until it finishes
        msg = conn.recv(8)
        (length,) = unpack('>Q', msg)

        print_lock.acquire()
        print(len(msg))
        print(length)
        print_lock.release()

        data = b''
        while len(data) < length:
            print_lock.acquire()
            print_lock.release()
            # doing it in batches is generally better than trying
            # to do it all in one go, so I believe.
            to_read = length - len(data)
            data += conn.recv(
                4096 if to_read > 4096 else to_read)
        print_lock.acquire()
        print("Block received")
        if not data:
            print("Error on Block")
        print_lock.release()
        block = pickle.loads(data)
        print_lock.acquire()
        print_lock.release()


        # Attempt to add block given to the chain
        blockchain_lock.acquire()
        if blockChain.check_block(block) and block.index > max_index:
            blockChain.add_block(block)
            max_index = block.index
            conn.send("OK".encode())
            print_lock.acquire()
            print("Block added")
            print_lock.release()
        else:
            conn.send("ER".encode())
            print_lock.acquire()
            print("Block lost")
            print_lock.release()

        print("length " + str(blockChain.length_chain()))
        if blockChain.length_chain() > max_length_chain:
            print_lock.acquire()
            print('Blockchain completed')
            blockChain.save_chain()
            print_lock.release()
            # Close clients
            fin = pack('>Q', 0)
            conn.sendall(fin)
            blockchain_lock.release()
            break
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

    # Parse program arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--conn", type=int, default=4, dest='max_connections',
                        help="Max number of collections allowed (default 4)")
    parser.add_argument("-d", "--difficulty", type=int, default=20, dest='difficulty',
                        help="Difficulty of mining (default 20)")
    parser.add_argument("-l", "--length", type=int, default=15, dest='max_length_chain',
                        help="Length of chain before program stops (default 15)")
    args = parser.parse_args()

    list_conections = []

    signal.signal(signal.SIGINT, signal_handler)

    #Initialize the socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((host, port))
    print("Socket binded to port ", port)

    # Initialize the blockchain
    global blockChain
    blockChain = BlockChain(args.difficulty)

    # Put the socket into listening mode
    s.listen(5)
    print("socket is listening")

    while True:
        try:
            blockchain_lock.acquire()
            print_lock.acquire()
            if blockChain.length_chain() > args.max_length_chain:
                print_lock.acquire()
                print('Blockchain completed. Press ctr+c to exit')
                blockChain.save_chain()
                print_lock.release()
                blockchain_lock.acquire()
                break
            blockchain_lock.release()
            print_lock.release()
            # establish connection with client
            while len(list_conections) > args.max_connections:
                print_lock.acquire()
                print('No more connections allowed')
                print_lock.release()
                continue
            c, addr = s.accept()

            # Lock acquired for safe printing
            print_lock.acquire()
            print('Connected to :', addr[0], ':', addr[1])
            print_lock.release()

            data = c.recv(3).decode()
            if not data:
                print_lock.acquire()
                print('Disconnecting from :', addr[0], ':', addr[1])
                print_lock.release()
                c.close()
            if data[:3] == 'ACK':
                connection_list_lock.acquire()
                list_conections.append(c)
                connection_list_lock.release()
                # Start a new thread and return its identifier
                t = threading.Thread(target=threaded, args=(c, addr, args.max_length_chain))
                t.daemon = True
                t.start()
            else:
                print_lock.acquire()
                print('Failed to establish a proper connection to :', addr[0], ':', addr[1])
                print_lock.release()
                c.close()
        except (KeyboardInterrupt, socket.error) as e:
            print('Process ended')
            blockChain.save_chain()
            print(e)
            break
    s.close()
    blockChain.save_chain()
    sys.exit(0)


if __name__ == '__main__':
    Main()