import sqlite3
import string
import json
import asyncio
import random
import math
import time, datetime

import nextcord
import config

from io import BytesIO
from nextcord.ext import commands
from nextcord.ext.commands import has_permissions, has_role, guild_only, BucketType
from nextcord.ui import Button, View
from PIL import Image, ImageChops, ImageDraw, ImageFont
from colorama import Fore, init


bot = commands.Bot(command_prefix='.', intents=nextcord.Intents.all())
bot.remove_command('help')

#FROM CONFIG
xp_multiplier = config.xp_multiplier
users_whitelist = config.users_whitelist
c_info = config.c_info
c_secc = config.c_secc
c_warn = config.c_warn
c_ban = config.c_ban


@bot.event
async def on_ready():
    init(autoreset=True)
    print(Fore.GREEN + 'BOT is on')
    await bot.change_presence(activity=nextcord.Activity(type=nextcord.ActivityType.watching, name=".help"))

    global conn, curs
    conn = sqlite3.connect('discordmaf.db')
    curs = conn.cursor()
    if conn:
        init(autoreset=True)
        print(Fore.GREEN + 'Database connected..')
        print(Fore.RESET + ' ')
    else:
        init(autoreset=True)
        print(Fore.RED + 'Database ERROR!!! Restart bot NOW..')


#ADD USERS TO DB
@bot.event
async def on_member_join(member):
    welcome_mess = config.welcome_mess
    await bot.get_channel(713102228000604272).send(f':wave: {member.mention} {random.choice(welcome_mess)}')
    logf = open('interact_logs.txt', 'a', encoding='utf-8')
    logf.write(f'{datetime.datetime.now().strftime("%d/%m/%Y, %H:%M")} _ {member.id} / {member} вошёл на сервер\n')

    #USERS_PROFILE
    if curs.execute(f' SELECT user_id FROM users_profile WHERE user_id = {member.id}').fetchone() is None:
        curs.execute('INSERT INTO users_profile VALUES(?, ?, ?, ?, ?, ?, ?, ?)',(member.id, 0, 0, 0, 0, 1, 'None', 'None'))
        conn.commit()

    #USERS_BAG
    if curs.execute(f' SELECT user_id FROM users_bag WHERE user_id = {member.id}').fetchone() is None:
        curs.execute('INSERT INTO users_bag VALUES(?, ?, ?)',(member.id, 'No', 'No'))
        conn.commit()
 

#UP LEVEL, XP
@bot.event
async def on_message(message):  
    if not message.author.bot:
        curs.execute(f' UPDATE users_profile SET xp = xp +1 WHERE user_id = {message.author.id}')
        xp = curs.execute(f' SELECT xp FROM users_profile WHERE user_id = {message.author.id}').fetchone()[0]
        lvl = math.sqrt(xp) / xp_multiplier

        if lvl.is_integer():
            curs.execute(f' UPDATE users_profile SET level = ? WHERE user_id = ?', (lvl, message.author.id))

        conn.commit()

    if message.content.startswith('лох'):
        await message.channel.send(f'Сам лох! <:pepejuice:966396070353580063> ')

    #BANWORDS
    if {i.lower().translate(str.maketrans('','', string.punctuation)) for i in message.content.split(' ')}\
    .intersection(set(json.load(open('banwords.json')))) != set():
        await message.channel.send(f'{message.author.mention} больше такое слово не пиши!!', delete_after=8)
        await message.delete()
    
    await bot.process_commands(message)


#ERRORS HANDLER
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
       await ctx.send('У Вас недостаточно прав.')
       init(autoreset=True)
       logf = open('interact_logs.txt', 'a', encoding='utf-8')
       logf.write(f'{datetime.datetime.now().strftime("%d/%m/%Y, %H:%M")} _ {ctx.author.id} / {ctx.author} попытался использовать комманду {str(ctx.message.content)}\n')
    elif isinstance(error, commands.MissingRole):
        await ctx.send('У Вас недостаточно прав.')
        init(autoreset=True)
        logf = open('interact_logs.txt', 'a', encoding='utf-8')
        logf.write(f'{datetime.datetime.now().strftime("%d/%m/%Y, %H:%M")} _ {ctx.author.id} / {ctx.author} попытался использовать комманду {str(ctx.message.content)}\n')
    elif isinstance(error, commands.CommandNotFound):
        await ctx.send('Комманда не найдена, используйте .help')
    elif isinstance(error, commands.CommandOnCooldown):
        cd_error = error.retry_after/60
        embed = nextcord.Embed(
            color = c_ban)
        embed.add_field(name='Недоступно...', value=f'Использовать эту комманду можно раз в {cd_error:.2f} минут <:monkaS:966396341100113981>', inline=False)
        embed.timestamp = datetime.datetime.utcnow()
        await ctx.send(embed=embed)


#-------------------BOT COMMANDS--------------------
#-------------------FOR USERS-----------------------

#PROFILE
def circle(pfp,size = (215,215)):
    
    pfp = pfp.resize(size, Image.Resampling.LANCZOS).convert("RGBA")
    
    bigsize = (pfp.size[0] * 3, pfp.size[1] * 3)
    mask = Image.new('L', bigsize, 0)
    draw = ImageDraw.Draw(mask) 
    draw.ellipse((0, 0) + bigsize, fill=255)
    mask = mask.resize(pfp.size, Image.Resampling.LANCZOS)
    mask = ImageChops.darker(mask, pfp.split()[-1])
    pfp.putalpha(mask)
    return pfp

