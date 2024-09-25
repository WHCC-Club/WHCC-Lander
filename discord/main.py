import interactions
from interactions import (
    slash_command, SlashContext, Embed, Modal, ShortText,
    modal_callback, ModalContext, slash_option, OptionType,
    ParagraphText
)
from models import SessionLocal, User, Challenge
import json
from dotenv import load_dotenv
import os

load_dotenv()

GUILD_ID = "1174483344533246054"  #
bot = interactions.Client(
    token=os.getenv("DISCORD_BOT_TOKEN"),
    intents=interactions.Intents.DEFAULT
)


# this code is brought you by a bottle of Henkell Trocken
global model_title
global model_url



import interactions
from interactions import SlashContext

def admin_only():
    async def predicate(ctx: SlashContext):
        guild = ctx.guild
        member = await guild.fetch_member(ctx.author.id)
        if not member:
            await ctx.send("Member not found.", ephemeral=True)
            return False
        if not member.has_permission(interactions.Permissions.ADMINISTRATOR):
            await ctx.send("You do not have permission to use this command.", ephemeral=True)
            return False
        return True
    return interactions.check(predicate)

@interactions.listen()
async def on_startup():
    print("Bot is ready!")

@admin_only()
@slash_command(name="ping", description="Ping the bot", scopes=[GUILD_ID])
async def ping(ctx: SlashContext):
    await ctx.send("Pong!")


@slash_command(name="solve", description="Solve a challenge", scopes=[GUILD_ID])
async def command(ctx: SlashContext):
    solve_modal = Modal(
        ShortText(label="Short Input Text", custom_id="flag"),
        title="Enter the CTF Flag",
        custom_id="solve_modal",
    )
    await ctx.send_modal(modal=solve_modal)

    modal_ctx: ModalContext = await ctx.bot.wait_for_modal(solve_modal)
    flag = modal_ctx.responses["flag"]

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.discord_id == str(ctx.author.id)).first()
        if not user:
            embed = Embed(
                title="Error",
                description="You need to have an account to participate in the CTF.",
                color=0xFF0000
            )
            await modal_ctx.send(embed=embed, ephemeral=True)
            return

        challenge = db.query(Challenge).filter(Challenge.flag == flag).first()
        if not challenge:
            embed = Embed(
                title="Error",
                description="Invalid flag. Please try again.",
                color=0xFF0000
            )
            await modal_ctx.send(embed=embed, ephemeral=True)
            return

        # Check if user has already completed this challenge
        if challenge.id in user.challenges:
            embed = Embed(
                title="Error",
                description="You have already completed this challenge.",
                color=0xFF0000
            )
            await modal_ctx.send(embed=embed, ephemeral=True)
            return

        user_challenges = user.challenges if user.challenges else []
        user_challenges.append(challenge.id)
        user.challenges = user_challenges
        user.score += challenge.points
        db.commit()

        embed = Embed(
            title="Success",
            description=f"Congratulations! You have completed the challenge and earned {challenge.points} points.",
            color=0x00FF00
        )
        await modal_ctx.send(embed=embed, ephemeral=True)

    except Exception as e:
        print(f"An error occurred: {e}")
        embed = Embed(
            title="Error",
            description="An unexpected error occurred. Please try again later.",
            color=0xFF0000
        )
        await modal_ctx.send(embed=embed, ephemeral=True)

    finally:
        db.close()



@slash_command(name="login", description="Login to the CTF platform", scopes=[GUILD_ID])
async def login(ctx: SlashContext):
    embed = Embed(
        title="Login",
        description="Click [here](https://whcc.club/login) to login to the CTF platform.",
        color=0x3498DB
    )
    await ctx.send(embed=embed, ephemeral=True)

@admin_only()

@slash_command(name="new", description="Create a new challenge", scopes=[GUILD_ID])
@slash_option(name="title", description="Title of the challenge", required=True, opt_type=OptionType.STRING)
@slash_option(name="url", description="URL of the challenge", required=True, opt_type=OptionType.STRING)
async def new_challenge(ctx: SlashContext, title: str, url: str):
    global model_title, model_url
    model_title = title
    model_url = url
    challenge_modal = Modal(
        ShortText(label="Description", custom_id="description"),
        ShortText(label="Hint", custom_id="hint"),
        ShortText(label="Flag", custom_id="flag"),
        ShortText(label="Points", custom_id="points"),
        title="Create a New Challenge",
        custom_id="challenge_modal",
    )
    await ctx.send_modal(modal=challenge_modal)


@modal_callback("challenge_modal")
async def on_modal_answer(ctx: interactions.ModalContext, description: str, hint: str, flag: str, points: str):
    global model_title, model_url
    title = model_title
    url = model_url

    db = SessionLocal()
    challenge = Challenge(title=title, description=description, url=url, hint=hint, flag=flag, points=int(points))

    try:
        db.add(challenge)
        db.commit()
        embed = Embed(
            title=f"🚀 {model_title}",
            description=description,
            color=0x3498DB
        )
        embed.add_field(name="**URL:**", value=model_url, inline=False)
        embed.add_field(name="**Hint:**", value=f"||{hint}||", inline=False)
        embed.add_field(name="**Points:**", value=points, inline=False)
        embed.add_field(name="🗓️ Walkthrough:", value="A walkthrough for this challenge will be posted in one week!",
                        inline=False)
        embed.set_footer(text="Good luck!", icon_url="https://example.com/logo.png")

        await ctx.send(embed=embed)

    except Exception as e:
        print(f"An error occurred while creating a new challenge: {e}")
        embed = Embed(
            title="Error",
            description="An error occurred while creating the challenge.",
            color=0xFF0000
        )
        await ctx.send(embed=embed)

    finally:
        db.close()


@slash_command(name="leaderboard", description="Show the leaderboard", scopes=[GUILD_ID])
async def leaderboard(ctx: SlashContext):
    db = SessionLocal()
    try:
        top_users = db.query(User).order_by(User.score.desc()).limit(10).all()

        if not top_users:
            await ctx.send("No users found in the leaderboard.", ephemeral=True)
            return

        embed = Embed(
            title="🏆 Leaderboard",
            description="Top 10 Users",
            color=0xFFD700  # Gold color for the leaderboard ish thing
        )

        for index, user in enumerate(top_users, start=1):
            embed.add_field(
                name=f"{index}. {user.username}",
                value=f"Score: {user.score}",
                inline=False
            )

        await ctx.send(embed=embed)

    except Exception as e:
        print(f"An error occurred while fetching the leaderboard: {e}")
        await ctx.send("An error occurred while fetching the leaderboard.", ephemeral=True)

    finally:
        db.close()


@slash_command(name="help", description="Show the list of available commands", scopes=[GUILD_ID])
async def help_command(ctx: SlashContext):
    embed = Embed(
        title="🤖 Help",
        description="List of Available Commands",
        color=0x3498DB
    )
    embed.add_field(name="/ping", value="Ping the bot", inline=False)
    embed.add_field(name="/solve", value="Solve a challenge", inline=False)
    embed.add_field(name="/login", value="Login to the CTF platform", inline=False)
    embed.add_field(name="/new", value="Create a new challenge", inline=False)
    embed.add_field(name="/leaderboard", value="Show the leaderboard", inline=False)
    await ctx.send(embed=embed)


bot.start()