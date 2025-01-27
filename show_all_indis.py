import pandas_ta as ta
import inspect
import os

def get_pandas_ta_indicators():
    # get all functions from the module
    functions = inspect.getmembers(ta, inspect.isfunction)

    return [name for name, _ in functions if not name.startswith('_')]


def write_indicators_to_file(file_path):
    # get all indicators
    pandas_ta_indicators = get_pandas_ta_indicators()

    # write indicators to the file
    with open(file_path, 'w') as file:
        file.write('Pandas TA indicators:\n')
        file.write('=======================')
        for indicator in pandas_ta_indicators:
            file.write(f'{indicator}\n')


if __name__ == "__main__":
    #speicfy the file path
    data_folder = 'src/btc_1h.csv'

    #create the file path
    file_path = os.path.join(data_folder, 'available_indicators.txt')

    #write indicators to the file
    write_indicators_to_file(file_path)

    print(f'Indicators written to: {file_path}')