@guild_only()
@bot.command(aliases=['профиль'])
async def profile(ctx, user:nextcord.User=None):
    if not user:
        user = ctx.author
    elif user.bot:
        return await ctx.send('Нельзя посмотреть профиль этого пользователя')
    name, nick = str(user), user.display_name
    balance = curs.execute(f' SELECT money FROM users_profile WHERE user_id = {user.id}').fetchone()[0]
    level = curs.execute(f' SELECT level FROM users_profile WHERE user_id = {user.id}').fetchone()[0]
    warns = curs.execute(f' SELECT warns FROM users_profile WHERE user_id = {user.id}').fetchone()[0]
    gender = curs.execute(f' SELECT gender FROM users_profile WHERE user_id = {user.id}').fetchone()[0]
    bg = curs.execute(f' SELECT bg FROM users_profile WHERE user_id = {user.id}').fetchone()[0]
    status = curs.execute(f' SELECT status FROM users_profile WHERE user_id = {user.id}').fetchone()[0]
    if gender == 'None':
        gender = '—'
    if status == 'None':
        status = '—'

    base = Image.open('profile/profile.png').convert('RGBA')
    background = Image.open(f'profile/backgrounds/bg{bg}.png').convert('RGBA')
    pfp = user.display_avatar
    data = BytesIO(await pfp.read())
    pfp = Image.open(data).convert('RGBA')
    name = f'{name[:14]}..' if len(name)>16 else name
    nick = f'AKA - {nick[:14]}..' if len(nick)>16 else f'AKA - {nick}'
    draw = ImageDraw.Draw(base)
    pfp = circle(pfp,size=(215,215))
    font = ImageFont.truetype('profile/DejaVuSans.ttf',39)
    akafont = ImageFont.truetype('profile/DejaVuSans.ttf',31)
    boxfont = ImageFont.truetype('profile/DejaVuSans.ttf',30)
    draw.text((24, 380), name, font = font)
    draw.text((386, 455), nick, font = akafont)
    draw.text((130, 620), str(balance), anchor="ms", font = boxfont)
    draw.text((555, 620), str(level), anchor="ms", font = boxfont)
    draw.text((124, 765), str(warns), anchor="ms", font = boxfont)
    draw.text((560, 765), gender, anchor="ms", font = boxfont)
    draw.text((202, 858), status, anchor="ls", font = boxfont)
    base.paste(pfp,(241,133),pfp)
    background.paste(base,(0,0),base)
    with BytesIO() as a:
        background.save(a,'PNG')
        a.seek(0)
        await ctx.send(file = nextcord.File(a,'profile.png'))

#GENDER
@guild_only()
@commands.cooldown(1, 172800, BucketType.user)
@bot.command(aliases=['пол', 'pol'])
async def gender(ctx):
    man = Button(emoji='👨')
    woman = Button(emoji='👩')
    view = View()
    view.add_item(man)
    view.add_item(woman)

    embed=nextcord.Embed(
        title = 'Выберите свой пол',
        description = '_менять пол можно раз в 48 часов_',
        color = c_info)
    embed.timestamp = datetime.datetime.utcnow()
    msg = await ctx.send(embed=embed, view=view)

    async def man_callback(interaction):
        curs.execute(f' UPDATE users_profile SET gender = ? WHERE user_id = ?',('Мужской', ctx.author.id))
        conn.commit()
        embed=nextcord.Embed(
            title = 'Успех!',
            description = 'Теперь Ваш пол: Мужской',
            color = c_secc)
        embed.timestamp = datetime.datetime.utcnow()
        await ctx.send(embed=embed)
        await msg.delete()

    async def woman_callback(interaction):
        curs.execute(f' UPDATE users_profile SET gender = ? WHERE user_id = ?',('Женский', ctx.author.id))
        conn.commit()
        embed=nextcord.Embed(
            title = 'Успех!',
            description = 'Теперь Ваш пол: Женский',
            color = c_secc)
        embed.timestamp = datetime.datetime.utcnow()
        await ctx.send(embed=embed)
        await msg.delete()

    man.callback = man_callback
    woman.callback = woman_callback

#BALANCE
@guild_only()
@bot.command(aliases=['money', 'bal', 'монеты' ,'баланс'])
async def balance(ctx, user:nextcord.Member=None):
    if not user:
        user = ctx.author
    elif user.bot:
        return await ctx.send('Нельзя посмотреть баланс этого пользователя')

    money = curs.execute(f' SELECT money FROM users_profile WHERE user_id = {user.id}').fetchone()[0]
    embed=nextcord.Embed(
        title = user.name,
        description = f'Баланс: **{money}**:moneybag:',
        color = c_info)
    embed.timestamp = datetime.datetime.utcnow()
    await ctx.send(embed=embed)

#LEADERBOARD
@guild_only()
@bot.command(aliases = ['lb', 'топ-монет'])
async def leaderboard(ctx):
    top_balance = curs.execute("SELECT user_id, money FROM users_profile ORDER BY money DESC LIMIT 10")
    com = 0
    a=[]
    for i in top_balance:
        user = await bot.fetch_user(i[0])
        com += 1
        a.append(f'#{com} | `{user.name}` - **{i[1]}** :moneybag:')

    ajoin = "\n".join(a)
    embed = nextcord.Embed(title = 'Топ 10 игроков по монетам', description=ajoin, color=c_info)
    await ctx.send(embed=embed)

#TEST
@guild_only()
@bot.command(aliases=['тест'])
async def test(ctx):
    embed = nextcord.Embed(
        title = 'Бот работает!',
        color = 0x1d241e)
    embed.timestamp = datetime.datetime.utcnow()
    await ctx.send(embed=embed, delete_after=5)
    await ctx.message.delete()

