"""
token bean
"""
import json
import eth_abi
from web3 import Web3, HTTPProvider

from enum import Enum
from typing import Dict


class SupportedChainId(Enum):
    OPTIMISM = 10
    OPTIMISTIC_KOVAN = 69
    ARBITRUM_ONE = 42161
    ARBITRUM_RINKEBY = 421611
    POLYGON_MUMBAI = 80001
    POLYGON = 137
    BSC = 56


class AddressMap(Dict[SupportedChainId, str]):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


def constructSameAddressMap(address: str, chains: list):
    addressMap = AddressMap()
    for chain in chains:
        addressMap[chain] = address
    return addressMap


V3_FACTORY_ADDRESS = "0x1F98431c8aD98523631AE4a59f267346ea31F984".lower()
V3_CORE_FACTORY_ADDRESSES = constructSameAddressMap(
    V3_FACTORY_ADDRESS,
    [
        SupportedChainId.OPTIMISM,
        SupportedChainId.OPTIMISTIC_KOVAN,
        SupportedChainId.ARBITRUM_ONE,
        SupportedChainId.ARBITRUM_RINKEBY,
        SupportedChainId.POLYGON_MUMBAI,
        SupportedChainId.POLYGON,
    ],
)
V3_CORE_FACTORY_ADDRESSES[SupportedChainId.BSC] = '0x0bfbcf9fa4f9c56b0f40a671ad40e0805a091865'.lower()


class RpcUrls(Dict[SupportedChainId, str]):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


RPC_URL_MAP = RpcUrls({
    SupportedChainId.OPTIMISM: '',
    SupportedChainId.BSC: ''
})


class AbiFileMap(Dict[SupportedChainId, str]):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


def constructSameAbiFileMap(file_name: str, chains: list):
    abiFileMap = AbiFileMap()
    for chain in chains:
        abiFileMap[chain] = file_name
    return abiFileMap


V3_POOL_ABI_FILES = constructSameAbiFileMap(
    'pool.abi.json',
    [
        SupportedChainId.OPTIMISM,
        SupportedChainId.OPTIMISTIC_KOVAN,
        SupportedChainId.ARBITRUM_ONE,
        SupportedChainId.ARBITRUM_RINKEBY,
        SupportedChainId.POLYGON_MUMBAI,
        SupportedChainId.POLYGON,
    ],
)
V3_POOL_ABI_FILES[SupportedChainId.BSC] = 'bsc.pool.abi.json'

POOL_INIT_CODE_HASH: str = '0xe34f199b19b2b4f47f68442619d555527d244f78a3297ea89325f843f87b8b54'
V3_POOL_INIT_CODE_HASH = constructSameAddressMap(
    POOL_INIT_CODE_HASH,
    [
        SupportedChainId.OPTIMISM,
        SupportedChainId.OPTIMISTIC_KOVAN,
        SupportedChainId.ARBITRUM_ONE,
        SupportedChainId.ARBITRUM_RINKEBY,
        SupportedChainId.POLYGON_MUMBAI,
        SupportedChainId.POLYGON,
    ],
)
ADDRESS_ZERO: str = '0x0000000000000000000000000000000000000000'


class Token:
    _decimal: int = 18
    _address: str
    _symbol: str

    def __init__(self, address: str, decimal: int = 18, symbol: str = None):
        self._decimal = decimal
        self._address = address
        self._symbol = symbol

    @property
    def decimal(self):
        return self._decimal

    @property
    def address(self):
        return self._address

    @property
    def symbol(self):
        return self._symbol


# 手续费枚举
class FeeAmount(Enum):
    LOWEST = 100
    LOW = 500
    MEDIUM = 3000
    HIGH = 10000


def compute_uniswap_v3_pool_address(token0: Token, token1: Token, fee: FeeAmount,
                                    chainId: SupportedChainId):
    if chainId == SupportedChainId.BSC:
        return get_pool_address(token0, token1, fee,chainId)
    factory_address = V3_CORE_FACTORY_ADDRESSES[chainId]
    abi_encoded_1 = eth_abi.encode(['address', 'address', 'uint24'],
                                   [Web3.to_checksum_address(token0.address.lower()),
                                    Web3.to_checksum_address(token1.address.lower()),
                                    fee.value])
    pool_init_code_hase = V3_POOL_INIT_CODE_HASH[chainId]
    # print(abi_encoded_1.hex())
    # keccak256(abi.encode(key.token0, key.token1, key.fee)),
    slat = Web3.solidity_keccak(['bytes'], ['0x' + abi_encoded_1.hex()])
    encodePacked = Web3.solidity_keccak(['bytes', 'address', 'bytes', 'bytes'],
                                        ['0xff', Web3.to_checksum_address(factory_address), slat, pool_init_code_hase])[
                   12:]
    return encodePacked.hex()


def get_pool_address(token0: Token, token1: Token, fee: FeeAmount, chainId: SupportedChainId):
    rpc_url = RPC_URL_MAP[chainId]
    web3_provider = Web3(HTTPProvider(rpc_url))
    factory_address = V3_CORE_FACTORY_ADDRESSES[chainId]
    f = open('facory.abi.json')
    factory_json = json.load(f)
    factory_contract = web3_provider.eth.contract(address=Web3.to_checksum_address(factory_address), abi=factory_json)
    return factory_contract.functions.getPool(Web3.to_checksum_address(token0.address.lower()),
                                              Web3.to_checksum_address(token1.address.lower()), fee.value).call()


def get_pool_slot0(pool_address: str, chainId: SupportedChainId):
    rpc_url = RPC_URL_MAP[chainId]
    web3_provider = Web3(HTTPProvider(rpc_url))
    fpath = V3_POOL_ABI_FILES[chainId]
    f = open(fpath)
    pool_address_json = json.load(f)
    pool_contract = web3_provider.eth.contract(address=Web3.to_checksum_address(pool_address.lower()),
                                               abi=pool_address_json)
    slot0 = pool_contract.functions.slot0().call();
    return slot0


# token address排序
def sorts_token_address_before(token0_address: str, token1_address: str):
    return (token0_address, token1_address) if int(token0_address, 16) < int(token1_address,
                                                                             16) else (token1_address, token0_address)


if __name__ == '__main__':
    (token0_address, token1_address) = sorts_token_address_before('0x9d34f1d15c22e4c0924804e2a38cbe93dfb84bc2',
                                                                  '0xc84da6c8ec7a57cd10b939e79eaf9d2d17834e04');
    token0 = Token(token0_address)
    token1 = Token(token1_address)
    pool_address = compute_uniswap_v3_pool_address(token0, token1, FeeAmount.MEDIUM, SupportedChainId.OPTIMISM)
    # pool_address = get_pool_address(token0, token1, FeeAmount.MEDIUM)
    print(pool_address)
    slot0 = get_pool_slot0(pool_address, chainId=SupportedChainId.OPTIMISM)
    sqrtPriceX96 = slot0[0]
    d = abs(10 ** (token0.decimal - token1.decimal))
    price = (sqrtPriceX96 ** 2 / 2 ** 192) * d
    print(price)
