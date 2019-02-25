import threading

blockChain = 10


def threaded():
    global BlockChain
    print("Thread1:" + BlockChain)
    BlockChain = "Bye"
    print("Thread2:" + BlockChain)


def Main():
    global BlockChain
    blockChain = "Hello"
    while True:
        try:
            print("Main:" + BlockChain)
            t = threading.Thread(target=threaded, args=())
            t.daemon = True
            t.start()
        except (KeyboardInterrupt, socket.error) as e:
            print('Process ended')
            print(e)
            break