#HELP
@guild_only()
@bot.command(aliases=['помощь', 'хэлп'])
async def help(ctx):
    embed = nextcord.Embed(
        title = 'Информация о сервере собрана в каналах ниже',
        color = c_info)
    embed.add_field(name='Правила сервера:', value='<#704066250803904562>', inline=False)
    embed.add_field(name='Новости:', value='\na', inline=False)
    embed.add_field(name='Комманды бота:', value='\na', inline=False)
    embed.add_field(name='Валюта и уровень:', value='\na', inline=False)
    embed.add_field(name='Список ролей:', value='<#704065088268664942>', inline=False)
    embed.set_footer(text='По всем вопросам к администраторам сервера')
    await ctx.send(embed=embed)

#SERVER
@guild_only()
@bot.command(aliases=['сервер'])
async def server(ctx):
    embed = nextcord.Embed(
        title = 'Статистика сервера',
        color = c_info)
    embed.add_field(name='Название сервера', value=ctx.guild.name, inline=False)
    embed.add_field(name='Сервер создан', value=ctx.guild.created_at.strftime("%A, %d %b, %Y"), inline=False)
    embed.add_field(name='Вы зашли на сервер', value=ctx.author.joined_at.strftime("%A, %d %b, %Y %H:%M"), inline=False)
    embed.add_field(name='Кол-во участников', value=ctx.guild.member_count, inline=False)
    embed.add_field(name='Создатель сервера', value=ctx.guild.owner.mention, inline=False)
    embed.set_thumbnail(url = ctx.guild.icon_url)
    embed.timestamp = datetime.datetime.utcnow()
    await ctx.send(embed=embed)

#ВОПРОС
@guild_only()
@bot.command(aliases=['вопрос', 'задать-вопрос'])
async def question(ctx, *, arg=None):
    answ = ['Да :thumbsup:', 'Нет :thumbsdown:', 'Не знаю <:smoge:966391681278705715>']
    answ1 = random.choice(answ)
    if arg == None:
        await ctx.send(f'{ctx.author.mention} пожалуйста укажите полный вопрос :thinking:')
    else:
        embed=nextcord.Embed(
            title = 'Успех!',
            color = c_secc)
        embed.add_field(name='Вопрос:', value=arg, inline=False)
        embed.add_field(name='Ответ:', value=answ1, inline=False)
        embed.timestamp = datetime.datetime.utcnow()
        await ctx.send(embed=embed)

#RANDOM
@guild_only()
@bot.command(aliases=['random', 'рандом'])
async def randomm(ctx, n: int = None):
    if n is None:
        await ctx.send('Введите количество игроков')
    else:
        nums = []
        for i in range(1,n+1):
            nums.append(str(i))
        random.shuffle(nums)
    
        await ctx.message.delete()
        a = await ctx.send('Генерация чисел...', delete_after=10)
        time.sleep(3)
        await a.add_reaction('✅')

        embed = nextcord.Embed(
            color = c_secc)
        embed.add_field(name='Успех!', value=f'{" ".join(nums)}', inline=False)
        embed.timestamp = datetime.datetime.utcnow()
        await ctx.author.send(embed=embed)

#DAILY-BONUS
@guild_only()
@commands.cooldown(1, 86400, BucketType.user)
@bot.command(aliases=['daily-bonus', 'ежедневный-бонус', 'бонус', 'bonus'])
async def daily_bonus(ctx):
    bonus = random.randint(40,130)
    curs.execute(f' UPDATE users_profile SET money = money + ? WHERE user_id = ?',(bonus, ctx.author.id))
    conn.commit()

    embed = nextcord.Embed(
        title = 'Ежедневный бонус!',
        color = c_secc)
    embed.add_field(name=f'Получено **{bonus}** :moneybag:', value='Следующий бонус будет доступен через 24 часа', inline=False)
    embed.timestamp = datetime.datetime.utcnow()
    await ctx.send(embed=embed)

    logf = open('interact_logs.txt', 'a', encoding='utf-8')
    logf.write(f'{datetime.datetime.now().strftime("%d/%m/%Y, %H:%M")} _ {ctx.author.id} / {ctx.author} собрал дневной бонус в размере {bonus} монет\n')

#ACTIVATE PROMOCODE
@guild_only()
@commands.cooldown(1, 1200, BucketType.user)
@bot.command(aliases=['promo', 'промокод', 'промо'])
async def promocode(ctx, promo_name: int=None):
    try:
        if promo_name is None:
            await ctx.send('Вы не ввели промокод')
        else:
            activate = conn.execute(F' SELECT activate FROM promocodes WHERE name = {promo_name} ').fetchone()[0]
            if activate <= 0:
                await ctx.send('Количество активаций промокода исчерпано')
            else:
                cmoney = curs.execute(f' SELECT count_money FROM promocodes WHERE name = {promo_name}').fetchone()[0]
                curs.execute(f' UPDATE promocodes SET activate = activate -1 WHERE name = {promo_name}')
                curs.execute(f' UPDATE users_profile SET money = money + ? WHERE user_id = ?',(cmoney, ctx.author.id))
                conn.commit()

                embed = nextcord.Embed(
                    title = 'Успех!',
                    color = c_secc)
                embed.add_field(name='Активированый промокод:', value=promo_name, inline=False)
                embed.add_field(name='Вы получили:', value=f'**{cmoney}** :moneybag:', inline=False)
                embed.timestamp = datetime.datetime.utcnow()
                await ctx.send(embed=embed)

                logf = open('interact_logs.txt', 'a', encoding='utf-8')
                logf.write(f'{datetime.datetime.now().strftime("%d/%m/%Y, %H:%M")} _ {ctx.author.id} / {ctx.author} активировал промокод {promo_name} и получил {cmoney} монет\n')
    except:
        await ctx.send('Промокода не существует либо колличество его активаций исчерпано <:sadge:966387808346443886>')
        logf = open('interact_logs.txt', 'a', encoding='utf-8')
        logf.write(f'{datetime.datetime.now().strftime("%d/%m/%Y, %H:%M")} _ {ctx.author.id} / {ctx.author} не активировал промокод из-за ошибки\n')

