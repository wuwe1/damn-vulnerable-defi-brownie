from brownie import (
    accounts,
    Exchange,
    DamnValuableNFT,
    TrustfulOracle,
    TrustfulOracleInitializer,
)
from brownie.network.account import Account
from brownie.network.contract import Contract


def test_compromised():
    sources = [
        "0xA73209FB1a42495120166736362A1DfA9F95A105",
        "0xe92401A4d3af5E446d93D11EEc806b1462b39D15",
        "0x81A5D6E50C214044bE44cA0CB057fe119097850c",
    ]
    deployer: Account = accounts[0]
    attacker: Account = accounts[1]
    EXCHANGE_INITIAL_ETH_BALANCE = 10000e18
    INITIAL_NFT_PRICE = 999e18
    deployer.transfer(sources[0], 5e18).wait(1)
    deployer.transfer(sources[1], 5e18).wait(1)
    deployer.transfer(sources[2], 5e18).wait(1)

    oracleInitializer = TrustfulOracleInitializer.deploy(
        sources,
        ["DVNFT", "DVNFT", "DVNFT"],
        [INITIAL_NFT_PRICE, INITIAL_NFT_PRICE, INITIAL_NFT_PRICE],
        {"from": deployer},
    )
    oracle = Contract.from_abi(
        "TrustfulOracle", oracleInitializer.oracle(), TrustfulOracle.abi
    )
    exchange = Exchange.deploy(
        oracle.address, {"from": deployer, "amount": EXCHANGE_INITIAL_ETH_BALANCE}
    )
    assert exchange.balance() == EXCHANGE_INITIAL_ETH_BALANCE
    token = Contract.from_abi("DamnValuableNFT", exchange.token(), DamnValuableNFT.abi)

    # YOUR EXPLOIT GOES HERE

    # Exchange must have lost all ETH
    assert exchange.balance() == 0
    assert attacker.balance() > EXCHANGE_INITIAL_ETH_BALANCE
