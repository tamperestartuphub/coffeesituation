#!/usr/bin/env python3
"""
@author lsipii
"""
import sys, getopt
from app.AppInfo import AppInfo
from app.ConfigReader import ConfigReader
from app.hardware.storage.MediaStorageFactory import MediaStorageFactory

# App runner
if __name__ == '__main__':

	argv = sys.argv[1:]
	
	# Help texts
	def printHelp():
		print("Usage: cron.py --help|--version") 
		exit()
		
	try:
		opts, args = getopt.getopt(argv, "hv", ["help", "version"])
	except getopt.GetoptError:
		printHelp()

	for opt, arg in opts:

		if opt in ("-h", "--help"):
			printHelp()
		if opt in ("-v", "--version"):
			print(AppInfo.getAppVersion())
			exit()

	# Run the bot
	config = ConfigReader().getConfig()
	try:
		S3Storage = MediaStorageFactory.getInstance(config, "S3")
		S3Storage.clearTooOldMediaFiles()
	except Exception as e:
		print(str(e))
	