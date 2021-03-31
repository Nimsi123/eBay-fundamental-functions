import csv
import matplotlib.pyplot as plt
import os.path

from eBayScraper.ItemOrganization.ProductCollection import ProductCollection
from eBayScraper.SiteOperations import printer
from eBayScraper.SiteOperations.fast_download import fast_download

from eBayScraper.data_files.directories import make_eBay_link, csv_dir, png_dir

"""TODO:

i'm getting way to many "bad" listings

problem with scraping and visualizing with brand new products that have never been scraped before.

ebay brought back the extra keys in the sale date. bring back the key code!

"""

class query_list:
	"""
	Represents all of the eBay queries we are keeping track of.
	"""
	SALE_TYPES = ["BIN", "Auction"]

	def __init__(self, json):
		self.query_collection = list(query_list.split(json))		

	def scrape(self, client, start_index = 0, end_index = 999, single_oper = False, synchronous_scrape = False, print_stats = False, deep_scrape = False):

		counter = start_index
		for groupA, groupB, groupC in self.query_collection[start_index:end_index]:
			printer.new_query(groupC, counter)
			csv_file = csv_dir(groupC)

			with open(csv_file, "r", encoding = "UTF-8") as f:
				if len(f.readlines()) == 0:
					empty = True
				else:
					empty = False

			if os.path.isfile(csv_file) and not empty:
				try:
					collection = ProductCollection.import_data(csv_file)
				except: # TODO: we shouldn't need this here.
					with open(csv_file, "w") as file:
						pass
					collection = ProductCollection(groupA, groupB, groupC)
			else:
				with open(csv_file, "w") as file:
					pass
				collection = ProductCollection(groupA, groupB, groupC)

			for sale_type in query_list.SALE_TYPES:
				cmdline_args = (print_stats, deep_scrape)

				if print_stats: 
					printer.start_scrape(groupC, sale_type)
				fast_download(client, collection, sale_type, make_eBay_link(sale_type, groupC), *cmdline_args)
				if print_stats:
					printer.end_scrape(sale_type, collection.get_count_added())

			collection.export_data(csv_file)
			counter += 1

			if single_oper:
				return

	def visualize(self, start_index = 0, single_oper = False, print_stats = False):
		for _, __, groupC in self.query_collection[start_index:]:
			if print_stats:
				printer.start_graph(groupC)

			csv_file = csv_dir(groupC)
			png_file = png_dir(groupC)
			assert os.path.isfile(csv_file)

			with open(csv_file, "r", encoding = "UTF-8") as f:
				if len(f.readlines()) == 0:
					empty = True
				else:
					empty = False

			if empty:
				return

			ProductCollection.import_data(csv_file).scatter(png_file)

			if single_oper:
				return

	""" 	JSON -> eBayQuery 	"""
	def split_helper(json, groupA = None):
	    #helper method to split
	    for key, value in json.items():
	        if type(value) == list:
	            if not groupA:
	                groupA = key
	            for sub in value:
	                yield (groupA, key, sub)
	        else:
	            yield from query_list.split_helper(value, key)

	def split(json):
		"""
		:param json: a json-like dict that holds query information regarding its category
		:type json: dict
		:yields: A tuple consisting of (groupA, groupB, groupC) -- groups that the query falls into.
		:ytype: tuple
		"""
		yield from query_list.split_helper(json)

	'''
	def sql_export():
		# Larger example that inserts many records at a time

		c.execute("""CREATE TABLE products (name, type, date, price)""")

		for query in self.query_collection:
			for listing_type in ["Auction", "BIN"]:
			data = [query.name, "Auction"]	
		c.executemany('INSERT INTO stocks VALUES (?,?,?,?)', purchases)
	'''