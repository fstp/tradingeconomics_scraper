# Scraping TradingEconomics WebSocket for Realtime Stock Data

## Overview

This project involves subscribing to real-time stock data over the TradingEconomics WebSocket. The data is received as encrypted JSON, which is decrypted using keys extracted from their obfuscated JavaScript. Additionally, the data is aggregated with VIX futures information from BNP Paribas and displayed using a `Rich` Live layout.

**Warning:**  
This implementation is a hack that relies on hardcoded browser cookies and decryption keys. It is fragile and may break at any time due to changes on the TradingEconomics platform.

## Disclaimer

This project is intended for educational purposes only. Use at your own risk, and ensure compliance with all applicable laws and terms of service.
