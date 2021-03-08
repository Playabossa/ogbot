import discord
import requests as r
from lxml import etree
from tabulate import tabulate
import os
from dotenv import load_dotenv
import datetime
from matplotlib import pyplot as plt

#need to pip install discord, requests, lxml, tabulate, dotenv, matplotlib

PlanetList = []
PositionList = []


global result

#there is a .env file with the Key of the bot. i'd like that to be private for now 
load_dotenv()
TOKEN = os.getenv('TOKEN')
client = discord.Client()

# for updateing xml data.
def update():
    dateNow = datetime.date.today()

    #parse current Collection of datapoints list
    xmlFile = etree.parse("HiScore.xml")
    i = "1"

    set i to the number of collected data points +1
    tree2 = xmlFile.getroot()
    for player in tree2.iter("Player"):
        for score in player.iter("Score"):
            i = score.attrib.get("number")
        i = str(int(i) + 1)
        break

    
    ElementsThere = False

    #check if current hiscore list has data
    for player in tree2.iter("Player"):
        if len(player) > 0:
            ElementsThere = True
        else:
            ElementsThere = False
        break


    if ElementsThere == False:
	
        lastUpdate = tree2.find("updated").attrib["date"]
	#check if not updated today
        if not dateNow.strftime("%Y-%m-%d") == lastUpdate:
	    #set new updated time
            tree2.find("updated").set("date", dateNow.strftime("%Y-%m-%d"))
	
	    #get xml from API
            response = r.get("https://s173-en.ogame.gameforge.com/api/highscore.xml?category=1&type=0")
            tree = etree.fromstring(response.content)
	    #make a player with childnode score
            for player in tree.iter("player"):
                child = etree.Element("Player")
                child.set("ID", player.attrib.get("id"))
                child.tail = "\n"
                score1 = etree.Element("Score")
                score1.text = player.attrib.get("score")
                score1.set("number", i)
                score1.set("date", dateNow.strftime("%Y-%m-%d"))
                score1.tail = "\n"
                child.append(score1)
                tree2.append(child)
	    #add into our hiscore xml
            xmlFile.write("HiScore.xml")

            lastUpdate = dateNow
    else:
	 #if we already have data
         lastUpdate = tree2.find("updated").attrib["date"]
	 #check if not updated today
         if not dateNow.strftime("%Y-%m-%d") == lastUpdate:
		
	    #update updated time
            tree2.find("updated").set("date", dateNow.strftime("%Y-%m-%d"))
            #get xml from API
            response = r.get("https://s173-en.ogame.gameforge.com/api/highscore.xml?category=1&type=0")
            tree = etree.fromstring(response.content)
	    #per player of HiScore.xml add another score child node and write it back to the file
            for player in tree.iter("player"):
                for player2 in tree2.iter("Player"):
                    if player2.attrib.get("ID") == player.attrib.get("id"):
                        child = player2
                        score1 = etree.Element("Score")
                        score1.text = player.attrib.get("score")
                        score1.set("number", i)
                        score1.set("date", dateNow.strftime("%Y-%m-%d"))
                        score1.tail = "\n"
                        child.append(score1)
	    #aka the reason it takes so long, because it has to write ALL the nodes back ...
            xmlFile.write("HiScore.xml")

            lastUpdate = dateNow      
  
#function for doing the graph          
def graph(name):
    update()
    try:
        ID = getID(name)
        tree = etree.parse("HiScore.xml") 
        listScore = []
        listDate = []
	#two lists ListScore = y axis
	#ListDate = x axis
	#for every player get the recorded score of the day
        for Player in tree.iter("Player"):
            if Player.attrib.get("ID") == ID:
                for Score in Player.iter("Score"):
                    listScore.append(int(Score.text))
                    listDate.append(Score.attrib.get("date"))


	#give error if somethings empty
        if listScore == []:
            return "fuck"
        if listDate == []:
            return "fuck"
	
	#use matplotlib to make it into a picture
        plt.style.use("dark_background")
        plt.figure(figsize=(20,10))
        plt.xlabel("Date")
        ylbl = "Points"
	#check for W I D E numbers
        for elem in listScore:
            if(elem > 1000000):
                ylbl = "Points in Millions"
            if elem > 10000000:
                ylbl = "Points in ten Millions"
            if elem > 100000000:
                ylbl = "Points in hundred Millions"
	
	#get difference from day before
        diffYes = listScore[-1] - listScore[-2] 
        if diffYes > 0:
            diffStr = "+" + '{:,}'.format(diffYes) + " Points"
        else:
            diffStr = '{:,}'.format(diffYes) + " Points"
	#give titles and save image as jpeg. img gets deleted after it is sentd
        plt.ylabel(ylbl)        
        plt.suptitle("Point growth of " + name, fontsize = 24)
        plt.title(diffStr, fontsize=15, loc="right")
        plt.xticks(rotation=40)
        plt.plot(listDate, listScore, marker="o")  
        plt.savefig("img" + ID)
        return "img" + ID + ".png"
    except:
        return "fuck"
    

         
