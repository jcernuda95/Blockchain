import time
import hashlib
import json
import random
import string


class Block:
    def __init__(self, index, data, previous_hash, difficulty):
        self.index = index
        self.timestamp = time.time()
        self.data = data
        self.previous_hash = previous_hash
        self.difficulty = difficulty
        self.nonce = 0
        self.hash= self.mine()

    def calculate_hash(self):
        return hashlib.sha224((str(self.index) + str(self.timestamp) +
                                          str(self.data) + str(self.previous_hash) +
                                          str(self.difficulty) + str(self.nonce)).encode('utf-8')).hexdigest()

    def mine(self):
        self.nonce = hashlib.sha512(''.join(random.choices(string.ascii_uppercase + string.digits, k=20)).encode('utf-8')).hexdigest()
        while True:
            attempt_hash = self.calculate_hash()
            if int(attempt_hash, 16) < pow(2, 256-self.difficulty):
                # Successful mine
                return attempt_hash
            else:
                self.nonce = hashlib.sha512(''.join(random.choices(string.ascii_uppercase + string.digits, k=20))).hexdigest()


class BlockChain:
    def __init__(self, difficulty):
        self.difficulty = difficulty  # static, defined at startup
        self.chain = self.initialize_chain()

    def initialize_chain(self):
        # Read chain from disk, create genesis block(server), request chain (client)
        # For now, lets create genesis block, maybe read in the future,
        # the server on start can read file from disk,
        # but more useful client can read chain from disk and request from server only the new blocks.
        # we might have to do shenanigans with factories
        # (https://stackoverflow.com/questions/43965376/initialize-object-from-the-pickle-in-the-init-function)
        return [Block(0, "GenesisBlock", None, self.difficulty)]

    def save_chain(self, path='./blockchain.info'):
        info = {
            "difficulty": self.difficulty,
            "chain": [ob.__dict__ for ob in self.chain],
        }
        # opening with "a" allows to append, something to consider if the chain gets to long.
        with open(path, "w") as file:
            json.dump(info, file)
        return 0

    def add_block(self, block):
        # useful for the server on block received
        if self.check_block(block) is True:
            print("Adding block")
            self.chain.append(block)
            return True
        else:
            return False

    def new_block(self, data):
        # Useful for the client. Creates, mines and adds the block, returns the block to be sent to the server
        previous_block = self.lookup_block_by_index(-1)
        new_block = Block(previous_block.index + 1, data, previous_block.hash, self.difficulty)
        if self.add_block(new_block):
            return new_block
        else:
            return False

    # def lookup_previous_block(self, block):
        # useful to loop over the chain. Maybe? using previous hash,
    # maybe its no use since we have index for now, if ever change to linked list would be a necessity

    def lookup_block_by_index(self, index):
        # index -1 will return last block
        return self.chain[index]

    def check_block(self, block):
        previous_block = self.lookup_block_by_index(block.index - 1)
        print("Hash (=): " + block.hash[-3:] + " " + block.calculate_hash()[-3:])
        print("Previous Hash (=): " + block.previous_hash[-3:] + " " + previous_block.hash[-3:])
        print("Index (>): " + str(block.index) + " " + str(previous_block.index))
        print("timestamp (>): " + str(block.timestamp) + " " + str(previous_block.timestamp))

        if (isinstance(block, Block) and previous_block.timestamp < block.timestamp and
                block.index - previous_block.index == 1 and block.previous_hash == previous_block.hash and
                block.hash == block.calculate_hash()):
            return True
        else:
            return False
        # if isinstance(block, Block):
        #     if previous_block.timestamp < block.timestamp:
        #         if block.index - previous_block.index == 1:
        #             if block.previous_hash == previous_block.hash:
        #                 if block.hash == block.calculate_hash():
        #                     return True
        #                 else:
        #                     print("Hash of block is wrong " + str(block.hash[-3:]) + + " " + str(block.calculate_hash()[-3:]))
        #                     return False
        #             else:
        #                 print("Hash of previous block doesnt match" + str(block.previous_hash[-3:]) + + " " + str(previous_block.hash[-3:]))
        #                 return False
        #         else:
        #             print("error on Block index" + str(block.index) + + " " + str(previous_block.index))
        #             return False
        #     else:
        #         print("error on timestamp" + str(previous_block.timestamp) + + " " + str(block.timestamp))
        #         return False
        # else:
        #     print("error block is not a block")
        #     return False

    def check_chain(self, start=0, end=None):
        if end is None: end = len(self.chain)
        for block in self.chain[start:end]:
            if self.check_block(block) == -1:
                return False
        return True

    def remove_last_block(self):
        del self.chain[-1]

    def length_chain(self):
        return len(self.chain)



