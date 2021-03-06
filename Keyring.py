#!/usr/bin/env python3
# By Mili
import re
import lib
import errno
import codecs
import shodan
import requests
from sys import path
from time import sleep
from bs4 import BeautifulSoup
from configparser import ConfigParser
from os import listdir, makedirs, mkdir
from concurrent.futures import ThreadPoolExecutor
from os.path import isfile, join, isdir, exists, dirname

# Global Variables
parser = ConfigParser()
curdir = path[0]
baselink = 'https://github.com/'
baseraw = 'https://raw.githubusercontent.com/'

# Global Functions
def shodan_search(displaymode, page, repo_crawl, verbosity):
	if repo_crawl is False:
		lib.PrintStatus("Searching for Shodan keys...")
	elif repo_crawl is True and verbosity == 'on':
		lib.PrintStatus("Searching for Shodan keys...")
	shodan_pattern = r'\b[a-zA-Z0-9]{32}\b'
	pagetext = page.text
	keyset = []
	for k in re.findall(shodan_pattern, pagetext):
		keyset.append(k)
	if not keyset:
		if repo_crawl is False:
			lib.PrintFailure("No valid shodan keys found in set.")
		elif repo_crawl is True and verbosity == 'on':
			lib.PrintFailure("No valid shodan keys found in set.")
	else:
		valid_paid_keys = {}
		valid_unpaid_keys = []
		for key in set(keyset):
			api = shodan.Shodan(key)
			try:
				keydata = api.info()
				usage_limits = keydata['usage_limits']
				if keydata['plan'] == 'dev' or keydata['plan'] == 'edu':
					credits_tuple = (usage_limits['scan_credits'], usage_limits['query_credits'])
					valid_paid_keys[key] = credits_tuple
				elif keydata['plan'] == 'oss':
					valid_unpaid_keys.append(key)
			except Exception:
				pass
		if displaymode == 's' or displaymode == 'b':
			shodan_output = f'{curdir}/Output/ShodanKeys.txt'
			if not exists(dirname(shodan_output)):
				try:
					makedirs(dirname(shodan_output))
				except OSError as racecondition:
					if racecondition.errno != errno.EEXIST:
						raise
			with open(shodan_output, 'a') as sofile:
				sofile.write('----------VALID KEYS----------')
				for pkey in valid_paid_keys.keys():
					sofile.write(f"Key: {pkey}\nCredits (scan, query): {valid_paid_keys[pkey][0]}, {valid_paid_keys[pkey][1]}\n\n")
				sofile.write('----------UNPAID KEYS----------')
				for upkeys in set(valid_unpaid_keys):
					sofile.write(f'Key: {upkeys}')
def generic_search(key, displaymode, page, repo_crawl, verbosity):
	if repo_crawl is False:
		lib.PrintStatus(f"Searching for {key[0]} keys...")
	elif repo_crawl is True and verbosity == 'on':
		lib.PrintStatus(f"Searching for {key[0]} keys...")
	pagetext = page.text
	for k in re.findall(lib.patterns_dict[key], pagetext):
		if displaymode == 's' or 'b':
			if key[1] is True:
				lib.PrintHighSeverity("Warning: High Severity Item Found")
			gen_output = f'{curdir}/Output/{key[0]}.txt'
			if not exists(dirname(gen_output)):
				try:
					makedirs(dirname(gen_output))
				except OSError as racecondition:
					if racecondition.errno != errno.EEXIST:
						raise
			with open(gen_output, 'a') as gofile:
				gofile.write(f'Potential Key: {k}\n')
		elif displaymode == 'p' or 'b':
			lib.PrintSuccess(f'Potential Key: {k}')
