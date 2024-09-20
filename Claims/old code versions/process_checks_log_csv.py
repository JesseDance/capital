import csv
from decimal import Decimal

def main(row_list):

	file = open('test-log-output.csv', 'w', newline='')
	writer = csv.writer(file, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL)
	write_log(writer, row_list)
	file.close()

def write_log(writer, row_list):

	for row in row_list:
		writer.writerow(row)

if __name__ == "__main__":

	main(row_list)