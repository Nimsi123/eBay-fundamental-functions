from Ebay.ItemOrganization.Item import Item
from Ebay.Site_Operations.cleanEntries import clean_title, clean_price, clean_shipping, clean_date
from Ebay.Site_Operations.traverseHtml import findElement, findAllLetters, findKey, findLink_new
from bs4 import BeautifulSoup
import bs4


def get_eBay_link(listing_type, search_str):
	"""
	Returns a starting link for a search query.

	>>> get_eBay_link("Auction", "Jimi Hendrix Poster")
	'https://www.ebay.com/sch/i.html?_from=R40&_nkw=Jimi Hendrix Poster&LH_Sold=1&LH_Complete=1&rt=nc&LH_Auction=1&_ipg=200'
	>>> get_eBay_link("Buy It Now", "Cream Disraeli Gears Album")
	'https://www.ebay.com/sch/i.html?_from=R40&_nkw=Cream Disraeli Gears Album&LH_Sold=1&LH_Complete=1&rt=nc&LH_BIN=1&_ipg=200'

	"""

	link = "https://www.ebay.com/sch/i.html?_from=R40&_nkw=" + search_str + "&LH_Sold=1&LH_Complete=1"

	if listing_type == "All Listings":
		pass
	elif listing_type == "Auction":
		link += "&rt=nc&LH_Auction=1"
	elif listing_type == "Buy It Now":
		link += "&rt=nc&LH_BIN=1"
	else:
		print("bad listing_type")

	return link + "&_ipg=200"


def extract(get_raw_func, html, element_type, class_name, clean_func):
	"""
	html -> a block of code representing a single listing

	Search the html block for the attribute of an item defined by 'element_type' and 'class_name.'
	Return the result of calling 'clean_func' on the item's attribute.
	"""

	raw = get_raw_func(html, element_type, "class", class_name)
	
	if raw == "nothing found":
		return None

	while type(raw) == bs4.Tag:
		#go deeper in a nest
		raw = raw.contents[0]

	return clean_func(str(raw)) #usable format for my algorithm

def extract_nested(get_raw_func, html, outer_element_type, outer_class_name, inner_element_type, inner_class_name, clean_func):
	"""
	Some attributes are nested within two blocks.
	Returns the attribute accessed by diving into one block, and then going deeper.
	"""

	outer_block = findElement(html, outer_element_type, "class", outer_class_name)

	if outer_block == "nothing found":
		return None
	
	outer_block = outer_block.contents[0]
	cleaned_inner = extract(get_raw_func, outer_block, inner_element_type, inner_class_name, clean_func)

	return cleaned_inner


def searchListings(html, element_type, class_code, item_collection, printer_bool_page_stats):
	"""
	html -> html code for an entire webpage

	Adds new items to item_collection.
	"""

	#ebay tries to mess with the sale date and my code
	#right before the code starts, I will find the special class_name that can be used to find the sale date!
	key = findKey(html, element_type, ["S", "o", "l", "d"])

	count = 0
	count_skipped_early = 0
	count_skipped_bad = 0
	count_skipped_class_code = 0
	for listing in html.find_all(element_type):
		if listing.get("class") == None:
			count_skipped_early += 1
			continue
		else:
			class_name = (listing.get("class"))[0]

		if class_name == class_code:
			#extract data from a single listing

			title = extract(findElement, listing, "h3", "s-item__title", clean_title)
			price = extract(findElement, listing, "span", "s-item__price", clean_price)
			shipping = extract(findElement, listing, "span", "s-item__shipping", clean_shipping)

			if key == None:
				date = extract(findElement, listing, "div", "s-item__title--tagblock", clean_date)
			else:
				print("*****need to do extra work to get sale date")
				date = extract_nested(findAllLetters, listing, "div", "s-item__title--tagblock", "span", key, clean_date)

			if title == None or price == None or shipping == None or date == None:
				print(f"*****bad listing -- title: {title} price: {price} shipping: {shipping} date: {date}")
				count_skipped_bad += 1
			else:
				total_cost = round(price+shipping, 2)
				item_collection.addItem( Item(title, total_cost, date) )
				count += 1
		else:
			count_skipped_class_code += 1

	if printer_bool_page_stats:
		print("\n")
		print("PAGE STATS")
		print(f"num item listings: {len(html.find_all(element_type))}")
		print(f"count added: {count}")
		print(f"count_skipped_early: {count_skipped_early} ... count_skipped_bad: {count_skipped_bad} ... count_skipped_class_code: {count_skipped_class_code}")



def receive_html(client, link):
	"""
	Returns the html from a webpage as a BeautifulSoup object.
	"""

	raw_html = client.get(url = link).text
	html = BeautifulSoup(raw_html, 'html.parser')

	return html


def aboutALink(client, link, product_collection):
	"""
	Starting from 'link', make requests to client for webpages' html code. 
	Populate 'product_collection' with new items listed on the webpage.
	Continue until we reach the end of the pages with listings.
	"""

	printer_bool_product_stats = False
	printer_bool_page_stats = False

	html = receive_html(client, link)
	print("link: ", link)

	strip_comma = lambda entry: entry.replace(',', '')
	print("extract: ", extract(findElement, html, "h1", "srp-controls__count-heading", strip_comma))
	total_listings = int(extract(findElement, html, "h1", "srp-controls__count-heading", strip_comma))

	if total_listings == 0:
		return

	max_iteration = min(50, int(total_listings/200 +1)) #ebay won't show us more that 10,000 items from their page even though there might be more to look at

	if printer_bool_product_stats:
		print("\nPRODUCT STATS")
		print("total_listings: ", total_listings)
		print("max_iteration", max_iteration)

	for count in range(max_iteration):

		html = receive_html(client, link)
		searchListings(html, "li", "s-item", product_collection, printer_bool_page_stats) #search the listings for data. populate the product_collection list

		if printer_bool_page_stats:
			print(f"iter count: {count} ... current item_list length: {len(product_collection.item_list)}")
			print(f"link: {link}")

		link = findLink_new(link)