def redis_search(displaymode, page, repo_crawl, verbosity):
	if repo_crawl is False:
		lib.PrintStatus("Scanning for Redis secrets...")
	elif repo_crawl is True and verbosity == 'on':
		lib.PrintStatus("Scanning for Redis secrets...")
	pagetext = page.text
	redis_pattern = r'redis://[0-9a-zA-Z:@.\\-]+'
	redis_artifacts = ['REDIS_PASSWORD', 'REDIS_CACHE_DATABASE', 'REDIS_HOST', 'REDIS_DATABASE']
	for k in re.findall(redis_pattern, pagetext):
		if displaymode == 's' or 'b':
			lib.PrintHighSeverity('Warning: High Severity Item Found')
			redis_output = f'{curdir}/Output/Redis/RedisLinks.txt'
			if not exists(dirname(redis_output)):
				try:
					makedirs(dirname(redis_output))
				except OSError as racecondition:
					if racecondition.errno != errno.EEXIST:
						raise
			with open(redis_output, 'a') as gofile:
				gofile.write(f'Potential link: {k}\n')
		elif displaymode == 'p' or 'b':
			lib.PrintSuccess(f'Potential link: {k}')
			lib.PrintHighSeverity('Warning: High Severity Item Found')
	for ra in set(redis_artifacts):
		if ra in pagetext:
			lib.PrintHighSeverity('Warning: High Severity Item Found')
			if displaymode == 's' or 'b':
				redis_artifacts_output = f'{curdir}/Output/Redis/RedisArtifacts.txt'
				if not exists(dirname(redis_artifacts_output)):
					try:
						makedirs(dirname(redis_artifacts_output))
					except OSError as racecondition:
						if racecondition.errno != errno.EEXIST:
							raise
				with open(redis_artifacts_output, 'a') as rafile:
					rafile.write(f'Artifact found: {ra}')
			elif displaymode == 'p' or 'b':
				lib.PrintSuccess(f'Artifact Found: {ra}')
def ssh_keys_search(displaymode, page, repo_crawl, verbosity):
	if repo_crawl is False:
		lib.PrintStatus("Scanning for SSH Keys...")
	elif repo_crawl is True and verbosity == 'on':
		lib.PrintStatus("Scanning for SSH Keys...")
	pagetext = page.text
	ssh_keys_identifiers = ["-----BEGIN OPENSSH PRIVATE KEY-----", "-----BEGIN DSA PRIVATE KEY-----", "-----BEGIN EC PRIVATE KEY-----"]
	for pattern in set(ssh_keys_identifiers):
		if pattern in pagetext:
			if displaymode == 's' or 'b':
				ssh_output = f'{curdir}/Output/SSHKeys.txt'
				if not exists(dirname(ssh_output)):
					try:
						makedirs(dirname(ssh_output))
					except OSError as racecondition:
						if racecondition.errno != errno.EEXIST:
							raise
				with open(ssh_output, 'a') as gofile:
					gofile.write(f'SSH Key: {pattern}\n')
			elif displaymode == 'p' or 'b':
				lib.PrintSuccess(f'SSH Key: {pattern}')
			lib.PrintHighSeverity('Warning: High Severity Item Found')
def misc_database_secrets(displaymode, page, repo_crawl, verbosity):
	if repo_crawl is False:
		lib.PrintStatus("Searching for miscellaneous database secrets...")
	elif repo_crawl is True and verbosity == 'on':
		lib.PrintStatus("Searching for miscellaneous database secrets...")
	pagetext = page.text
	database_secrets = ['DB_USER', 'DB_PASSWORD', 'SUPERUSER_NAME', 'SUPERUSER_PASSWORD', 'DB_NAME']
	for ds in set(database_secrets):
		if ds in pagetext:
			lib.PrintHighSeverity('Warning: High Severity Item Found')
			if displaymode == 's' or 'b':
				db_output = f'{curdir}/Output/DatabaseSecrets.txt'
				if not exists(dirname(db_output)):
					try:
						makedirs(dirname(db_output))
					except OSError as racecondition:
						if racecondition.errno != errno.EEXIST:
							raise
				with open(db_output, 'a') as gofile:
					gofile.write(f'Database Secret: {ds}\n')
			elif displaymode == 'p' or 'b':
				print(f"Database secret: {ds}")
def better_search_execute(displaymode, page, repo_crawl, verbosity):
	shodan_search(displaymode, page, repo_crawl, verbosity)
	redis_search(displaymode, page, repo_crawl, verbosity)
	ssh_keys_search(displaymode, page, repo_crawl, verbosity)
	misc_database_secrets(displaymode, page, repo_crawl, verbosity)

	for x in lib.patterns_dict.keys():
		generic_search(x, displaymode, page, repo_crawl, verbosity)
def connect(url):
	# TODO: Add Color
	def PrintConnectError():
		lib.PrintError(f"""
Exception occurred: {e}
Possible causes: Poor/Non-functioning Internet connection or {url} is unreachable
Possible fixes: Troubleshoot internet connection or check status of {url}
		""")
	def PrintTimeoutError():
		lib.PrintError(f"""
Exception occurred: {e}
Possible causes: Too many requests made to {url}
Possible fixes: Check firewall settings and check the status of {url}.
		""")
	def PrintGenericError():
		lib.PrintError(f"""
Exception occurred: {e}
		""")
	try:
		page = requests.get(url, headers=lib.random_headers())
		return page
	except Exception as e:
		if e is requests.exceptions.ConnectionError:
			PrintConnectError()
		elif e is requests.exceptions.Timeout:
			PrintTimeoutError()
		else:
			PrintGenericError()
		return 'connection_failed'
