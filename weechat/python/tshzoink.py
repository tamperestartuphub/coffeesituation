"""
@author lsipii
# Derived from: irssinotifier
"""
import weechat
import urllib

weechat.register("tshzoink", "TshZoink", "1.0", "GPL3", "Responds to coffee queries", "", "")
weechat.prnt("", "TSH Zoink registered")

# Settings
settings = {
    "api_token": "",
}

for option, default_value in settings.items():
    if weechat.config_get_plugin(option) == "":
        weechat.prnt("", weechat.prefix("error") + "tshzoink: Please set option: %s" % option)
        weechat.prnt("", "tshzoink: /set plugins.var.python.tshzoink.%s STRING" % option)

# Hook message listener
weechat.hook_print("", "", "", 1, "checkIfShouldAskForCoffee", "")

"""
Checks if coffee was asked, fires the asker if so
"""
def checkIfShouldAskForCoffee(data, bufferp, uber_empty, tagsn, isdisplayed, ishilight, prefix, message):

	coffeeQuestions = ["kahvia", "coffee can I has"]
	acceptedChannels = ["#tests"]

	if message in coffeeQuestions:
		# Resolve channel
		chan = (weechat.buffer_get_string(bufferp, "short_name") or weechat.buffer_get_string(bufferp, "name"))

		if chan in acceptedChannels:
			askForCoffee()

	return weechat.WEECHAT_RC_OK

"""
Asks for coffee
"""
def askForCoffee():
    API_TOKEN = weechat.config_get_plugin("api_token")
    if API_TOKEN != "":
    	weechat.prnt("", "TSH Zoink asks for coffee")
        url = "https://morphotic-cow-5470.dataplicity.io/"
        postdata = urllib.urlencode({'accessKey':API_TOKEN,'version':1})
        hook1 = weechat.hook_process_hashtable("url:"+url, {"postfields":  postdata}, 2000, "handleAskingResponse", "")

"""
Asks for coffee
"""
def handleAskingResponse(pointer, data, command, returnCode, stdout = None, stderr = None):
    weechat.prnt("", "TSH Zoink asked for coffee")
    weechat.prnt("", pointer)
    return weechat.WEECHAT_RC_OK