# API client for Trading212

Based on "trading212-rest" at https://github.com/ms32035/trading212-rest
Based on the new REST API of [Trading212](https://www.trading212.com/).

## Installation

```bash
pip install trading212-rest
pip install T212
```
did not work for me, instead:
export PYTHONPATH=${PWD}

## Usage

```python
from T212 import T212

client = T212(token="your_api_token", demo=False)

orders = client.exch_df()
orders = client.pf_df()
orders = client.instr_df()

This is just a small selection of functions. Most endpoints are already implemented.

For a full documentation on Trading212 endpoint paramaters see https://t212public-api-docs.redoc.ly/