def get_repos(profilelink):
	if profilelink.endswith('//'):
		profilelink = profilelink[:len(profilelink) - 1]
	repos = profilelink + '?tab=repositories'
	repos = repos.replace(' ', '')
	profilepage = connect(repos)
	soup = BeautifulSoup(profilepage.text, 'html.parser')
	hrefs = soup.findAll('a', href=True, itemprop="name codeRepository")
	repolist = []
	for h in hrefs:
		repolink = baselink + str(h['href'])
		repolist.append(repolink)
	return repolist
def traverse_repos(repolist, link_type, directory_filtering, blacklisted_directories, verbosity): # Here Be Recursion
	fileaddrs = []
	def spider_current_level(page):
		dirnames = []
		levelsoup = BeautifulSoup(page.text, 'html.parser')
		spans = levelsoup.findAll('span', {'class': "css-truncate css-truncate-target"})
		for s in spans:
			subtags = s.findAll('a', {'class': "js-navigation-open"}, href=True)
			for st in subtags:
				if '/blob/' in st['href']:
					lnk = st['href'].replace('blob/', '')
					if verbosity == 'y':
						lib.PrintStatus(f"File: {lnk}")
					full = baseraw + lnk
					fileaddrs.append(full)
				else:
					if verbosity == 'y':
						lib.PrintStatus(f"Directory: {st['href']}")
					if directory_filtering is True:
						slashcount = 0
						for character in st['href']:
							if character == '/':
								slashcount += 1
						directory_name = st['href'].split('/')[slashcount]
						if directory_name not in set(blacklisted_directories):
							dirnames.append(st['href'])
					else:
						dirnames.append(st['href'])
		if len(dirnames) == 0:
			if verbosity == 'y':
				lib.PrintStatus("Branch exhausted")
		else:
			for subdir in dirnames:
				subdir_addr = baselink + subdir
				subdir_page = connect(subdir_addr)
				spider_current_level(subdir_page)
	if link_type == 'profile':
		for i in repolist:
			repopage = connect(i)
			if repopage == 'connection_failed':
				lib.PrintError(f'Connection to {i} failed.')
			else:
				spider_current_level(repopage)
	elif link_type == 'repo':
		repopage = connect(repolist)
		if repopage == 'connection_failed':
			lib.PrintError(f'Connection to {repolist} failed.')
		else:
			spider_current_level(repopage)
	return fileaddrs
def scrape(scrape_input_method, displaymode, limiter, repo_crawl, link_type, directory_filtering, blacklisted_directories, verbosity):
	if scrape_input_method.lower() == 'm':
		url = input("Enter the URL: ")
		if url[len(url)-1] == ' ':
			url = url[:len(url)-1]
		urlpage = connect(url)
		if urlpage == 'connection failed':
			lib.PrintError("Connection to specified URL could not be established.")
			exit()
		else:
			lib.PrintStatus('Status: [200], Searching for API Keys...')
			if repo_crawl is False:
				better_search_execute(displaymode, urlpage, repo_crawl, verbosity)
			else:
				if link_type == 'profile':
					resources = get_repos(url)
					file_addresses = traverse_repos(resources, link_type, directory_filtering, blacklisted_directories, verbosity)
				elif link_type == 'repo':
					file_addresses = traverse_repos(url, link_type, directory_filtering, blacklisted_directories, verbosity)
				if len(file_addresses) > 0:
					executor = ThreadPoolExecutor(max_workers=len(file_addresses))
				else:
					lib.PrintError("Fatal Error: No File Addresses Were Returned")
					lib.PrintError("This is likely a mistyped, but valid, URL in the input.")
					lib.PrintError("This also occurs if a github repo link is provided when the profile option is enabled, or vice versa")
					exit()
				for addr in set(file_addresses):
					urlpage = connect(addr)
					executor.submit(better_search_execute(displaymode, urlpage, repo_crawl, verbosity))
					sleep(limiter)
			lib.PrintSuccess("Scanning complete.")
	else:
		while True:
			url_file = input("Enter the full path to the input file: ")
			if isfile(url_file) is True:
				break
			elif str(url_file) == "":
				pass
			else:
				lib.PrintError("No Such File Found.")
				continue
		with open(url_file) as ufile:
			count = 0
			for line in ufile.readlines():
				if repo_crawl is False:
					count += 1
					urlpage = connect(line.rstrip())
					if urlpage == 'connection failed':
						lib.PrintFailure(f"[Line: {count}] Connection failed on host {line}")
					else:
						better_search_execute(displaymode, urlpage, repo_crawl, verbosity)
						sleep(limiter)
				else:
					if link_type == 'profile':
						resources = get_repos(line)
					elif link_type == 'repo':
						resources = line
					file_addresses = traverse_repos(resources, link_type, directory_filtering, blacklisted_directories, verbosity)
					executor = ThreadPoolExecutor(max_workers=len(file_addresses))
					for addr in set(file_addresses):
						urlpage = connect(addr)
						executor.submit(better_search_execute(displaymode, urlpage, repo_crawl, verbosity))
						sleep(limiter)
