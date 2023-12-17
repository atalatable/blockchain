# Usage guide

## Global explaination

To run, juste run `./buil_run_docker.sh name`, with any name you want (name of the docker image)

## Available commands

```
- add
    Add a new transaction (opens new menu)
- create_transactions
    Create Random transaction each 0-5 seconds
    /* The transactions are all signed with the same key */
- stop_transactions
    Stops the creation of all transactions if activated
- check id_transaction
    Check the transaction with id_transaction
- show [number]
    Shows the list of [number] last transactions (10 by default)
- alter id_transaction
    Alter the transaction with id_transaction
- help
    displays an help menu
- clear/cls
    clears the console
- quit/exit
    exits the program
```

## Design

### Transaction

| Attributes | explaination |
|-----------|-------------|
| id | Id of the transaction, based on time and randomness |
| sender  | Sender of the transaction (string) |
| receiver | Receiver of the transaction (string) |
| data | Content of the transaction (string) |
| hash | Hash of the transaction, based on all previous elements |
| signature | Signature of the transation |

| Methods | explaination |
|-----------|-------------|
| __init__() | Creates the transaction with a random id and calculates the hash |
| load_from_string(string) | Load each attribute of a Transaction from a string |
| verify_signature(public_key) | Verify if the signature of the transaction corresponds to the given public key |
| sign_transaction(private_key) | Set self.signature according to given private_key  |
| alter () | Alters the content of a transaction |
| has_valid_hash() | Checks the hash of the transaction |
| has_valid_sig() | Checks the signature of the transaction|
| get_hash() | Returns the hash of the Transaction |

### Sender

| Attributes | explaination |
|-----------|-------------|
| name | name of the sender |
| key | private key associated to the name |

| Methods | explaination |
|-----------|-------------|
| __init__() | If key is already saved, load key from file, else creates one and saves it |
| save() | save the private key in a file under `./save/sender/{sender}.ke` |
| verify_signature(transaction) | Verify the signature of the given transaction (sender must be curretn sender) |
| get_key() | returns private key |

### Block

| Attributes | explaination |
|-----------|-------------|
| id | Id of the block (increments with each block and starts at 0) |
| previous hash | Hash of the previous block ("0" for first) |
| timestamp | Time of the creation of the block (first transaction added into it) |
| transactions | List of ten Transactions |
| hash | Hash of the block includin all elements |
| nonce | Element to vary for the proof of work |

| Methods | explaination |
|-----------|-------------|
| __init__() | Create a new block with current timestamp |
| add_transaction(string) | Add a Transaction to the transactions list |
| get_hash() | Returns the hash of the block |
| validate() | Finds the proof of work |
| is_valid() | Check the block integrity and if the hash starts with "00" |
| save(id) | Saves the block in a file `./save/blocks/{id}.block` |
| load_from_file(id) | Load a block from a file `./save/blocks/{id}.block` |

### Chain

| Attributes | explaination |
|-----------|-------------|
| chain | List of Blocks |
| senders | List of all Senders that have already sent in the chain |

| Methods | explaination |
|-----------|-------------|
| __init__() | Create the chain with empty arrays |
| add_block(block) | Add a block the chain |
| add_transaction(transaction) | Add a transaction to the last (not full) block |
| load_blocks_from_folder() | Load the blocks from the folder `./save/blocks` |
| check_transaction(id) | Checks the transaction with given id   |
| get_last_transactions(n) | returns last n transactions |
| alter(id) | Alters the transaction with given id |
| initiate() | Add the genesis block in the chain |