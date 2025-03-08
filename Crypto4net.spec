# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_submodules

hiddenimports = ['aiohttp', 'asyncio', 'configparser', 'datetime', 'json', 'bip_utils', 'bip_utils.bip.bip39']
hiddenimports += collect_submodules('bip_utils')


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('E:\\Crypto4net\\.venv\\lib\\site-packages\\bip_utils\\bip\\bip39\\wordlist', 'bip_utils/bip/bip39/wordlist'), ('config_setups', 'config_setups')],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Crypto4net',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version='version_info.txt',
    icon=['C:\\Users\\Shafeik\\Downloads\\stock-vector-coins-with-symbols-of-cryptocurrencies-xrp-solana-sol-shiba-inu-shib-ethereum-eth-tether-2536382139.ico'],
)
