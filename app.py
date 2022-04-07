import csv
import glob, os
from operator import truediv
from terminaltables import SingleTable
import argparse
from datetime import datetime
from dateutil import parser

config = {
    "symbols": [ "TQQQ" ],
    "start_date" : "04/05/2022 00:00:00",
    "date_format": "%m/%d/%Y %H:%M:%S"
}

p = argparse.ArgumentParser("Trading App")
p.add_argument("--date", help="Date to be analyzed.")
args = p.parse_args()

single_date = None
if args.date is not None:
    single_date = datetime.strptime(args.date, '%m/%d/%Y')

start_date = datetime.strptime(config['start_date'], config['date_format'])

positions = {}
trades = []
total_profit = 0

def parse_row(row):
    return {
        "name": row[0],
        "symbol": row[1],
        "side": row[2],
        "status": row[3],
        "filled": row[4],
        "qty": row[5],
        "price": row[6],
        "avg_price": row[7],
        "time_in_force": row[8],
        "placed_time": row[9],
        "filled_time": row[10]
    }

def load_transactions():
    # Open CSV file of transactions
    os.chdir("./")
    transactions = []
    for filename in glob.glob("*.csv"):
        print(filename)
        with open(filename, newline='') as csvfile:
            reader = csv.reader(csvfile, delimiter=',', quotechar='"')
            for row in reader:
                transaction = parse_row(row)
                if transaction['status'] == 'Filled':
                    ts = transaction['filled_time'][:-4]
                    filled_time = datetime.strptime(ts, config['date_format'])
                    if start_date.date() <= filled_time.date() and (single_date is None or filled_time.date() == single_date.date()):
                        transactions.append(transaction)

    transactions.reverse()
    return transactions

def print_transaction(transaction):
    print(f"{transaction['side']} {transaction['qty']} {transaction['symbol']} @ {transaction['avg_price']}")

def is_position_closed(position):
    total = 0
    for transaction in position:
        qty = float(transaction['qty'])
        if transaction['side'] == 'Buy':
            total += qty
        else:
            total -= qty
    
    return total == 0

def num_format(num):
    return '{0:.2f}'.format(num)

def calculate_profitloss(transactions):
    global total_profit
    is_short = False
    if transactions[0]['side'] == 'Sell':
        is_short = True

    profit = 0
    open_capital = 0
    shares_open = 0
    avg_open = 0

    close_capital = 0
    shares_closed = 0
    avg_close = 0

    # Calculate full trade data
    for tran in transactions:
        qty = float(tran['qty'])
        price = float(tran['avg_price'])
        tran_value = qty * price
        if tran['side'] == 'Buy':
            profit -= tran_value
            open_capital += tran_value
            shares_open += qty
            avg_open = open_capital / shares_open
        else:
            profit += tran_value
            close_capital += tran_value
            shares_closed += qty
            avg_close = close_capital / shares_closed

    open = transactions[0]
    table_data.append([ open['filled_time'], "Short" if is_short else "Long", num_format(shares_open), num_format(avg_open), num_format(avg_close), num_format(profit)])
    total_profit += profit
    return profit

def update_positions(transaction):
    symbol = transaction['symbol']
    if symbol in positions:
        positions[symbol].append(transaction)
    else:
        positions[symbol] = [ transaction ]

    if is_position_closed(positions[symbol]):
        calculate_profitloss(positions[symbol])
        del positions[symbol]

table_data = [
    ['Date', 'Side', 'Shares', 'Entry Price', 'Exit Price', 'Profit/Loss']
]

transactions = load_transactions()

for tracked in config['symbols']:
    for transaction in transactions:
        if transaction['symbol'] == tracked:
            if transaction['status'] == 'Filled':
                update_positions(transaction)

t = SingleTable(table_data)
print(t.table)
print(f"TOTAL PROFIT/LOSS: ${num_format(total_profit)}")