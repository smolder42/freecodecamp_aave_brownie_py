from scripts.helpful_scripts import get_account
from scripts.get_weth import get_weth
from brownie import config, network, interface
from web3 import Web3

amount = Web3.toWei(0.1, "ether")


def main():
    account = get_account()
    if network.show_active() in ["mainnet-fork"]:
        get_weth()
    lending_pool = get_lending_pool()
    approve_erc20(lending_pool, amount, account)

    print("Depositing 0.1 WETH...")
    tx = lending_pool.deposit(
        config["networks"][network.show_active()]["weth_token"],
        amount,
        account.address,
        0,
        {"from": account},
    )
    tx.wait(1)
    print("Deposited 0.1 WETH!")

    borrowable_eth, total_debt = get_user_account_data(lending_pool, account.address)

    dai_eth_price = interface.AggregatorV3Interface(
        config["networks"][network.show_active()]["dai_eth_price"]
    )
    latest_dai_eth_price = dai_eth_price.latestRoundData()[1]
    latest_dai_eth_price = Web3.fromWei(latest_dai_eth_price, "ether")
    print(f"DAI price is {latest_dai_eth_price}")

    dai_amount = 1 / float(latest_dai_eth_price) * (borrowable_eth * 0.95)
    print("Borrowing...")
    borrow_tx = lending_pool.borrow(
        config["networks"][network.show_active()]["dai_token"],
        Web3.toWei(dai_amount, "ether"),
        1,
        0,
        account.address,
        {"from": account},
    )
    borrow_tx.wait(1)
    print(f"You have borrowed {dai_amount} DAI!")
    get_user_account_data(lending_pool, account)

    # repay_all(lending_pool, account, dai_amount)


def repay_all(lending_pool, account, dai_amount):
    erc20 = interface.IERC20(config["networks"][network.show_active()]["dai_token"])
    erc20.approve(lending_pool, dai_amount, {"from": account})
    print("Repaying...")
    repay_tx = lending_pool.repay(
        config["networks"][network.show_active()]["dai_token"],
        Web3.toWei(dai_amount, "ether"),
        1,
        account.address,
        {"from": account},
    )
    repay_tx.wait(1)
    print("Repaid!")
    pass


def get_user_account_data(lending_pool, account):
    (
        total_collateral_eth,
        total_debt_eth,
        available_borrow_eth,
        current_liquidation_threshold,
        ltv,
        healthFactor,
    ) = lending_pool.getUserAccountData(account)
    total_collateral_eth = Web3.fromWei(total_collateral_eth, "ether")
    total_debt_eth = Web3.fromWei(total_debt_eth, "ether")
    available_borrow_eth = Web3.fromWei(available_borrow_eth, "ether")
    print(f"You deposited {total_collateral_eth} worth of ETH.")
    print(f"You have borrowed {total_debt_eth} worth of ETH.")
    print(f"You can borrow {available_borrow_eth} worth of ETH.")
    return (float(available_borrow_eth), float(total_debt_eth))


def approve_erc20(spender, amount, account):
    print("Approving...")
    erc20 = interface.IERC20(config["networks"][network.show_active()]["weth_token"])
    erc20.approve(spender, amount, {"from": account})
    print("Approved!")


def get_lending_pool():
    lending_pool_addresses_provider = interface.ILendingPoolAddressesProvider(
        config["networks"][network.show_active()]["lending_pool_addresses_provider"]
    )
    lending_pool_address = lending_pool_addresses_provider.getLendingPool()
    lending_pool = interface.ILendingPool(lending_pool_address)
    return lending_pool