#STATUS
@guild_only()
@bot.command(aliases=['статус'])
async def status(ctx):
    status_buy = curs.execute(f'SELECT status_buy FROM users_bag WHERE user_id = {ctx.author.id}').fetchone()[0]

    if status_buy == 'No':
        embed = nextcord.Embed(title='Ошибка ❌', description='У Вас не куплена возможность менять статус\nПриобрести можно в .shop', color=c_ban)
        embed.timestamp = datetime.datetime.utcnow()
        await ctx.send(embed=embed)
    elif status_buy == 'Yes':
        question = ['Введите Ваш новый статус длиной до 22 символов. Помните, что нужно соблюдать <#704066250803904562>']

        answers = []

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        for i in question:
            await ctx.send(i) 

            try:
                msg = await bot.wait_for('message', timeout=80.0, check=check)
            except asyncio.TimeoutError:
                await ctx.send('Вы не вписали статус. Попробуйте заново и в этот раз будьте быстрее')
                return
            else:
                answers.append(msg.content)

        newstatus = answers[0][:22]
        curs.execute('UPDATE users_profile SET status = ? WHERE user_id = ?',(newstatus, ctx.author.id))
        conn.commit()

        embed = nextcord.Embed(
            title='Успешно!', 
            description=f'Ваш новый статус:\n{newstatus}',
            color=c_secc)
        embed.timestamp = datetime.datetime.utcnow()
        await ctx.send(embed=embed)

        logf = open('interact_logs.txt', 'a', encoding='utf-8')
        logf.write(f'{datetime.datetime.now().strftime("%d/%m/%Y, %H:%M")} _ {ctx.author.id} / {ctx.author} изменил статус профиля на - {newstatus}\n')
    else:
        await ctx.send('Неизвестная ошибка! Обратитесь к администрации сервера')
        logf = open('interact_logs.txt', 'a', encoding='utf-8')
        logf.write(f'{datetime.datetime.now().strftime("%d/%m/%Y, %H:%M")} _ {ctx.author.id} / {ctx.author} не смог изменить статус из-за ошибки\n')

#BACKGROUND
@guild_only()
@bot.command(aliases=['bg','бг'])
async def background(ctx):
    bg_buy = curs.execute(f'SELECT bg_buy FROM users_bag WHERE user_id = {ctx.author.id}').fetchone()[0]

    if bg_buy == 'No':
        embed = nextcord.Embed(title='Ошибка ❌', description='У Вас не куплена возможность изменять задний фон профиля\nПриобрести можно в .shop', color=c_ban)
        embed.timestamp = datetime.datetime.utcnow()
        await ctx.send(embed=embed)
    elif bg_buy == 'Yes':
        question = ['Посмотреть фоны можно в <#713109238968352869>']
        answers = []

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        for i in question:
            embed = nextcord.Embed(title='Выберите фон и впишите его номер в чат', 
                description=i, color=0x800080)
            await ctx.send(embed=embed)

            try:
                msg = await bot.wait_for('message', timeout=50.0, check=check)
            except asyncio.TimeoutError:
                await ctx.send('Вы не успели с выбором. Попробуйте заново и в этот раз будьте быстрее')
                return
            else:
                answers.append(msg.content)

        try:
            newbg = int(answers[0])
        except:
            await ctx.send('Чтобы установить задний фон, нужно вписать его номер из списка')
            return

        if newbg <= 0:
            await ctx.send('Такого номера нет в списке')
            return
        elif newbg <= 11:
            curs.execute('UPDATE users_profile SET bg = ? WHERE user_id = ?',(newbg, ctx.author.id))
            conn.commit()
        else:
            await ctx.send('Такого номера нет в списке')
            return

        embed = nextcord.Embed(
            title='Успешно!', 
            description=f'Задний фон профиля под номером {newbg} установлен',
            color=c_secc)
        embed.timestamp = datetime.datetime.utcnow()
        await ctx.send(embed=embed)
    else:
        await ctx.send('Неизвестная ошибка! Обратитесь к администрации сервера')
        logf = open('interact_logs.txt', 'a', encoding='utf-8')
        logf.write(f'{datetime.datetime.now().strftime("%d/%m/%Y, %H:%M")} _ {ctx.author.id} / {ctx.author} не смог изменить задний фон из-за ошибки\n')

