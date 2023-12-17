import hashlib
import json
import time
from uuid import uuid5, NAMESPACE_DNS
from random import randint, choice
import os
import threading
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA256
import base64
import copy

run_fake_transactions = False
quit_thread = False
key = ""

class Transaction:
    def __init__(self, sender="", receiver="", data=""):
        self.id = str(uuid5(NAMESPACE_DNS, str(time.time()) + "".join(chr(randint(33,126)) for i in range(4))))
        self.sender = sender
        self.receiver = receiver
        self.data = data
        self.hash = self.get_hash()
        s = Sender(sender)
        self.sign_transaction(s.get_key())
    
    def load_from_string(self, string:str):
        data = json.loads(string)

        for key, value in data.items():
            if key == 'signature':
                value = base64.b64decode(value.encode('utf-8'))

            setattr(self, key, value)

    def verify_signature(self, public_key):
        message = f"{self.id}{self.sender}{self.receiver}{self.data}".encode('utf-8')
        h = SHA256.new(message)
        try:
            pkcs1_15.new(public_key).verify(h, self.signature)
            return True
        except (ValueError, TypeError):
            return False

    def sign_transaction(self, private_key):
        message = f"{self.id}{self.sender}{self.receiver}{self.data}".encode('utf-8')
        h = SHA256.new(message)
        self.signature = pkcs1_15.new(private_key).sign(h)

    def alter(self):
        self.data += ":)"
        print("transactions altered !")

    def has_valid_hash(self):
        return self.hash == self.get_hash()
    
    def has_valid_sig(self):
        return self.verify_signature(Sender(self.sender).get_public_key())

    def get_hash(self):
        return hashlib.sha256(f"{self.id}{self.sender}{self.receiver}{self.data}".encode('utf-8')).hexdigest()

    def get_pretty_str(self):
        return f"{self.id} : {self.sender} -> {self.receiver} ({self.data})"

    def __str__(self) -> str:
        ret = copy.deepcopy(self.__dict__)

        signature_str = base64.b64encode(self.signature).decode('utf-8')
        ret['signature'] = signature_str

        return json.dumps(ret)
    
class Sender:
    def __init__(self, name):
        self.name = name
        if os.path.exists(f"save/senders/{name}.key"):
            with open(f"save/senders/{name}.key", "rb") as file:
                self.key = RSA.import_key(file.read())
        else:
            print(f"Generating key pair for {name}...")
            self.key = RSA.generate(1024)
            self.save()
            print(f"Keys generated and saved !")

    def save(self):
        with open(f"save/senders/{self.name}.key", "w+") as file:
            file.write(self.key.export_key("PEM").decode("utf-8"))

    def get_key(self):
        return self.key
    
    def get_public_key(self):
        return self.key.public_key()

    def __str__(self) -> str:
        return f"{self.name}"

class Block:
    def __init__(self, previous_hash):
        self.id = 0
        self.previous_hash = previous_hash
        self.timestamp = time.time()
        self.transactions = []
        self.hash = "0"
        self.nonce = 0

    def add_transaction(self, transaction):
        self.transactions.append(transaction)
        self.hash = self.get_hash()
        if len(self.transactions) == 10:
            self.validate()
        self.save(self.id)

    def get_hash(self):
        str = f"{self.id}{self.previous_hash}{self.timestamp}{self.nonce}"
        for transaction in self.transactions: str += transaction.__str__()
        return hashlib.sha256(str.encode('utf-8')).hexdigest()

    def validate(self):
        while not self.hash.startswith("00"):
            self.nonce += 1
            self.hash = self.get_hash()

    def is_valid(self):
        return (self.hash.startswith("00") and self.hash == self.get_hash())

    def save(self, id):
        with open(f"./save/blocks/{id}.block", "w+") as file:
            file.write(self.__str__())

    def load_from_file(self, id):
        try:
            file = open(f"./save/blocks/{id}.block", "r")
        except:
            return False
        
        content = file.read().splitlines()
        file.close()

        self.id = content.pop(0)
        self.previous_hash = content.pop(0)
        self.timestamp = content.pop(0)
        self.hash = content.pop(0)
        self.nonce = int(content.pop(0))

        for transaction in content:
            new_transaction = Transaction()
            new_transaction.load_from_string(transaction)
            self.add_transaction(new_transaction)

        return True        

    def __str__(self) -> str:
        str = f"{self.id}\n{self.previous_hash}\n{self.timestamp}\n"
        str += f"{self.hash}\n{self.nonce}\n"
        for transaction in self.transactions:
            str += transaction.__str__() + "\n"
        return str