#function that retrieves the ID for a player name.
def getID(Name):
    global result
    result = ""
    try:
	#get api list of all players
        response = r.get("https://s173-en.ogame.gameforge.com/api/players.xml")

        tree = etree.fromstring(response.content)
	find our entered player, return 0 if nothing is found
        for player in tree.iter("player"):
            if(Name == player.attrib.get("name")):
                result += "Showing Data for Player: " + Name + "\n"
                return player.attrib.get("id")
        return "0"

    except:
        result = "no data found. check spelling and try again, Noob."


#showme function
def getData(ID):
    global result
    ToAdd = []
    PlanetList = []
    PositionList = []
    #get api data
    response = r.get("https://s173-en.ogame.gameforge.com/api/playerData.xml?id=" + ID)
    tree = etree.fromstring(response.content)

    #ally
    allystr = " "
    for ally in tree.iter("alliance"):
        for name in ally.iter("name"):
            allystr += name.text
        for tag in ally.iter("tag"):
            allystr += " - " + tag.text
    if allystr == " ":
        result += ""
    else:
        result += "Member of:" + allystr

    result += "\n\nRankings\n\n"

    #positions
    ships = False
    for position in tree.iter("position"):
        ToAdd = []
        if position.attrib.get("type") == "0":
            ToAdd.append("Points")
        if position.attrib.get("type") == "1":
            ToAdd.append("Economy")
        if position.attrib.get("type") == "2":
            ToAdd.append("Research")
        if position.attrib.get("type") == "3":
            ToAdd.append("Military")
            ships = True
        if position.attrib.get("type") == "4":
            ToAdd.append("Military Points lost")
        if position.attrib.get("type") == "5":
            ToAdd.append("Military Points build")        
        if position.attrib.get("type") == "6":
            ToAdd.append("Military Points destroyed")
        if position.attrib.get("type") == "7":
            ToAdd.append("Honor Points")
        ToAdd.append(position.attrib.get("score"))
        ToAdd.append(position.text)
        if ships:
            ToAdd.append("Ships: " + position.attrib.get("ships"))
            ships = False
        PositionList.append(ToAdd)

    result += tabulate(PositionList, headers = ["Category", "Points", "Rank", ""])
    
    result += "\n\nPlanets\n\n"

    #planets
    for planet in tree.iter("planet"):
        ToAdd = []
        ToAdd.append(planet.attrib.get("name"))
        ToAdd.append(planet.attrib.get("coords"))

        for moon in planet.iter("moon"):
            ToAdd.append(moon.attrib.get("name"))
            ToAdd.append(moon.attrib.get("size") + "km")

        PlanetList.append(ToAdd)
    result += tabulate(PlanetList, headers=["Planet name", "Coordinates", "Moon", "Moon Size"])

    #Last Update
    date = int(tree.attrib.get("timestamp"))
    date = datetime.datetime.utcfromtimestamp(date).strftime("%d-%m-%Y %H:%M")

    result += "\n\nlast updated: " + date

#ini for showme. gets id and then collects data
def ini(Name):  
    global result
    PID = (getID(Name))
    if PID == "0":
        result = "No data found, please check spelling and try again."
    else:
        getData(PID)

#event that tells you bot has connected
@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')

#events that happen on every message
@client.event
async def on_message(message):
    global result
    #do nothing if author is bot itself
    if message.author == client.user:
        return
    #showme command.
    if message.content.startswith("$showme"):
	#remove Command from message string
        Name = message.content[8:]
	#get Id and put data into result
        ini(Name)
	#to return it as codeblock with three ´´´
        await message.channel.send("""
        ```""" + result + """
        ```""")
        result = ""
    #graph command
    if message.content.startswith("$graph"):
	#remove command and graph it
        Name = message.content[7:]
	#get the file from graph
        file = graph(Name)
	#fuck means bad
        if file == "fuck":
            await message.channel.send("""
        ```""" + "There's nothing i can show you. You most likely can't spell." + """
        ```""")
        else:
	    #send file
            await message.channel.send(file=discord.File(file))
	    #delete file
            os.remove(file)
        


#client.run(TOKEN)
#to graph:
graph("Magalampa")
#to showme:
#ini("Magalampa")