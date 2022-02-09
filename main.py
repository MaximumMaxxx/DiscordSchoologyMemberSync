import asyncio
from dataclasses import dataclass
import os
import logging
import json as js
import re
import sqlite3 as sl


from dotenv import load_dotenv
import schoolopy
import discord
from discord import option

logging.basicConfig(level=logging.WARNING, filename="log.log")
con = sl.connect('my-test.db')
load_dotenv()
bot = discord.Bot(intents=discord.Intents.members())
sc = schoolopy.Schoology(schoolopy.Auth(
    os.environ.get("apiKey"), 
    os.environ.get("apiSecret")))
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


async def updateRoleList():
    logging.info("Updating roles")
    for guild in bot.guilds:
        try:
            with con:
                con.execute(f"SELECT * FROM {guild.id}")
                associations = con.fetchall()
            role = discord.utils.get(guild.roles, id=int(os.environ.get("roleId")))
            for member in guild.fetch_members():
                await member.remove_role(role)
                for row in associations:
                    if member.id != row[0]:
                        continue

                    await member.add_role(role)
        except Exception as e:
            logging.error(f"Error wthile accessing table {guild.id} {e}")


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
@discord.ext.commands.has_permissions(administer=True)
async def syncmember(ctx: discord.ApplicationContext, member: discord.member.Member = option("member", None, description="Who do you want to assign"), person: str = option("person", None, description="The first and last name for the person you want to associate with")):
    names = [member.firstlast.lower() for member in fetchpeople()]
    if person in names:
        try:
            with con:
                con.execute(f"""
                    CREATE TABLE IF NOT EXISTS {ctx.guild_id()} 
                    (uid TEXT, name TEXT UNIQUE);
                """)
                con.execute(f"""
                    CREATE TABLE IF NOT EXISTS set{ctx.guild_id()} 
                    (setting TEXT UNIQUE, value TEXT);
                """)
                con.execute(f"REPLACE INTO {ctx.guild_id()} ('{member.id}', '{person.lower()}');")
                con.commit()
            embed = discord.Embed(title="Sucess", description=f"{member.name} as succesfully been associated with {person}", color=discord.Color.green)
            ctx.respond(embed= embed)
            return
        except Exception as e:
            ctx.respond(f"something is broke here {e}")
            logging.error(f"Error in syncmember {e}")
            return
    else:
        embed = discord.Embed(color = discord.Color.red(), title = "Error", description = "Good chance the bot is broken but it's also possible that you did something wrong.")
        ctx.respond(embed = embed)
        return

@bot.slash_command()
@discord.ext.commands.has_permissions(administer=True)
async def refreshlist(ctx: discord.ApplicationContext):
    ctx.respond("Working on that")
    await updateRoleList()
    msg = await ctx.interaction.original_message()
    await msg.edit("Done")


async def roleloop():
    await updateRoleList()
    # 24hours
    asyncio.sleep(60*60*60*24)
    roleloop()

if __name__ == '__main__':
    bot.loop.create_task(roleloop())
    bot.run(os.environ.get('botToken'))
    print("Bot up")