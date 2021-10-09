from brownie import accounts, DamnValuableToken, TrusterLenderPool
from brownie.network.account import Account


def test_truster():
    deployer: Account = accounts[0]
    attacker: Account = accounts[1]
    TOKENS_IN_POOL = 1000000e18

    token = DamnValuableToken.deploy({"from": deployer})
    pool = TrusterLenderPool.deploy(token.address, {"from": deployer})
    token.transfer(pool.address, TOKENS_IN_POOL, {"from": deployer})
    assert token.balanceOf(pool.address) == TOKENS_IN_POOL
    assert token.balanceOf(attacker.address) == 0
    # YOUR EXPLOIT GOES HERE

    # SUCCESS CONDITIONS
    assert token.balanceOf(attacker.address) == TOKENS_IN_POOL
    assert token.balanceOf(pool.address) == 0
