import threading

BlockChain = 10


def threaded():
    global BlockChain
    print("Thread1:" + BlockChain)
    BlockChain = "Bye"
    print("Thread2:" + BlockChain)


def Main():
    global BlockChain
    BlockChain = "Hello"
    while True:
        try:
            print("Main:" + BlockChain)
            t = threading.Thread(target=threaded, args=())
            t.daemon = True
            t.start()
        except KeyboardInterrupt as e:
            print('Process ended')
            print(e)
            break
