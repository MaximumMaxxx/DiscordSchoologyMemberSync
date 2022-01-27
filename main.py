from dataclasses import dataclass
from dotenv import load_dotenv
import discord
import schoolopy 
import os
import logging
import json as js

logging.basicConfig(level=logging.INFO, filename="log.log")

load_dotenv()

bot = discord.Bot()

# Initialize the API session
sc = schoolopy.Schoology(schoolopy.Auth(os.environ.get("apiKey"), os.environ.get("apiSecret")))
# Change the member limit so you can get everyhing in one api call, there are better ways to handle this but just increasing the value works for now
sc.limit = os.environ.get("schoologyMemberLimit")

@dataclass
class schoologyUser():
    firstname: str
    middlename: str
    lastname: str
    pfp: str
    isAdmin: bool

    @property
    def fullname(self):
        return f"{self.firstname} {self.middlename} {self.lastname}"
    @property
    def firstlast(self):
        return f"{self.firstname} {self.lastname}"


@bot.event
async def on_ready(self):
    print("----------------------")
    print("Bot is ready")

    await bot.change_presence(activity = discord.Activity(name="Syncing schoology since like ... ealrier this week"))

@bot.slash_command(guilds=[935274828003418122])
async def fetchpeople(ctx:discord.ApplicationContext):
    await ctx.respond("Working on that... please wait")
    print("Fetching people...")
    members = fetchpeople()
    msg = await ctx.interaction.original_message()
    msg.edit(content="this is a new meesage")


@bot.slash_command(guilds=[935274828003418122])
async def ping(ctx:discord.ApplicationContext):
    ctx.respond("I am alive")

def fetchpeople() -> list[schoologyUser]:
    members = []
    memberslst = sc.get_group_enrollments(5341282072)
    for member in memberslst:
        # Makes json and returns a list of classes for members
        json = js.loads(member.json().replace("'",'"'))
        memberClass = schoologyUser(
        firstname = json["name_first"].lower(), 
        middlename = json["name_middle"].lower(), 
        lastname = json["name_last"].lower(),
        pfp = json["picture_url"],
        isAdmin = True if json["admin"] == 1 else False)
        members.append(memberClass)
    return members

if __name__ == '__main__':
    bot.run(os.environ.get('botToken'))
    print("Bot up")