def load_config():
	if isdir(f'{curdir}/KRconfig') is False:
		lib.PrintError(f"Config directory not detected in {curdir}...")
		lib.PrintStatus(f"Making config directory in {curdir}...")
		mkdir(f'{curdir}/KRconfig')
	config_files = {}
	count = 0
	onlyfiles = [f for f in listdir(f'{curdir}/KRconfig') if isfile(join(f'{curdir}/KRconfig', f))]
	for file in onlyfiles:
		if file.endswith('.ini'):
			count += 1
			config_files[file] = count
	if count == 0:
		lib.PrintStatus("No config files detected, making default...")
		with codecs.open(f'{curdir}/KRconfig/defaultconfig.ini', 'w', 'utf-8') as dconf:
			dconf.write(
'''[initial_vars]
displaymode = b
[scraping_vars]
scrape_input_method = m
limiter = 5
repo_crawl = False
link_type = regular
directory_filtering = False
blacklisted_directories = []
verbosity = off''')
		config_files['Default Configuration'] = 1
		count += 1
	for k in config_files.keys():
		print(f"[{config_files[k]}]: {k}")
	while True:
		try:
			load_choice = int(input("Select which config file to load: "))
			if load_choice > count:
				raise ValueError
			elif load_choice == "":
				pass
				continue
			else:
				break
		except ValueError:
			lib.PrintFailure("Invalid Input. Please enter the integer that corresponds with the desired config file.")
			continue
	for k in config_files.keys():
		if load_choice == config_files[k]:
			selected_file = k
	parser.read(f"{curdir}/KRconfig/{selected_file}", encoding='utf-8')
	# Initial Variables
	displaymode = parser.get('initial_vars', 'displaymode')
	# Scraping Variables
	scrape_input_method = parser.get('scraping_vars', 'scrape_input_method')
	limiter = int(parser.get('scraping_vars', 'limiter'))
	repo_crawl = parser.getboolean('scraping_vars', 'repo_crawl')
	link_type = parser.get('scraping_vars', 'link_type')
	directory_filtering = parser.getboolean('scraping_vars', 'directory_filtering')
	blacklisted_directories = parser.get('scraping_vars', 'blacklisted_directories')
	verbosity = parser.get('scraping_vars', 'verbosity')
	return displaymode, scrape_input_method, limiter, repo_crawl, link_type, directory_filtering, blacklisted_directories, verbosity
