# C5-REAL EXERGY CERTIFIED
from setuptools import setup, Extension

module1 = Extension('cortex_guard_core',
                    sources = ['cortex_guard_core.c'])

setup (name = 'cortex_guard_core',
       version = '1.0',
       description = 'ULTRATHINK Zero-Tolerance Dependency Vanguard (Native C)',
       ext_modules = [module1])