#SHOP
@guild_only()
@bot.command(aliases=['магазин'])
async def shop(ctx):
    #ITEM PRICE
    statusp = curs.execute("SELECT price FROM shop WHERE name = 'status'").fetchone()[0]
    bgp = curs.execute("SELECT price FROM shop WHERE name = 'bg'").fetchone()[0]
    usermoney = curs.execute(f'SELECT money FROM users_profile WHERE user_id = {ctx.author.id}').fetchone()[0]

    #MAIN PAGE SHOP
    firtsitem = Button(emoji='1️⃣')
    seconditem = Button(emoji='2️⃣')
    view = View()
    view.add_item(firtsitem)
    view.add_item(seconditem)

    #ITEM1 PAGE SHOP
    successfirst = Button(emoji='✅')
    cancel1 = Button(emoji='❌')
    view2 = View()
    view2.add_item(successfirst)
    view2.add_item(cancel1)

    #ITEM2 PAGE SHOP
    successcesond = Button(emoji='✅')
    cancel2 = Button(emoji='❌')
    view3 = View()
    view3.add_item(successcesond)
    view3.add_item(cancel2)

    embed = nextcord.Embed(
            title = 'Магазин',
            color = c_info)
    embed.add_field(name=f'1. Статус - **{statusp}** :moneybag:', value='_Возможность задавать статус в профиле_', inline=False)
    embed.add_field(name=f'2. Задний фон профиля - **{bgp}** :moneybag:', value='_Возможность менять задний фон профиля_', inline=False)
    msg = await ctx.send(embed=embed, view=view)

    async def firstitem_callback(interaction):
        embed=nextcord.Embed(
            title = 'Подтвердить покупку?',
            color = c_info)
        embed.add_field(name=f'Статус - **{statusp}** :moneybag:', value='_Возможность задавать статус в профиле_', inline=False)
        global msgi
        msgi = await ctx.send(embed=embed, view=view2)
        await msg.delete()

    async def seconditem_callback(interaction):
        embed=nextcord.Embed(
            title = 'Подтвердить покупку?',
            color = c_info)
        embed.add_field(name=f'Задний фон профиля - **{bgp}** :moneybag:', value='_Возможность менять задний фон профиля_', inline=False)
        global msgi
        msgi = await ctx.send(embed=embed, view=view3)
        await msg.delete()

    async def successfirst_callback(interaction):
        if usermoney < statusp:
            await ctx.send('Недостаточно денег для покупки')
            await msgi.delete()
        else:
            curs.execute('UPDATE users_profile SET money = money - ? WHERE user_id = ?',(statusp, ctx.author.id))
            curs.execute('UPDATE users_bag SET status_buy = ? WHERE user_id = ?',('Yes', ctx.author.id))
            conn.commit()
            embed=nextcord.Embed(
                title = 'Покупка совершена',
                color = c_secc)
            embed.add_field(name='Теперь у Вас есть возможность задать статус профиля', value='_используйте .статус_', inline=False)
            embed.timestamp = datetime.datetime.utcnow()
            await ctx.send(embed=embed)
            await msgi.delete()
        
    async def successsecond_callback(interaction):
        if usermoney < bgp:
            await ctx.send('Недостаточно денег для покупки')
            await msgi.delete()
        else:
            curs.execute('UPDATE users_profile SET money = money - ? WHERE user_id = ?',(bgp, ctx.author.id))
            curs.execute('UPDATE users_bag SET bg_buy = ? WHERE user_id = ?',('Yes', ctx.author.id))
            conn.commit()
            embed=nextcord.Embed(
                title = 'Покупка совершена',
                color = c_secc)
            embed.add_field(name='Теперь у Вас есть возможность изменить задний фон профиля', value='_используйте .bg_', inline=False)
            embed.timestamp = datetime.datetime.utcnow()
            await ctx.send(embed=embed) 
            await msgi.delete()
        
    async def cancel_callback(interaction):
        embed=nextcord.Embed(
            title = 'Отмена покупки ❌',
            color = c_ban)
        embed.timestamp = datetime.datetime.utcnow()
        await ctx.send(embed=embed)
        await msgi.delete()       

    firtsitem.callback = firstitem_callback
    seconditem.callback = seconditem_callback
    successfirst.callback = successfirst_callback
    successcesond.callback = successsecond_callback
    cancel1.callback = cancel_callback
    cancel2.callback = cancel_callback



#-------------------FOR ADMINS/MODERS-----------------------


#WARN
@guild_only()
@has_permissions(kick_members=True)
@bot.command(aliases=['варн', 'предупреждение'])
async def warn(ctx, user:nextcord.Member = None, *, reason = None):
    if user is None:
        await ctx.send('Введите пользователя которому нужно выдать предупреждение')
    elif reason is None: 
        await ctx.send('Введите причину предупреждения')    
    elif user.bot:
        await ctx.send('Вы не можете выдать предупреждение этому пользователю') 
    else:
        role = nextcord.utils.get(ctx.guild.roles, name="🍀")
        if role in user.roles:
            await ctx.send('Вы не можете выдать предупреждение этому пользователю')

            logf = open('interact_logs.txt', 'a', encoding='utf-8')
            logf.write(f'{datetime.datetime.now().strftime("%d/%m/%Y, %H:%M")} _ {ctx.author.id} / {ctx.author} пытался выдать варн - {user.id} / {user} по причине - {reason}. Но наткнулся на клевер\n')
        else:
            curs.execute(f' UPDATE users_profile SET warns = warns +1 WHERE user_id = {user.id}')
            warncount = curs.execute(f' SELECT warns FROM users_profile WHERE user_id = {user.id}').fetchone()[0]
            conn.commit()

            embed = nextcord.Embed(
                title = 'Успех!',
                color = c_warn)
            embed.add_field(name='Администратор', value=ctx.author.mention, inline=False)
            embed.add_field(name='Выдал предупреждение', value=user.mention, inline=False)
            embed.add_field(name='По причине: ', value=reason, inline=False)
            embed.add_field(name='Количество предупреждений', value=warncount, inline=False)
            embed.timestamp = datetime.datetime.utcnow()
            await ctx.send(embed=embed) 

            logf = open('interact_logs.txt', 'a', encoding='utf-8')
            logf.write(f'{datetime.datetime.now().strftime("%d/%m/%Y, %H:%M")} _ {ctx.author.id} / {ctx.author} выдал варн - {user.id} / {user} по причине - {reason}\n')