class Chain:
    def __init__(self):
        self.chain = []
        self.senders = []

    def add_block(self, bloc:Block):
        bloc.id = len(self.chain)
        try:
            bloc.previous_hash = self.chain[bloc.id - 1].hash
        except:
            bloc.previous_hash = "0"

        self.chain.append(bloc)

    def add_transaction(self, transaction):
        if len(self.chain[-1].transactions) < 10:
            self.chain[-1].add_transaction(transaction=transaction)
        else:
            self.add_block(Block(""))
            self.chain[-1].add_transaction(transaction=transaction)

    def load_blocks_from_folder(self):
        block = Block("")
        i = 0
        while block.load_from_file(i):
            chain.add_block(block)
            block = Block("")
            i+=1
        if i == 0: self.initiate()

    def check_transaction(self, id:str):
        for block in self.chain[::-1]:
            for transaction in block.transactions:
                if str(transaction.id) == id:
                    if transaction.has_valid_hash():
                        print("- Transaction hash is valid")
                    else:
                        print("- Transaction hash is not valid")
                    if transaction.has_valid_sig():
                        print("- Transaction signature is valid")
                    else:
                        print("- Transaction signature is not valid")
                    if block.is_valid():
                        print("- Block containing the transaction is valid (block number " + str(block.id) + ")")
                    else:
                        print("- Block containing the transaction is not valid ! (block number " + str(block.id) + ")")
                    return
        print("The ID you gave does not exist !")

    def get_last_transactions(self, number=10):
        array = []
        
        for block in self.chain[::-1]:
            for transaction in block.transactions[::-1]:
                if len(array) >= number:
                    return array
                array.append(transaction)
        return array

    def alter(self, id:str):
        for block in self.chain[::-1]:
            for transaction in block.transactions:
                if str(transaction.id) == id:
                    transaction.alter()
                    return
        print("The ID you gave does not exist !")

    def initiate(self):
        self.chain = [Block("0")]

    def __str__(self) -> str:
        str = ""
        for block in self.chain:
            str += block.__str__()
        return str

def worker(chain:Chain):
    personas = ["Alice", "Bob", "Toto", "Jean", "Jacques", "Baptiste", "Antoine", "Yves", "Juan", "Hugo", "Ben", "Angelo", "Manu", "Axel", "Anais", "Lea"]
    content = [" pizzas", " pieces", " bitcoins"]
    while True:
        if run_fake_transactions:
            s = choice(personas)
            chain.add_transaction(Transaction(sender=s, receiver=choice(personas), data=(str(randint(0, 10000)) + choice(content))))

            time.sleep(randint(0, 5))
        elif quit_thread:
            break

def menu():
    os.system('cls' if os.name == 'nt' else 'clear')
    
    print("""      __...--~~~~~-._   _.-~~~~~--...__
    //               `V'               \\\\ 
   //                 |                 \\\\ 
  //__...--~~~~~~-._  |  _.-~~~~~~--...__\\\\ 
 //__.....----~~~~._\\ | /_.~~~~----.....__\\\\
====================\\\\|//====================
                    `---`
               ==  Welcome == """)

if __name__ == "__main__":

    if not os.path.exists('save'):
        os.makedirs('save')
    
    if not os.path.exists('save/blocks'):
        os.makedirs('save/blocks')

    if not os.path.exists('save/senders'):
        os.makedirs('save/senders')

    chain = Chain();
    chain.load_blocks_from_folder()
    threading.Thread(target=worker, daemon=True ,args=[chain]).start()

    menu()

    command = ""

    while command.lower() not in ["quit", "q", "exit"]:
        command = input("> ")

        if command in "":
            pass

        elif command.lower() in ["help", "h", "?"]:
            print("- add\n\tAdd a new transaction (opens new menu)")
            print("- create_transactions\n\tCreate Random transaction each 5-10 seconds (generates trash output in the terminal)")
            print("- stop_transactions\n\tStops the creation of all transactions if activated")
            print("- check id_transaction\n\tCheck the transaction with id_transaction")
            print("- show [number]\n\tShows the list of [number] last transactions (10 by default)")
            print("- alter id_transaction\n\tAlter the transaction with id_transaction")
            print("- quit/exit\n\texits the program")

        elif command.lower() in ["cls", "clear"]: menu()

        elif command.lower() in ["add", "a"]:
            print("Adding a new transaction")
            sender = input("sender > ")
            receiver = input("receiver > ")
            content = input("content > ")

            chain.add_transaction(Transaction(sender=sender, receiver=receiver, data=content))

            print("Transaction added successfully !\n")
        
        elif command.lower() in ["create_transactions"]:
            run_fake_transactions = True
            print("Thread running...")

        elif command.lower() in ["stop_transactions"]:
            run_fake_transactions = False
            print("Thread stopped")
        
        elif command.lower().split()[0] in ["show"]:
            try:
                n = int(command.lower().split()[1])
            except:
                n = 10

            transactions = chain.get_last_transactions(n)

            for transaction in transactions:
                print(transaction.get_pretty_str())

            if len(transactions) < n:
                print("No more transactions....")

        elif command.lower().split()[0] in ["check"]:
            try:
                id = command.split()[1]
                chain.check_transaction(id)
            except:
                print("You should give a valid id")

        elif command.lower().split()[0] in ["alter"]:
            try:
                id = command.split()[1]
                chain.alter(id)
            except:
                print("You should give a valid id")

        elif command.lower() in ["quit", "q", "exit"]:
            run_fake_transactions = False
            quit_thread = True
            print("Good bye") 

        elif command.lower() in ["test"]:
            c = Sender("Jean")

        else:
            print("Unknown command '" + command + "'")

    run_fake_transactions = False
    quit_thread = True