import discord
from discord.ext import commands
import random
import json
import os
import datetime
from dotenv import load_dotenv

load_dotenv()  # .envファイルの読み込み


bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())

START_BALANCE = 1000
START_BANK = 0

# データ読み込み/保存
def load_data():
    if os.path.exists('data.json'):
        with open('data.json', 'r') as f:
            return json.load(f)
    return {}

def save_data():
    with open('data.json', 'w') as f:
        json.dump(data, f)

data = load_data()

def init_user(user_id):
    if user_id not in data:
        data[user_id] = {
            "wallet": START_BALANCE,
            "bank": START_BANK,
            "daily_bonus": 50,
            "last_daily": None
        }
        save_data()

def get_balance(user_id):
    init_user(user_id)
    return data[user_id]["wallet"]

def get_bank(user_id):
    init_user(user_id)
    return data[user_id]["bank"]

def update_wallet(user_id, amount):
    init_user(user_id)
    data[user_id]["wallet"] += amount
    save_data()

def update_bank(user_id, amount):
    init_user(user_id)
    data[user_id]["bank"] += amount
    save_data()

@bot.event
async def on_ready():
    print(f'ログインしました: {bot.user}')

# 所持金確認
@bot.command()
async def balance(ctx):
    await ctx.send(f"{ctx.author.mention} の所持金: {get_balance(str(ctx.author.id))} コイン")

# 銀行残高確認
@bot.command()
async def bank(ctx):
    await ctx.send(f"{ctx.author.mention} の銀行残高: {get_bank(str(ctx.author.id))} コイン")

# 預け入れ
@bot.command()
async def deposit(ctx, amount: int):
    user_id = str(ctx.author.id)
    if amount <= 0 or get_balance(user_id) < amount:
        return await ctx.send("金額が不正か、所持金が足りません。")
    update_wallet(user_id, -amount)
    update_bank(user_id, amount)
    await ctx.send(f"{amount} コインを銀行に預けました。")

# 引き出し
@bot.command()
async def withdraw(ctx, amount: int):
    user_id = str(ctx.author.id)
    if amount <= 0 or get_bank(user_id) < amount:
        return await ctx.send("金額が不正か、銀行残高が足りません。")
    update_bank(user_id, -amount)
    update_wallet(user_id, amount)
    await ctx.send(f"{amount} コインを銀行から引き出しました。")

# デイリーボーナス
@bot.command()
async def daily(ctx):
    user_id = str(ctx.author.id)
    init_user(user_id)
    last_claim = data[user_id]["last_daily"]

    now = datetime.datetime.now().timestamp()

    if last_claim and now - last_claim < 86400:
        remaining = 86400 - (now - last_claim)
        hours = int(remaining // 3600)
        minutes = int((remaining % 3600) // 60)
        return await ctx.send(f"次のデイリーまで {hours}時間 {minutes}分 残っています。")

    bonus = data[user_id]["daily_bonus"]
    update_wallet(user_id, bonus)
    data[user_id]["daily_bonus"] += 25
    data[user_id]["last_daily"] = now
    save_data()

    await ctx.send(f"🎁 デイリーボーナス！ {bonus} コインを獲得しました！")

# コインフリップ
@bot.command()
async def coinflip(ctx, amount: int, choice: str):
    user_id = str(ctx.author.id)
    if amount <= 0 or get_balance(user_id) < amount:
        return await ctx.send("金額が不正か、所持金が足りません。")
    choice = choice.lower()
    if choice not in ["heads", "tails"]:
        return await ctx.send("heads または tails を指定してください。")
    result = random.choice(["heads", "tails"])
    if result == choice:
        update_wallet(user_id, amount)
        await ctx.send(f"🎉 当たり！ {result} でした！ +{amount}コイン")
    else:
        update_wallet(user_id, -amount)
        await ctx.send(f"😢 はずれ… {result} でした… -{amount}コイン")

# ブラックジャック
@bot.command()
async def blackjack(ctx, amount: int):
    user_id = str(ctx.author.id)
    if amount <= 0 or get_balance(user_id) < amount:
        return await ctx.send("金額が不正か、所持金が足りません。")

    def draw_card():
        return random.randint(1, 11)

    player = [draw_card(), draw_card()]
    dealer = [draw_card(), draw_card()]

    await ctx.send(f"あなたの手札: {player} (合計: {sum(player)})")
    await ctx.send(f"ディーラーの手札: [{dealer[0]}, ?]")

    while sum(player) < 21:
        await ctx.send("ヒットしますか？ (y/n)")
        try:
            msg = await bot.wait_for('message', check=lambda m: m.author == ctx.author, timeout=30.0)
        except:
            break
        if msg.content.lower() == 'y':
            player.append(draw_card())
            await ctx.send(f"あなたの手札: {player} (合計: {sum(player)})")
        else:
            break

    while sum(dealer) < 17:
        dealer.append(draw_card())

    await ctx.send(f"ディーラーの手札: {dealer} (合計: {sum(dealer)})")

    if sum(player) > 21:
        update_wallet(user_id, -amount)
        await ctx.send("バースト！あなたの負けです。")
    elif sum(dealer) > 21 or sum(player) > sum(dealer):
        update_wallet(user_id, amount)
        await ctx.send("あなたの勝ち！")
    elif sum(player) == sum(dealer):
        await ctx.send("引き分けです。")
    else:
        update_wallet(user_id, -amount)
        await ctx.send("あなたの負けです。")

# スロット
@bot.command()
async def slot(ctx, amount: int):
    user_id = str(ctx.author.id)
    if amount <= 0 or get_balance(user_id) < amount:
        return await ctx.send("金額が不正か、所持金が足りません。")
    symbols = ["🍒", "🍋", "🔔", "⭐", "💎"]
    result = [random.choice(symbols) for _ in range(3)]
    await ctx.send(" | ".join(result))

    if len(set(result)) == 1:
        win = amount * 5
        update_wallet(user_id, win)
        await ctx.send(f"🎉 大当たり！ +{win}コイン")
    elif len(set(result)) == 2:
        win = amount * 2
        update_wallet(user_id, win)
        await ctx.send(f"おめでとう！ +{win}コイン")
    else:
        update_wallet(user_id, -amount)
        await ctx.send(f"残念… -{amount}コイン")

# サーバー主限定お金追加
@bot.command()
async def addmoney(ctx, member: discord.Member, amount: int):
    if ctx.author != ctx.guild.owner:
        return await ctx.send("このコマンドはサーバー主のみ使用できます。")
    update_wallet(str(member.id), amount)
    await ctx.send(f"{member.mention} に {amount} コイン追加しました。")

# 他の人にお金を渡す
@bot.command()
async def givemoney(ctx, member: discord.Member, amount: int):
    user_id = str(ctx.author.id)
    if amount <= 0 or get_balance(user_id) < amount:
        return await ctx.send("金額が不正か、所持金が足りません。")
    update_wallet(user_id, -amount)
    update_wallet(str(member.id), amount)
    await ctx.send(f"{ctx.author.mention} が {member.mention} に {amount} コイン渡しました。")
   
load_dotenv()
token = os.getenv("DISCORD_TOKEN")
bot.run(token)