#UNWARN
@guild_only()
@has_permissions(kick_members=True)
@bot.command(aliases=['унварн'])
async def unwarn(ctx, user:nextcord.Member = None):
    if user is None:
        await ctx.send('Введите пользователя у которого нужно снять предупреждение')
    elif user.bot:
        await ctx.send('Вы не можете снять предупреждение у этого пользователя')  
    elif user == ctx.author:
        await ctx.send('Нельзя снять предупреждение самому себе, обратитесь к администрации')
        logf = open('interact_logs.txt', 'a', encoding='utf-8')
        logf.write(f'{datetime.datetime.now().strftime("%d/%m/%Y, %H:%M")} _ {ctx.author.id} / {ctx.author} пытался снять варн у самого себя\n')
    else:
        warncount = curs.execute(f' SELECT warns FROM users_profile WHERE user_id = {user.id}').fetchone()[0]
        if warncount == 0:
            await ctx.send('У этого пользователя 0 предупреждений')

            logf = open('interact_logs.txt', 'a', encoding='utf-8')
            logf.write(f'{datetime.datetime.now().strftime("%d/%m/%Y, %H:%M")} _ {ctx.author.id} / {ctx.author} пытался снять варн - {user.id} / {user}. Но у него 0 варнов\n')  
        else:
            curs.execute(f' UPDATE users_profile SET warns = warns -1 WHERE user_id = {user.id}')
            warncount = curs.execute(f' SELECT warns FROM users_profile WHERE user_id = {user.id}').fetchone()[0]
            conn.commit()

            embed = nextcord.Embed(
                title = 'Успех!',
                color = c_warn)
            embed.add_field(name='Администратор', value=ctx.author.mention, inline=False)
            embed.add_field(name='Снял предупреждение', value=user.mention, inline=False)
            embed.add_field(name='Количество предупреждений', value=warncount, inline=False)
            embed.timestamp = datetime.datetime.utcnow()
            await ctx.send(embed=embed) 

            logf = open('interact_logs.txt', 'a', encoding='utf-8')
            logf.write(f'{datetime.datetime.now().strftime("%d/%m/%Y, %H:%M")} _ {ctx.author.id} / {ctx.author} снял варн - {user.id} / {user}\n')

#KICK
@guild_only()
@has_permissions(kick_members=True)  
@bot.command(aliases=['кик'])
async def kick(ctx, user:nextcord.Member = None, *, reason = None):
    if user is None:
        await ctx.send('Выберите пользователя которого нужно выгнать')
    elif reason is None:
        await ctx.send('Введите причину кика')
    elif user.bot:
        await ctx.send('Вы не можете выгнать этого пользователя')  
    elif user == ctx.author:
        await ctx.send('Вы не можете выгнать самого себя')
    else:
        role = nextcord.utils.get(ctx.guild.roles, name="🍀")
        if role in user.roles:
            await ctx.send('Вы не можете выгнать этого пользователя')

            logf = open('interact_logs.txt', 'a', encoding='utf-8')
            logf.write(f'{datetime.datetime.now().strftime("%d/%m/%Y, %H:%M")} _ {ctx.author.id} / {ctx.author} пытался кикнуть - {user.id} / {user} по причине - {reason}. Но наткнулся на клевер\n')
        else:
            embed = nextcord.Embed(
                title = 'Успех!',
                color = c_ban)
            embed.add_field(name='Администратор', value=ctx.author.mention, inline=False)
            embed.add_field(name='Выгнал с сервера', value=user.mention, inline=False)
            embed.add_field(name='По причине: ', value=reason, inline=False)
            embed.timestamp = datetime.datetime.utcnow()
            await ctx.send(embed=embed) 
            await user.kick(reason=reason)

            logf = open('interact_logs.txt', 'a', encoding='utf-8')
            logf.write(f'{datetime.datetime.now().strftime("%d/%m/%Y, %H:%M")} _ {ctx.author.id} / {ctx.author} кикнул - {user.id} / {user} по причине - {reason}\n')
    
#BAN
@guild_only()
@has_permissions(kick_members=True)
@bot.command(aliases=['бан'])
async def ban(ctx, user:nextcord.Member = None, *, reason = None):
    if user is None:
        await ctx.send('Выберите пользователя которого нужно забанить')
    elif reason is None:
        await ctx.send('Введите причину бана')
    elif user.bot:
        await ctx.send('Вы не можете забанить этого пользователя')  
    elif user == ctx.author:
        await ctx.send('Вы не можете забанить самого себя')
    else:
        role = nextcord.utils.get(ctx.guild.roles, name="🍀")
        if role in user.roles:
            await ctx.send('Вы не можете забанить этого пользователя')

            logf = open('interact_logs.txt', 'a', encoding='utf-8')
            logf.write(f'{datetime.datetime.now().strftime("%d/%m/%Y, %H:%M")} _ {ctx.author.id} / {ctx.author} пытался забанить - {user.id} / {user} по причине - {reason}. Но наткнулся на клевер\n')
        else:
            embed = nextcord.Embed(
                title = 'Успех!',
                color = c_ban)
            embed.add_field(name='Администратор', value=ctx.author.mention, inline=False)
            embed.add_field(name='Забанил', value=user.mention, inline=False)
            embed.add_field(name='По причине: ', value=reason, inline=False)
            embed.timestamp = datetime.datetime.utcnow()
            await ctx.send(embed=embed) 
            await user.ban(reason=reason)

            logf = open('interact_logs.txt', 'a', encoding='utf-8')
            logf.write(f'{datetime.datetime.now().strftime("%d/%m/%Y, %H:%M")} _ {ctx.author.id} / {ctx.author} забанил - {user.id} / {user} по причине - {reason}\n')

