from brownie import (
    accounts,
    FlashLoanerPool,
    TheRewarderPool,
    DamnValuableToken,
    RewardToken,
    AccountingToken,
)
from brownie.network.contract import Contract
from brownie.network.state import Chain


def test_the_rewarder():
    deployer = accounts[0]
    alice = accounts[1]
    bob = accounts[2]
    charlie = accounts[3]
    david = accounts[4]
    attacker = accounts[5]
    users = [alice, bob, charlie, david]

    TOKENS_IN_LENDER_POOL = 1000000e18
    liquidity_token = DamnValuableToken.deploy({"from": deployer})
    flashloan_pool = FlashLoanerPool.deploy(liquidity_token.address, {"from": deployer})
    liquidity_token.transfer(
        flashloan_pool.address, TOKENS_IN_LENDER_POOL, {"from": deployer}
    )
    rewarder_pool = TheRewarderPool.deploy(liquidity_token.address, {"from": deployer})
    reward_token = Contract.from_abi(
        "RewardToken", rewarder_pool.rewardToken(), RewardToken.abi
    )
    accounting_token = Contract.from_abi(
        "AccountingToken", rewarder_pool.accToken(), AccountingToken.abi
    )

    for user in users:
        amount = 100e18
        liquidity_token.transfer(user.address, amount, {"from": deployer})
        liquidity_token.approve(rewarder_pool.address, amount, {"from": user})
        rewarder_pool.deposit(amount, {"from": user})
        assert accounting_token.balanceOf(user.address) == amount

    assert accounting_token.totalSupply() == 400e18
    assert reward_token.totalSupply() == 0
    Chain().sleep(5 * 24 * 60 * 60)

    for user in users:
        rewarder_pool.distributeRewards({"from": user})
        assert reward_token.balanceOf(user) == 25e18
    assert reward_token.totalSupply() == 100e18
    assert rewarder_pool.roundNumber() == 2

    # YOUR EXPLOIT GOES HERE

    # Only one round should have taken place
    assert rewarder_pool.roundNumber() == 3
    for user in users:
        rewarder_pool.distributeRewards({"from": user})
        assert reward_token.balanceOf(user) == 25e18

    # Rewards must have been issued to the attacker account
    assert reward_token.totalSupply() > 100e18
    assert reward_token.balanceOf(attacker.address) > 0
