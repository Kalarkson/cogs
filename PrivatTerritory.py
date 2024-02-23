import disnake
import json
import asyncio
from disnake.ext import commands
import io
from PIL import Image, ImageDraw
import random
colors = ['red', 'orange', 'yellow', 'green', 'blue', 'violet', 'white', 'brown', 'pink']

def write_json(filename, content):
    with open(filename, "w") as outfile:
        json.dump(content, outfile, ensure_ascii=True, indent=4)


def load_json(filename):
    with open(filename, encoding="utf-8") as infile:
        return json.load(infile)


class PrivatTerritory(commands.Cog):
    def __init__(self, bot=commands.Bot):
        self.bot = bot
        print('Модуль {} активирован'.format(self.__class__.__name__))

    @commands.command()
    async def add(self, inter, name: str, x1: int, z1: int, r1: int):
        territories = load_json('territories.json')
        territories[str(name)] = {'x': x1, 'z': z1, 'r': r1}
        await inter.send(f"Территория {name} успешно зарегистрирована.")

    @commands.command()
    async def delete(self, inter, name: str):
        territories = load_json('territories.json')
        if name not in territories:
            await inter.send(f"Территории с именем {name} не существует.")
            return
        del territories[str(name)]
        await inter.send(f"Территория {name} успешно удалена.")

    @commands.command()
    async def reg(self, inter, x1: int, z1: int, r1: int):
        territories = load_json('territories.json')
        intersecting_territories = []
        for territory in territories.keys():
            x2 = int(territories[territory]['x'])
            z2 = int(territories[territory]['z'])
            r2 = int(territories[territory]['r'])
            x1_min = x1 - r1
            x1_max = x1 + r1
            z1_min = z1 - r1
            z1_max = z1 + r1
            x2_min = x2 - r2
            x2_max = x2 + r2
            z2_min = z2 - r2
            z2_max = z2 + r2
            if (x1_min <= x2_max and x1_max >= x2_min and z1_min <= z2_max and z1_max >= z2_min):
                intersecting_territories.append(territory)
        if intersecting_territories:
            message = await inter.send(f"Территория пересекается с территориями: {', '.join(intersecting_territories)}")
            thread = await message.create_thread(name='пересечения')
            for intersecting_territory in intersecting_territories:
                x2 = int(territories[str(intersecting_territory)]["x"])
                z2 = int(territories[str(intersecting_territory)]["z"])
                r2 = int(territories[str(intersecting_territory)]["r"])
                min_x1 = x1 - r1
                min_z1 = z1 - r1
                max_x1 = x1 + r1
                max_z1 = z1 + r1
                min_x2 = x2 - r2
                min_z2 = z2 - r2
                max_x2 = x2 + r2
                max_z2 = z2 + r2
                background_width = max(max_x1, max_x2) - min(min_x1, min_x2) + 60
                background_height = max(max_z1, max_z2) - min(min_z1, min_z2) + 60
                background = Image.new('RGB', (background_width, background_height), color='#2b2d31')
                draw = ImageDraw.Draw(background)
                draw.rectangle((x1 - r1 - min(min_x1, min_x2) + 30, z1 - r1 - min(min_z1, min_z2) + 30,
                                x1 + r1 - min(min_x1, min_x2) + 30, z1 + r1 - min(min_z1, min_z2) + 30),
                               outline='green', width=5)
                draw.rectangle((x2 - r2 - min(min_x1, min_x2) + 30, z2 - r2 - min(min_z1, min_z2) + 30,
                                x2 + r2 - min(min_x1, min_x2) + 30, z2 + r2 - min(min_z1, min_z2) + 30),
                               outline='red', width=5)
                image_byte_array = io.BytesIO()
                background.save(image_byte_array, format='PNG')
                image_byte_array.seek(0)
                await thread.send(str(intersecting_territory), file=disnake.File(image_byte_array, filename=f'{intersecting_territory}.png'))
        else:
            components = disnake.ui.ActionRow(
                disnake.ui.Button(
                    style=disnake.ButtonStyle.grey,
                    label='Зарегистрировать территорию.',
                    custom_id=f'terra_{x1}_{z1}_{r1}'
                )
            )
            await inter.send(f"Территория {x1} {z1} не занята.", components=components)

    @commands.Cog.listener()
    async def on_button_click(self, inter: disnake.MessageInteraction):
        if inter.component.custom_id.startswith("terra_"):
            territories = load_json('territories.json')
            x = inter.component.custom_id.split("_")[1]
            z = inter.component.custom_id.split("_")[2]
            r = inter.component.custom_id.split("_")[3]
            await inter.response.send_modal(
                title="Заполните",
                custom_id="name_terra_id",
                components=[
                    disnake.ui.TextInput(
                        label="Введите имя территории",
                        placeholder="Найт-Сити",
                        custom_id="name_terra",
                        style=disnake.TextInputStyle.short
                    )
                ]
            )
            def check_modal_submit(i):
                return i.custom_id == "name_terra_id" and i.author.id == inter.author.id
            try:
                modal_inter = await self.bot.wait_for("modal_submit", check=check_modal_submit, timeout=300)
                name_terra = modal_inter.text_values["name_terra"]
            except asyncio.TimeoutError:
                return
            if str(name_terra) in territories.keys():
                await modal_inter.send(f"Территория с именем {name_terra} уже была зарегистрирована.")
                return
            territories[str(name_terra)] = {'x': x, 'z': z, 'r': r}
            write_json('territories.json', territories)
            await inter.message.edit(components=None)
            await modal_inter.send(f"Территория {name_terra} ({x} {z}) успешно зарегистрирована.")

    @commands.command()
    async def map(self, inter):
        territories = load_json('territories.json')
        background_width = background_height = 5000
        background = Image.new('RGB', (background_width, background_height), color='#2b2d31')
        draw = ImageDraw.Draw(background)
        for territory_id, territory_info in territories.items():
            x = int(territory_info["x"])
            z = int(territory_info["z"])
            r = int(territory_info["r"])
            min_x = x - r
            max_x = x + r
            min_z = z - r
            max_z = z + r
            draw.rectangle((min_x + 2500, min_z + 2500, max_x + 2500, max_z + 2500), outline=random.choice(colors), width=15)
        image_byte_array = io.BytesIO()
        background.save(image_byte_array, format='PNG')
        image_byte_array.seek(0)
        await inter.send("Карта территорий:", file=disnake.File(image_byte_array, filename='territories_map.png'))

    @commands.command()
    async def help(self, inter):
        embed = disnake.Embed(description="""```
----------------
*add(имя x z радиус) команда создаёт территорию с указанным именем на указанных координатах с указанным радиусом
----------------
*delete(имя) команда удаляет территорию с указанным именем
----------------
*reg(x z радиус) команда проверяет влезет ли на указанных координатах территория, в случае если территория не занята предложит зарегистрировать
----------------
*map() команда выводит игровой мир с всеми зарегистрированными территориями
----------------
```""")
        await inter.send(embed=embed)

def setup(bot: commands.Bot):
    bot.add_cog(PrivatTerritory(bot))