#UNBAN
@guild_only()
@bot.command(aliases=['унбан', 'разбан'])
async def unban(ctx):
    await ctx.send('Для разбана обратитесь к администрации') 

    logf = open('interact_logs.txt', 'a', encoding='utf-8')
    logf.write(f'{datetime.datetime.now().strftime("%d/%m/%Y, %H:%M")} _ {ctx.author.id} / {ctx.author} получил информацию о разбане\n')

#GIVE MONEY
@guild_only()
@has_permissions(administrator=True)
@bot.command(aliases=['дать-денег', 'выдать-денег', 'дать-баланс', 'give-balance', 'give-money'])
async def give_money(ctx, user:nextcord.Member = None, amount: int = None):
    if user is None:
        await ctx.send('Укажите пользователя которому желаете выдать денег')
    elif amount is None or amount <= 0:
        await ctx.send('Введите суму больше 0')   
    elif user.bot:
        await ctx.send('Вы не можете выдать денег этому пользователю')
    else:
        curs.execute(' UPDATE users_profile SET money = money + ? WHERE user_id = ?', (amount, user.id))
        new_bal = curs.execute(f' SELECT money FROM users_profile WHERE user_id = {user.id}').fetchone()[0]
        conn.commit()

        embed = nextcord.Embed(
            title = 'Успех!',
            color = c_secc)
        embed.add_field(name=f'Пользователю {user.name} было выдано **{amount}** :moneybag:!',\
        value=f'Теперь баланс {user.mention} - {new_bal} :moneybag:', inline=False)
        embed.timestamp = datetime.datetime.utcnow()
        await ctx.send(embed=embed)

        logf = open('interact_logs.txt', 'a', encoding='utf-8')
        logf.write(f'{datetime.datetime.now().strftime("%d/%m/%Y, %H:%M")} _ {ctx.author.id} / {ctx.author} выдал - {user.id} / {user} - {amount} монет\n')

#TAKE MONEY
@guild_only()
@has_permissions(administrator=True)
@bot.command(aliases=['забрать-денег', 'забрать-денеги', 'забрать-баланс', 'take-balance', 'take-money'])
async def take_money(ctx, user:nextcord.Member = None, amount: int = None):
    if user is None:
        await ctx.send('Укажите пользователя у которого нужно забрать денеги')
    elif amount is None or amount <= 0:
        await ctx.send('Введите суму больше 0')        
    elif user.bot:
        await ctx.send('Вы не можете забрать деньги у этого пользователя')
    else:
        bal = curs.execute(f' SELECT money FROM users_profile WHERE user_id = {user.id}').fetchone()[0]
        if amount > bal:
            await ctx.send(f'Нельзя забрать больше денег чем есть у пользователя.\nЕго баланс {bal}')

            logf = open('interact_logs.txt', 'a', encoding='utf-8')
            logf.write(f'{datetime.datetime.now().strftime("%d/%m/%Y, %H:%M")} _ {ctx.author.id} / {ctx.author} пытался забрать у - {user.id} / {user} - {amount} монет. Но у него всего {bal}\n')
        else:
            curs.execute(' UPDATE users_profile SET money = money - ? WHERE user_id = ?', (amount, user.id))
            new_bal = curs.execute(f' SELECT money FROM users_profile WHERE user_id = {user.id}').fetchone()[0]
            conn.commit()

            embed = nextcord.Embed(
                title = 'Успех!',
                color = c_secc)
            embed.add_field(name=f'У пользователя {user.name} забрали **{amount}** :moneybag:!',\
            value=f'Теперь баланс {user.mention} - {new_bal} :moneybag:', inline=False)
            embed.timestamp = datetime.datetime.utcnow()
            await ctx.send(embed=embed) 

            logf = open('interact_logs.txt', 'a', encoding='utf-8')
            logf.write(f'{datetime.datetime.now().strftime("%d/%m/%Y, %H:%M")} _ {ctx.author.id} / {ctx.author} забрал у - {user.id} / {user} - {amount} монет\n')

#CLEAR
@guild_only()
@has_role(970344029780836352)
@bot.command(aliases=['очистка', 'chat-clear'])
async def clear(ctx, count: int=None):
    if count is None:
        await ctx.send('Введите количество сообщений которое нужно удалить')
    else:
        await ctx.channel.purge(limit=count+1)
        embed = nextcord.Embed(
            title = 'Успех!',
            description=f'Было удалено {count} сообщений',
            color = c_secc)
        embed.timestamp = datetime.datetime.utcnow()
        await ctx.send(embed=embed, delete_after=3)

#BOT-STATUS
@guild_only()
@has_role(970344029780836352)
@bot.command(aliases=['presens', 'пресенс', 'бот-статус', 'bot-status'])
async def bot_status(ctx, newst=None):
    if newst is None:
        await ctx.send('Введите новый статус бота')
    else:
        await bot.change_presence(activity=nextcord.Activity(type=nextcord.ActivityType.watching, name=newst))
        embed = nextcord.Embed(title='Успех!',
        color=c_secc,
        description=f'Установлен статус - Смотрит {newst}')
        await ctx.send(embed=embed)

        logf = open('interact_logs.txt', 'a', encoding='utf-8')
        logf.write(f'{datetime.datetime.now().strftime("%d/%m/%Y, %H:%M")} _ {ctx.author.id} / {ctx.author} изменил статус бота на - {newst}\n')

