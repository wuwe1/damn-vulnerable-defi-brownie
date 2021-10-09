from brownie import (
    accounts,
    DamnValuableTokenSnapshot,
    SelfiePool,
    SimpleGovernance,
)
from brownie.network.account import Account


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

    # SUCCESS CONDITIONS
    assert token.balanceOf(attacker.address) == TOKENS_IN_POOL
    assert token.balanceOf(pool.address) == 0
