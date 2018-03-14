# -*- coding: utf-8 -*-
"""
@author lsipii
@see https://www.fullstackpython.com/blog/build-first-slack-bot-python.html
"""
from slackclient import SlackClient
from urllib import request, parse
import time

class SlackBot():

    """
    Initializes the slack client

    @param (dict) config
    """
    def __init__(self, config):
        self.config = config

        # Validate config
        if "SLACK_BOT_TOKEN" not in self.config:
            raise Exception("SLACK_BOT_TOKEN not in slackbot config")
        if "COFFEE_BOT_TOKEN" not in self.config:
            raise Exception("COFFEE_BOT_TOKEN not in slackbot config")
        if "COFFEE_BOT_URL" not in self.config:
            raise Exception("COFFEE_BOT_URL not in slackbot config")

        self.slack = SlackClient(self.config["SLACK_BOT_TOKEN"])
        self.slackBotUser = None
        self.slackRTMReadDelay = 1 # 1 sec read delay
        
        # Internal flags
        self.debugMode = False
        self.commandInProgress = False

        # Coffee keywords
        self.coffeeKeywords = [
            "kahvi", 
            "kahve",
            "kohve",
            "kaffe",
            "kahavi",
            "sumppi",
            "suppii",
            "sumpe",
            "sumpit",
            "caffe",
            "coffee",
            "cafe",
            "kofe",
            "cofe",
        ]

    """
    Engages the client
    """
    def engage(self):
        if self.slack.rtm_connect(with_team_state=False):
            
            # Configures the connection
            self.slackBotUser = self.slack.api_call("auth.test")
            
            # Validates the connection
            if not self.slackBotUser["ok"]:
                self.printDebugMessage("Slackbot authentication error", 1, True)

            self.printDebugMessage("Slack connection successful")
            self.printDebugMessage("Listening..")
            
            # The primary loop
            while True:
                if not self.commandInProgress:
                    self.resolveAndFireCommand(self.slack.rtm_read())            
                time.sleep(self.slackRTMReadDelay)
        else:
            self.printDebugMessage("Slackbot connection failed", 1, True)

    """
    Parses the slack events for commands to fire, fires commands 

    @param (array) slackEvents
    """
    def resolveAndFireCommand(self, slackEvents):

        """
        Validates the event
        
        @param (SlackEvent dict) event
        @return (bool) weWantThisEvent
        """
        def validateEvent(event):
            isValidEvent = False
            if event["type"] == "message" or event["type"] == "message.im":
                isValidEvent = True
            if isValidEvent and "subtype" in event:
                isValidEvent = False
            if isValidEvent and "user" not in event:
                isValidEvent = False
            return isValidEvent

        # Loop through the events, fire!
        for event in slackEvents:
            if validateEvent(event):
                if self.checkForDirectBotCommand(event):
                    self.fireBotControlCommand(event)
                    break
                elif self.checkIfShouldAskForACoffee(event["user"], event["text"]):
                    self.fireAskForCoffeeEvent(event)
                    break


    """
    Checks for bot control commands

    @param (SlackEvent dict) event
    @return (bool) weShouldIndeed
    """    
    def checkForDirectBotCommand(self, event):
        if event["user"] != self.slackBotUser["user_id"]:
            if self.checkIfDirectBotMessageEvent(event):
                return True
            else:
                return event["text"].find("<@"+self.slackBotUser["user_id"]+">") > -1
        return False


    """
    Resolves and fires slack bot control command

    @param (SlackEvent dict) event
    """
    def fireBotControlCommand(self, event):
        message = event["text"].lower()
        channel = event["channel"]

        # Flags as in progress
        self.commandInProgress = True

        try:
            if message.find("help") > -1 or message.find("ohje") > -1:
                self.sendBotHelp(channel)
            elif message.find("list") > -1 or message.find("listaa") > -1:
               self.sendBotCoffeeKeywords(channel)
            elif self.checkIfShouldAskForACoffee(event["user"], event["text"]):
                self.fireAskForCoffeeEvent(event)
            else:
                self.sendBotHelp(channel, "Sorry, the command not recognized")
        except Exception as e:
            self.printDebugMessage("fireBotControlCommand exception: "+str(e))
            self.sendBotDefaultErrorMsg(channel)

        # Flags as not in progress
        self.commandInProgress = False


    """
    Checks if coffee was asked, fires the asker if so

    @param (string) slackUserId
    @param (string) message
    @return (bool) weShouldIndeed
    """
    def checkIfShouldAskForACoffee(self, slackUserId, message):

        # we should indeed
        weShouldIndeed = False

        # Sanitize the message
        lowerCaseMessage = message.lower()
        lowerCaseMessage = message.replace('é', 'e')

        # Check for any matches
        if any(keyWord in lowerCaseMessage for keyWord in self.coffeeKeywords):
            weShouldIndeed = True

        # If a match, validate the user
        if weShouldIndeed:
            user = self.getSlackUser(slackUserId)
            if user is False:
                return False
            elif user["name"].startswith("Coffee_Situation:"): 
                return False

        return weShouldIndeed

    """
    Asks for coffee

    @param (SlackEvent dict) event
    """
    def fireAskForCoffeeEvent(event):

        # Flags as in progress
        self.commandInProgress = True

        try:
            # Arrange request data
            data = parse.urlencode({
                'api_token': self.config["COFFEE_BOT_TOKEN"], 
                'channel': event["channel"], 
                'network': self.slackBotUser["team"],
                'message': event["text"],
                'username': event["user"],
                'app':'tshCoffeeSlackbot', 
                'app_version':1
            }).encode()

            # Make the request
            req =  request.Request(self.config["COFFEE_BOT_URL"], data=data)
            resp = request.urlopen(req)

            # Expects a notify container with a message in the response
            if "notify" in resp and "message" in resp["notify"]:
                self.sendSlackBotResponse(channel, resp["notify"]["message"], resp["notify"])
            else:
                self.sendBotDefaultErrorMsg(channel)
        except Exception as e:
            self.printDebugMessage("fireAskForCoffeeEvent exception: "+str(e))
            self.sendBotDefaultErrorMsg(channel)

        # Flags as in progress
        self.commandInProgress = False

    """
    Sends bot help text to a channel

    @param (string) channel
    @param (string) errorMsg = None
    """
    def sendBotHelp(self, channel, errorMsg = None):
        helpTextLines = [
            "Usage:",
            "Help: Prints this usage text",
            "List: Prints accepted coffee related keywords",
        ]

        if errorMsg is not None:
            helpTextLines.insert(0, errorMsg)

        helpText = "\n".join(helpTextLines)
        self.sendSlackBotResponse(channel, helpText)

    """
    Sends bot help text to a channel

    @param (string) channel
    """
    def sendBotCoffeeKeywords(self, channel):
        helpText = "Coffee keywords: "
        keywords = ", ".join(self.coffeeKeywords)
        helpText += keywords
        self.sendSlackBotResponse(channel, helpText)

    """
    Sets the bot in debugmode

    @param (bool) debugMode
    """
    def sendBotDefaultErrorMsg(self, channel):
        helpText = "Sorry, the bot is busy solving a random encounter"
        self.sendSlackBotResponse(channel, helpText)

    """
    Sends a bot response back to the channel

    @param (string) channel
    @param (string) responseText
    @param (dict) slackResponseData = None, {icon_emoji|icon_url, username, unfurl_media, unfurl_links}
    """
    def sendSlackBotResponse(self, channel, responseText, slackResponseData = None):

        newLinesList = responseText.split('\n')
        responseTextFallback = ', '.join(newLinesList)
        responseTextFallback = responseTextFallback.replace(':, ', ': ')

        postArgs = {
            "channel": channel,
            "attachments": [{
                "text": responseText,
                "fallback": responseTextFallback,
                "color": "#120800",
            }],
            "unfurl_media": False,
            "unfurl_links": False,
        }

        if slackResponseData is not None:
            if "icon_emoji" in slackResponseData:
                postArgs["icon_emoji"] = slackResponseData["icon_emoji"]
            elif "icon_url" in slackResponseData:
                postArgs["icon_url"] = slackResponseData["icon_url"]
            if "username" in slackResponseData:
                postArgs["username"] = slackResponseData["username"]
            if "unfurl_media" in slackResponseData:
                postArgs["unfurl_media"] = slackResponseData["unfurl_media"]
            if "unfurl_links" in slackResponseData:
                postArgs["unfurl_links"] = slackResponseData["unfurl_links"]

        self.slack.api_call("chat.postMessage", **postArgs)

    """
    Gets slack user info by ID

    @param (string) slackUserId
    @return (SlackUser dict|bool) user
    """
    def getSlackUser(self, slackUserId):
        resp = self.slack.api_call(
            "users.info",
            user=slackUserId
        )
        if "ok" in resp and resp["ok"]:
            return resp["user"]
        return False

    """
    Checks if the message was sent to an public channel

    @param (SlackEvent dict) event
    @return (bool) isADirectBotQueryEvent
    """
    def checkIfDirectBotMessageEvent(self, event):
        
        if event["type"] == "message.im":
            return True

        # Ask from the API
        resp = self.slack.api_call(
            "channels.info",
            channel=event["channel"]
        )

        if "ok" in resp and not resp["ok"]:
            return True
        return False

    """
    Sets the bot in debugmode

    @param (bool) debugMode
    """
    def setDebugMode(self, debugMode):
        self.debugMode = debugMode

    """
    Prints a debug message in the runner console
    
    @param (string) message
    @param (int) exitCode = None, exits in debug mode if set
    @param (bool) exitAnyHow = False, disregards the debug mode
    """
    def printDebugMessage(self, message, exitCode = None, exitAnyHow = False):
        if self.debugMode:
            print(message)
            if exitCode is not None:
                exit(exitCode)
        elif exitAnyHow and exitCode is not None:
            print(message)
            exit(exitCode)