def manual_setup():
	while True:
		displaymode = input("[p]rint to screen, [s]ave to file, or [b]oth: ")
		if displaymode == "":
			pass
			continue
		elif displaymode.lower() == 'p' or 's' or 'b':
			break
		else:
			lib.PrintError("Invalid Input.")
			continue
	while True:
		scrape_input_method = input("[m]anual input (single url) or load from [f]ile: ")
		if scrape_input_method.lower() == 'm' or 'f':
			break
		elif scrape_input_method == "":
			pass
			continue
		else:
			lib.PrintError("Invalid Input.")
			continue
	while True:
		try:
			limiter = int(input("Enter the time between requests, in seconds: "))
			if limiter < 0:
				continue
			elif limiter == "":
				pass
				continue
			break
		except ValueError:
			lib.PrintError("Invalid Input. Enter a positive integer.")
			continue
	lib.PrintStatus("If provided links to one (or multiple) github profiles, Keyring can crawl all repositories for secrets.")
	lib.PrintStatus("If provided links to github repositories, Keyring can crawl all files in that repository.")
	lib.PrintStatus("However, this means Keyring WILL NOT FUNCTION CORRECTLY if provided links to other pages in the same text file, or if profile and repo links are mixed.")
	lib.PrintStatus("Large profiles will also take a fairly long time, as Keyring fetches ALL files from ALL repos.")
	while True:
		repocrawlchoice = input("Enable repo crawling? [y]/[n]: ")
		if repocrawlchoice == "":
			pass
			continue
		elif repocrawlchoice.lower() == 'y':
			repo_crawl = True
			while True:
				lib.PrintHighSeverity("Warning: Turning on verbosity will output a LOT when spidering large profiles.")
				verbosity = input("Enable verbosity for spidering: [y]/[n]: ")
				if verbosity == "":
					pass
					continue
				elif verbosity.lower() == 'y' or 'n':
					break
				else:
					lib.PrintError("Invalid Input.")
					continue
			while True:
				link_type_input = input("Github [p]rofile links or Github [r]epository links?: ")
				if link_type_input == "":
					pass
					continue
				elif link_type_input.lower() == 'p':
					link_type = 'profile'
					break
				elif link_type_input.lower() == 'r':
					link_type = 'repo'
					break
				else:
					lib.PrintError("Invalid Input.")
					continue
			while True:
				lib.PrintStatus("Repositories may contain large directories with no value in crawling, such as dependency folders.")
				directory_filtering_status = input("Enable directory filtering: [y]/[n]: ")
				if directory_filtering_status.lower() == 'y':
					directory_filtering = True
					blacklisted_directories = []
					blacklisted_directory_input = input("Enter the directory names you wish to filter (separated by a single comma): ").split(',')
					for directory in blacklisted_directory_input:
						blacklisted_directories.append(directory)
					break
				elif directory_filtering_status.lower() == 'n':
					directory_filtering = False
					blacklisted_directories = [] #placeholder for configparser
					break
				elif directory_filtering_status == "":
					pass
					continue
				else:
					lib.PrintError("Invalid Input.")
					continue
			break
		elif repocrawlchoice.lower() == 'n':
			repo_crawl = False
			link_type = 'regular'
			directory_filtering = False
			blacklisted_directories = []
			verbosity = 'off'
			break
		else:
			lib.PrintError("Invalid Input.")
			continue
	while True:
		savechoice = input("Save choices as config file? [y]/[n]: ")
		if savechoice.lower() == 'n':
			break
		elif savechoice.lower() == 'y':
			while True:
				if isdir(f'{curdir}/KRconfig') is False:
					lib.PrintError(f"Config directory not detected in {curdir}...")
					lib.PrintStatus(f"Making config directory...")
					mkdir(f'{curdir}/KRconfig')
					break
				else:
					break
			configname = input("Enter the name for this configuration: ")
			with open(f'{curdir}/KRconfig/{configname}.ini', 'w') as cfile:
				cfile.write(
f'''[initial_vars]
displaymode = {displaymode}
[scraping_vars]
scrape_input_method = {scrape_input_method}
limiter = {limiter}
repo_crawl = {repo_crawl}
link_type = {link_type}
directory_filtering = {directory_filtering}
blacklisted_directories = {blacklisted_directories}
verbosity = {verbosity}
''')
		else:
			lib.PrintError("Invalid Input.")
			continue
		break
	return displaymode, scrape_input_method, limiter, repo_crawl, link_type, directory_filtering, blacklisted_directories, verbosity
def main():
	try:
		while True:
			initchoice = input("[L]oad config file or [m]anually enter?: ")
			if initchoice.lower() == 'l':
				displaymode, scrape_input_method, limiter, repo_crawl, link_type, directory_filtering, blacklisted_directories, verbosity = load_config()
				if scrape_input_method == 'f':
					while True:
						addressfile = input("Enter the full path to the address file: ")
						if isfile(addressfile) is True:
							break
						else:
							lib.PrintError("No such file found.")
							continue
				break
			elif initchoice.lower() == 'm':
				displaymode, scrape_input_method, limiter, repo_crawl, link_type, directory_filtering, blacklisted_directories, verbosity = manual_setup()
				break
			elif initchoice == "":
				pass
			else:
				lib.PrintError("Invalid Input.")
				continue
		scrape(scrape_input_method, displaymode, limiter, repo_crawl, link_type, directory_filtering, blacklisted_directories, verbosity)
	except KeyboardInterrupt:
		# print() # are you doing something with this?
		lib.PrintError("Search canceled.")

if __name__ == '__main__':
	main()
