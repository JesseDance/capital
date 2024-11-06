from decimal import Decimal, DecimalException, InvalidOperation
from bson.decimal128 import Decimal128

'''
	Convert python Decimal to Decimal128 
		ex. mongo_decimal128 = Decimal128(Decimal('12.4'))

	Convert Mongo Decimal128 to Python Decimal 
		ex. python_decimal128 = mongo_decimal128.to_decimal()
'''

def convert_decimal(dict_item):
	# This function iterates a dictionary looking for types of Decimal and converts them to Decimal128
	# Embedded dictionaries and lists are called recursively.
	if dict_item is None: return None

	for k, v in list(dict_item.items()):
		if isinstance(v, dict):
			convert_decimal(v)
		elif isinstance(v, list):
			for l in v:
				convert_decimal(l)
		elif isinstance(v, Decimal):
			dict_item[k] = Decimal128(str(v))

	return dict_item


def convert_string_to_decimal128(convert_string):
	dec128 = None
	#Decimal("12.155").quantize(Decimal('.01'))
	try:
		if convert_string.isspace() is True:
			dec128 = Decimal128(Decimal("0").quantize(Decimal('.01')))

		else:
		 				
			if convert_string:
				dec128 = Decimal128(Decimal(convert_string).quantize(Decimal('.01')))
				# dec128 = Decimal128(Decimal(convert_string))
			
			else:
				dec128 = Decimal128(Decimal("0").quantize(Decimal('.01')))
				# dec128 = Decimal128(Decimal("0"))

	except(ValueError, DecimalException, InvalidOperation):
		return
	
	return dec128

def convert_decimal_to_decimal128(convert_value):
	dec128 = None
	#Decimal("12.155").quantize(Decimal('.01'))
	try:		
		 				
		if convert_value:
			dec128 = Decimal128(Decimal(convert_value).quantize(Decimal('.01')))
			# dec128 = Decimal128(Decimal(convert_string))
		
		else:
			dec128 = Decimal128(Decimal("0").quantize(Decimal('.01')))
			# dec128 = Decimal128(Decimal("0"))

	except(ValueError, DecimalException, InvalidOperation):
		return
	
	return dec128

'''
	convert from mongo decimal128 to python decimal
'''
def convert_decimal128_to_py_decimal(convert_mongo_decimal):
	py_decimal = None
	try:
		py_decimal = convert_mongo_decimal.to_decimal()

	except(ValueError, DecimalException, InvalidOperation):
		return
	
	return py_decimal


if __name__ == "__main__":
	'''
	dict_item = {"number": Decimal(5.25)}
	converted_dict = convert_decimal(dict_item)
	print("")
	print("converted dict ", converted_dict)
	print("")
	'''
	convert_string = ""
	#print("")
	#print(convert_string_to_decimal128(convert_string))
	#print("")

	print("")
	d128 = convert_decimal_to_decimal128(Decimal("25.50"))
	print(d128)
	print("type: ", type(d128))
	print("")

	#convert_mongo_decimal = convert_string_to_decimal128(convert_string)
	#print(convert_decimal128_to_py_decimal(convert_mongo_decimal))