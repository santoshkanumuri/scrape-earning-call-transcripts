import yfinance as yf
import pandas as pd

file1= pd.read_csv('./input/data.csv')
symbols = file1['Symbol'].tolist()

exchanges = []

for symbol in symbols:
    try:
        ticker = yf.Ticker(symbol)
        exchange = ticker.info.get("exchange")
        if exchange:
            exchanges.append((symbol, exchange))
        else:
            print(f"No exchange information found for {symbol}")
    except Exception as e:
        print(f"Error processing {symbol}: {e}")

print(exchanges)

# add the following code to the end of the script to write the exchange data to a CSV file:

df = pd.DataFrame(exchanges, columns=['Symbol', 'Exchange'])
df.to_csv('./output/exchanges.csv', index=False)
print("Exchange data saved to 'exchanges' CSV file.")
