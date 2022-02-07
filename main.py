from dataclasses import dataclass
import os
import logging
import json as js
import re

from dotenv import load_dotenv
import schoolopy
import discord
from discord import option


logging.basicConfig(level=logging.WARNING, filename="log.log")
load_dotenv()
bot = discord.Bot()
sc = schoolopy.Schoology(schoolopy.Auth(
    os.environ.get("apiKey"), os.environ.get("apiSecret")))
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
async def on_ready():
    print("----------------------")
    print("Bot is ready")
    await bot.change_presence(activity=discord.Activity(name="Syncing schoology since like ... ealrier this week"))


@bot.slash_command()
async def fetchpeople(ctx: discord.ApplicationContext):
    await ctx.respond("Working on that... please wait")
    print("Fetching people...")
    members = fetchpeople()

    memberString = ''.join(f"{member.firstlast}\n" for member in members)

    membersSplit = re.findall('.{1,2000}', memberString, flags=re.S)

    print(membersSplit)
    msg = await ctx.interaction.original_message()
    await msg.edit(content=membersSplit[0])
    if len(membersSplit) != 1:
        for i in range(1, len(membersSplit)):
            await ctx.send(membersSplit[i])

@bot.slash_command()
async def syncmember(ctx, member: discord.member.Member = option("member", None, description="Who do you want to assign")):
    pass


def fetchpeople() -> list[schoologyUser]:
    members = []
    memberslst = sc.get_group_enrollments(os.environ.get("groupId"))
    for member in memberslst:
        # Makes json and returns a list of classes for members
        # Try catch is for edge cases with names like Kear'i
        try:
            json = js.loads(member.json().replace("'", '"'))
            memberClass = schoologyUser(
                firstname=json["name_first"].lower(),
                middlename=json["name_middle"].lower(),
                lastname=json["name_last"].lower(),
                pfp=json["picture_url"],
                isAdmin=True if json["admin"] == 1 else False)
            members.append(memberClass)
        except:
            logging.warning(f"Failed for parse json for {member}")
    return members


if __name__ == '__main__':
    bot.run(os.environ.get('botToken'))
    print("Bot up")
