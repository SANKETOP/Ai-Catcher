import aiosqlite, os, json, asyncio, random, aiohttp, string
from discord.ext import commands, tasks
import numpy as np
from PIL import Image
from io import BytesIO
from tensorflow.keras.models import load_model

TOKEN = os.environ['user_token']
logs_id = os.environ['logs_id']
user_id = os.environ['owner_id']
spam_id = os.environ['spam_id']

bot = commands.Bot(command_prefix='$')

stopped = False
captcha_done = True

loaded_model = load_model('model.h5', compile=False)

def user_only(user_id):
    def predicate(ctx):
        return ctx.author.id == user_id

    return commands.check(predicate)


# Add the check to all commands
@bot.check(user_only(user_id))
async def restrict_commands(ctx):
    return True
bot.remove_command('help')

@bot.command()  #auto Leveling Section
@commands.check(lambda ctx: ctx.author.id == user_id) #only user can use this
async def addpoke(ctx, *args):
    global LevelUp_list
    for arg in args:
        if arg.isdigit():
            LevelUp_list += arg + "\n"
        else:
            await ctx.send(f"{arg} is not a valid pokemon number. Please enter a valid integer number.")
            return
    with open('data/LevelUp', 'w', encoding='utf8') as file:
        file.write(LevelUp_list)
    await asyncio.sleep(3)      
    await ctx.send("Poke data added successfully! they will become Level 100 soon ༼ つ ◕_◕ ༽つ")


@tasks.loop(seconds=random.randint(2, 5)) #Spam Speed Dont make it more Fast
async def spam():
    channel = bot.get_channel(int(spam_id))
    message_length = random.randint(7, 20)  
    message = ''.join(random.choices(string.ascii_letters + string.digits, k=message_length))

    await channel.send(message)


@spam.before_loop
async def before_spam():
    await bot.wait_until_ready()


spam.start()

with open('classes.json', 'r') as f:
    classes = json.load(f)

@bot.event
async def on_ready():
    print('We have logged in as {0.user}'.format(bot))
    bot.db = await aiosqlite.connect("pokemon.db")
    await bot.db.execute(
        "CREATE TABLE IF NOT EXISTS pokies (command str)")
    print("pokies table created!!")
    await bot.db.commit()

@bot.event
async def on_message(message):
    while not hasattr(bot, 'db'):
        await asyncio.sleep(0.1)
    if message.author.id == 716390085896962058:
      if len(message.embeds)>0:
          embed = message.embeds[0]
          if "appeared!" in embed.title :
              cur = await bot.db.execute("SELECT command from pokies")
              res = await cur.fetchone()
              if embed.image:
                  url = embed.image.url
                  async with aiohttp.ClientSession() as session:
                      async with session.get(url=url) as resp:
                          if resp.status == 200:
                              content = await resp.read()
                              image_data = BytesIO(content)
                              image = Image.open(image_data)
                  preprocessed_image = await preprocess_image(image)
                  predictions = loaded_model.predict(preprocessed_image)
                  classes_x = np.argmax(predictions, axis=1)
                  name= list(classes.keys())[classes_x[0]]
                  async with message.channel.typing():
                      await asyncio.sleep(random.randint(3, 6))
                  await message.channel.send(f'<@716390085896962058> c {name} ')
          elif 'human' in content:
                        captchaDm = message.content
                        if logs_id:
                            user = await bot.fetch_user(user_id)
                            if user:
                                channel = await user.create_dm()
                                await channel.send(f"{captchaDm}")
                            await channel.send(
                                f"```Oops! Captcha detected!```\nYour autocatcher was paused because a pending captcha. Check your catch channel and use the command '%captcha_done' to confirm the autocatcher can continue."
                            )      
                    
@bot.command()
async def captcha_done(ctx):
    global captcha_done
    global stopped
    if captcha_done == True:
        await ctx.send("```There aren't any pending captcha!```")

    else:
        await ctx.send(
            "```Captcha confirmed! bot has been reactivated!```")
        stopped = False
        captcha_done = True

async def preprocess_image(image):
    image = image.resize((64, 64))
    image = np.array(image)
    image = image / 255.0
    image = np.expand_dims(image, axis=0)
    return image


bot.run(TOKEN, log_handler=None)