#CREATE-PROMOCODE
@guild_only()
@has_permissions(administrator=True)
@bot.command(aliases=['create-promocode', 'create-promo', 'создать-промокод'])
async def create_promocode(ctx, count_money: int=None, activate: int=None):
    if count_money is None:
        await ctx.send('Используйте .create-promocode <количество монет> <количество активаций>')
    elif activate is None:
        await ctx.send('Используйте .create-promocode <количество монет> <количество активаций>')   
    else:
        try:
            promo_name = random.randint(10000000, 99999999)
            curs.execute('INSERT INTO promocodes VALUES(?, ?, ?)',(promo_name, count_money, activate))
            conn.commit()
            await ctx.message.add_reaction('✅')
            await ctx.author.send(f'Промокод создан - {promo_name}, количество активаций - {activate}')

            logf = open('interact_logs.txt', 'a', encoding='utf-8')
            logf.write(f'{datetime.datetime.now().strftime("%d/%m/%Y, %H:%M")} _ {ctx.author.id} / {ctx.author} создал промокод {promo_name}\n')
        except:
            await ctx.send('Произошла ошибка, попробуйте ещё раз <:sadge:966387808346443886>')
            logf = open('interact_logs.txt', 'a', encoding='utf-8')
            logf.write(f'{datetime.datetime.now().strftime("%d/%m/%Y, %H:%M")} _ {ctx.author.id} / {ctx.author} не смог создать промокод из-за ошибки\n')

#PROMOCODE-LIST
@guild_only()
@has_permissions(administrator=True)
@bot.command(aliases=['promo-list', 'promocode-list', 'plist', 'список-промо', 'список-промокодов'])
async def promo_list(ctx):
    embed = nextcord.Embed(title = 'Список промокодов')
    for i in curs.execute(f' SELECT name, count_money, activate FROM promocodes'):
        embed.add_field(
            name=i[0],
            value=f'денег за активацию - {i[1]}; количество активация - {i[2]}',
            inline=False)
    await ctx.message.add_reaction('✅')
    await ctx.author.send(embed=embed)

    logf = open('interact_logs.txt', 'a', encoding='utf-8')
    logf.write(f'{datetime.datetime.now().strftime("%d/%m/%Y, %H:%M")} _ {ctx.author.id} / {ctx.author} получил список промокодов\n')

#GIVEAWAY
def convert(time):
    pos = ['s','m','h','d']
    time_dict = {'s' : 1, 'm' : 60, 'h' : 3600, 'd' : 3600*24}
    unit = time[-1]

    if unit not in pos:
        return -1
    try:
        val = int(time[:-1])
    except:
        return -2
    
    return val * time_dict[unit]


@guild_only()
@has_role(970344029780836352)
@bot.command(aliases=['гив', 'розыгрыш'])
async def giveaway(ctx):
    await ctx.send('Создания розыгрыша...')

    question = ['В каком канале будет проходить розыгрыш',
                'Сколько времени он будет длится? (s|m|h|d)',
                'Количество :moneybag: в призе?']

    answers = []

    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel

    for i in question:
        await ctx.send(i)

        try:
            msg = await bot.wait_for('message', timeout=20.0, check=check)
        except asyncio.TimeoutError:
            await ctx.send('❌ Вы не успели вписать ответ, пожалуйста повторите попытку')
            return
        else:
            answers.append(msg.content)

    try:
        c_id = int(answers[0][2:-1])
    except:
        await ctx.send(f'Вы должны упомянуть канал для розыгрыша. Пример {ctx.channel.mention}')
    channel = bot.get_channel(c_id)

    time = convert(answers[1])
    if time == -1:
        await ctx.send('Введите время в правильном формате используя s|m|h|d')
        return
    elif time == -2:
        await ctx.send('Введите время в правильном формате используя s|m|h|d')
        return
    prize = answers[2]

    await ctx.send(f'Розыгрыш пройдет в канале {channel.mention} с призом {prize} и продлится {answers[1]}')
    embed = nextcord.Embed(
        title='Розыгрыш!', 
        description=f'Приз - **{prize}** :moneybag:',
        color=0xe4f312)
    embed.set_footer(text=f'Продлится {answers[1]}')
    await channel.send('@here')
    my_msg = await channel.send(embed=embed)
    await my_msg.add_reaction('🎉')

    logf = open('interact_logs.txt', 'a', encoding='utf-8')
    logf.write(f'{datetime.datetime.now().strftime("%d/%m/%Y, %H:%M")} _ {ctx.author.id} / {ctx.author} создал гив в канале {channel.id} с призом {prize} который продлится {answers[1]}\n')

    await asyncio.sleep(time)

    new_msg = await channel.fetch_message(my_msg.id)
    users = await new_msg.reactions[0].users().flatten()
    users.pop(users.index(bot.user))

    winner = random.choice(users)
    curs.execute('UPDATE users_profile SET money = money + ? WHERE user_id = ?',(prize, winner.id))
    conn.commit()
    await channel.send(f'{winner.mention} - победитель розыгрыша. Он получает **{prize}** :moneybag:')

    logf = open('interact_logs.txt', 'a', encoding='utf-8')
    logf.write(f'{datetime.datetime.now().strftime("%d/%m/%Y, %H:%M")} _ {winner.id} / {winner} победил в гиве и получил {prize} монет\n')


















        



if __name__ == "__main__":
    bot.run(config.TOKEN)