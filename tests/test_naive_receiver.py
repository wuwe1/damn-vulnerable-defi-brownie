from brownie import NaiveReceiverLenderPool, FlashLoanReceiver, accounts
from brownie.network.account import Account
from brownie.network.contract import ProjectContract
from web3 import Web3

ETHER_IN_POOL = Web3.toWei(1000, "ether")
ETHER_IN_RECEIVER = Web3.toWei(10, "ether")


def test_naive_receiver():
    deployer: Account = accounts[0]
    user: Account = accounts[1]
    attacker: Account = accounts[2]
    pool: ProjectContract = NaiveReceiverLenderPool.deploy({"from": deployer})
    deployer.transfer(pool.address, ETHER_IN_POOL)
    assert pool.balance() == ETHER_IN_POOL
    assert pool.fixedFee() == Web3.toWei(1, "ether")
    receiver: ProjectContract = FlashLoanReceiver.deploy(pool.address, {"from": user})
    user.transfer(receiver.address, ETHER_IN_RECEIVER)
    assert receiver.balance() == ETHER_IN_RECEIVER

    # YOUR EXPLOIT GOES HERE

    # SUCCESS CONDITIONS
    assert receiver.balance() == 0
    assert pool.balance() == ETHER_IN_POOL + ETHER_IN_RECEIVER
