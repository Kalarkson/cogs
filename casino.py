import random
import disnake
import json
from disnake.ext import commands


def write_json(filename, content):
    with open(filename, "w") as outfile:
        json.dump(content, outfile, ensure_ascii=True, indent=4)


def load_json(filename):
    with open(filename, encoding="utf-8") as infile:
        return json.load(infile)


def generate_unique_numbers(start, end, n):
    numbers = list(range(start, end + 1))
    random.shuffle(numbers)
    return numbers[:n]


def is_valid_number(s):
    try:
        int(s)
        return True
    except ValueError:
        return False


def examination(var1, var2, var3, var4, var5, var6, var7, var8, var9):
    text = 0
    count_empty = 0
    for var in [var1, var2, var3, var4, var5, var6, var7, var8, var9]:
        if var in ['  ', '00']:
            count_empty += 1
    if str(count_empty) == 8:
        text = 1
    elif var1 == var2 == var3 == var4 == var5 == var6 == var7 == var8 == var9 == '  ':
        text = 2
    return text


class Casino(commands.Cog):
    def __init__(self, bot=commands.Bot):
        self.bot = bot
        print('Модуль {} активирован'.format(self.__class__.__name__))

    def print_ticket(self, amount):

        amount_s = amount

        load = load_json('casino.json')
        tlist = load[str(amount)]["cart"]

        if len(str(amount)) == 3:
            amount = amount
        if len(str(amount)) == 2:
            amount = f'0{amount}'
        if len(str(amount)) == 1:
            amount = f'00{amount}'
        t1 = tlist[0]
        t2 = tlist[1]
        t3 = tlist[2]
        t4 = tlist[27]
        t5 = tlist[28]
        t6 = tlist[29]
        if len(str(tlist[0])) == 1:
            t1 = f'{tlist[0]} '
        if len(str(tlist[1])) == 1:
            t2 = f'{tlist[1]} '
        if len(str(tlist[2])) == 1:
            t3 = f'{tlist[2]} '
        if len(str(tlist[27])) == 1:
            t4 = f'{tlist[27]} '
        if len(str(tlist[28])) == 1:
            t5 = f'{tlist[28]} '
        if len(str(tlist[29])) == 1:
            t6 = f'{tlist[29]} '
        str1 = f' \n        ╓═──═о═──═╖ \n         Лотерейный\n            билет\n        ╚═──═о═──═╝\n \n       ─═ Тираж №1 ═─\n' \
               f' \n \n                 ╒о═о╕\n                  {amount}\n                 ╘о═о╛'
        str2 = """        ─═ Правила ═─
В 1 туре §l§4побеждает§l§r тот, кто §l§4закрыл один любой столбец.§r
Во 2 туре §l§1побеждает§l§r тот, кто §l§1закрыл одно любое поле.§r
В 3 туре §l§6побеждает§l§r тот, кто §l§6закрыл оба поля.§r
Призы выдаются на усмотрение организатора."""
        str3 = f'        ─═ Поле №1 ═─\n     | {t1} |  | {t2} |  | {t3} |\n     | {tlist[3]} |  | {tlist[4]} |  | {tlist[5]} |\n     | {tlist[6]} |  | {tlist[7]} |  | {tlist[8]} |\n' \
               f'     | {tlist[9]} |  | {tlist[10]} |  | {tlist[11]} |\n     | {tlist[12]} |  | {tlist[13]} |  | {tlist[14]} |\n     | {tlist[15]} |  | {tlist[16]} |  | {tlist[17]} |\n     | {tlist[18]} |  | {tlist[19]} |  | {tlist[20]} |\n' \
               f'     | {tlist[21]} |  | {tlist[22]} |  | {tlist[23]} |\n     | {tlist[24]} |  | {tlist[25]} |  | {tlist[26]} |'
        str4 = f'        ─═ Поле №2 ═─\n     | {t4} |  | {t5} |  | {t6} |\n     | {tlist[30]} |  | {tlist[31]} |  | {tlist[32]} |\n     | {tlist[33]} |  | {tlist[34]} |  | {tlist[35]} |\n' \
               f'     | {tlist[36]} |  | {tlist[37]} |  | {tlist[38]} |\n     | {tlist[39]} |  | {tlist[40]} |  | {tlist[41]} |\n     | {tlist[42]} |  | {tlist[43]} |  | {tlist[44]} |\n     | {tlist[45]} |  | {tlist[46]} |  | {tlist[47]} |\n' \
               f'     | {tlist[48]} |  | {tlist[49]} |  | {tlist[50]} |\n     | {tlist[51]} |  | {tlist[52]} |  | {tlist[53]} |'
        str5 = f'Билет {amount_s}'
        # print(str(list))
        embed = disnake.Embed(
            description='Билет создан',
            colour=disnake.Colour.from_rgb(43, 45, 49)
        )
        embed.add_field(name="**Страница 1:**", value=f'```{str1}```', inline=False)
        embed.add_field(name="**Страница 2:**", value=f'```{str2}```', inline=False)
        embed.add_field(name="**Страница 3:**", value=f'```{str3}```', inline=False)
        embed.add_field(name="**Страница 4:**", value=f'```{str4}```', inline=False)
        embed.add_field(name="**Название книги:**", value=f'```{str5}```', inline=False)

        return embed

    @commands.slash_command(name='покупка', description='Зарегистрировать покупку.')
    async def purchase(self,
                       inter: disnake.ApplicationCommandInteraction,
                       member: disnake.Member,
                       number: commands.Range[1, ...]
                       ):
        load = load_json('casino.json')
        try:
            ticket = load[str(number)]
            ticket["member_id"] = member.id
            if member.nick != None:
                fm_nick = member.nick
            else:
                fm_nick = member.name
            ticket["member_nick"] = fm_nick
            write_json('casino.json', load)
            text = f'Пользователь {member.mention} успешно прикреплён к номеру билета.'
        except:
            text = 'Не найден номер билета.'

        await inter.response.send_message(text, ephemeral=True)

    @commands.slash_command(name='билет', description='Создать лотерейный билет.')
    async def casino(self,
                     ctx,
                     number: commands.Range[1, ...] = commands.Param(
                         default=None
                     )):
        if number is not None:
            try:
                embed = self.print_ticket(number)
            except:
                embed = disnake.Embed(description='None')
        else:
            ticket1 = generate_unique_numbers(1, 9, 6)
            ticket2 = generate_unique_numbers(10, 19, 6)
            ticket3 = generate_unique_numbers(20, 29, 6)
            ticket4 = generate_unique_numbers(30, 38, 6)
            ticket5 = generate_unique_numbers(40, 49, 6)
            ticket6 = generate_unique_numbers(50, 59, 6)
            ticket7 = generate_unique_numbers(60, 69, 6)
            ticket8 = generate_unique_numbers(70, 79, 6)
            ticket9 = generate_unique_numbers(80, 89, 6)
            list1 = ticket1[3:] + ticket2[3:] + ticket3[3:] + ticket4[3:] + ticket5[3:] + ticket6[3:] + ticket7[3:] + ticket8[3:] + ticket9[3:]
            indices_to_replace = random.sample(range(len(list1)), 12)
            for index in indices_to_replace:
                list1[index] = '  '
            list2 = ticket1[:3] + ticket2[:3] + ticket3[:3] + ticket4[:3] + ticket5[:3] + ticket6[:3] + ticket7[:3] + ticket8[:3] + ticket9[:3]
            indices_to_replace = random.sample(range(len(list2)), 12)
            for index in indices_to_replace:
                list2[index] = '  '
            tlist = list1 + list2
            load = load_json('casino.json')
            amount = len(load) + 1
            load[str(amount)] = {
                f"member_id": None,
                f"member_nick": None,
                f"cart": tlist
            }
            write_json('casino.json', load)
            embed = self.print_ticket(amount)

        await ctx.send(embed=embed, ephemeral=True)

    @commands.slash_command(name='номер', description='Ввести выпавшее число')
    async def purchase(self,
                       inter: disnake.ApplicationCommandInteraction,
                       number: commands.Range[1, 90]
                       ):
        await inter.response.defer(ephemeral=True)
        embed = disnake.Embed(description='**Итог:**')
        load2 = load_json('kon2.json')
        load = load_json('casino.json')
        load2['gol'].append(number)
        for item in load:
            if load[item]["member_id"] is not None:
                bd = load[item]["cart"]
                for i in range(len(bd)):
                    if is_valid_number(bd[i]) and int(bd[i]) == int(str(number)):
                        bd[i] = '  '
                        bd2 = load[item]["cart"]
                        write_json('casino.json', load)
                        if bd2[24] != 00:
                            text = examination(bd2[0], bd2[3], bd2[6], bd2[9], bd2[12], bd2[15], bd2[18], bd2[21],  bd2[24])
                            if text == 1:
                                embed.add_field(name='', value=f'у игрока <@{load[item]["member_id"]}> сложилась предвыигрышная ситуация', nline=False)
                            if text == 2:
                                embed.add_field(name='', value=f'у игрока <@{load[item]["member_id"]}> заполнен  столбец', inline=False)
                                bd2[24] = '00'
                                load2['1'].append(load[item]["member_nick"])
                        if bd2[25] != 00:
                            text = examination(bd2[1], bd2[4], bd2[7], bd2[10], bd2[13], bd2[16], bd2[19], bd2[22], bd2[25])
                            if text == 1:
                                embed.add_field(name='', value=f'у игрока <@{load[item]["member_id"]}> сложилась предвыигрышная ситуация', inline=False)
                            if text == 2:
                                embed.add_field(name='', value=f'у игрока <@{load[item]["member_id"]}> заполнен  столбец', inline=False)
                                bd2[25] = '00'
                                load2['1'].append(load[item]["member_nick"])
                        if bd2[26] != 00:
                            text = examination(bd2[2], bd2[5], bd2[8], bd2[11], bd2[14], bd2[17], bd2[20], bd2[23], bd2[26])
                            if text == 1:
                                embed.add_field(name='', value=f'у игрока <@{load[item]["member_id"]}> сложилась предвыигрышная ситуация', inline=False)
                            if text == 2:
                                embed.add_field(name='', value=f'у игрока <@{load[item]["member_id"]}> заполнен  столбец', inline=False)
                                bd2[26] = '00'
                                load2['1'].append(load[item]["member_nick"])
                        if bd2[51] != 00:
                            text = examination(bd2[27], bd2[30], bd2[33], bd2[36], bd2[39], bd2[42], bd2[45], bd2[48], bd2[51])
                            if text == 1:
                                embed.add_field(name='', value=f'у игрока <@{load[item]["member_id"]}> сложилась предвыигрышная ситуация', inline=False)
                            if text == 2:
                                embed.add_field(name='', value=f'у игрока <@{load[item]["member_id"]}> заполнен  столбец', inline=False)
                                bd2[51] = '00'
                                load2['1'].append(load[item]["member_nick"])
                        if bd2[52] != 00:
                            text = examination(bd2[28], bd2[31], bd2[34], bd2[37], bd2[40], bd2[43], bd2[46], bd2[49], bd2[52])
                            if text == 1:
                                embed.add_field(name='', value=f'у игрока <@{load[item]["member_id"]}> сложилась предвыигрышная ситуация', inline=False)
                            if text == 2:
                                embed.add_field(name='', value=f'у игрока <@{load[item]["member_id"]}> заполнен  столбец', inline=False)
                                bd2[52] = '00'
                                load2['1'].append(load[item]["member_nick"])
                        if bd2[53] != 00:
                            text = examination(bd2[29], bd2[32], bd2[35], bd2[38], bd2[41], bd2[44], bd2[47], bd2[50], bd2[53])
                            if text == 1:
                                embed.add_field(name='', value=f'у игрока <@{load[item]["member_id"]}> сложилась предвыигрышная ситуация', inline=False)
                            if text == 2:
                                embed.add_field(name='', value=f'у игрока <@{load[item]["member_id"]}> заполнен  столбец', inline=False)
                                bd2[53] = '00'
                                load2['1'].append(load[item]["member_nick"])
                        if bd2[0] != 00:
                            if all(val == '  ' or val == '00' for val in bd2[:27]):
                                embed.add_field(name='', value=f'Первая таблица игрока <@{load[item]["member_id"]}> заполнена', inline=False)
                                bd2[0] = '00'
                                load2['2'].append(load[item]["member_nick"])
                        if bd2[27] != 00:
                            if all(val == '  ' or val == '00' for val in bd2[27:]):
                                embed.add_field(name='', value=f'Вторая таблица игрока <@{load[item]["member_id"]}> заполнена', inline=False)
                                bd2[27] = '00'
                                load2['2'].append(load[item]["member_nick"])
                        if all(value in ['  ', '00'] for value in bd):
                            embed.add_field(name='', value=f'Игрок <@{load[item]["member_id"]}> заполнил обе таблицы', inline=False)
                            bd2[27] = '00'
                            bd2[0] = '00'
                            load2['3'].append(load[item]["member_nick"])
        write_json('casino.json', load)
        write_json('kon2.json', load2)
        await inter.edit_original_response(embed=embed)

def setup(bot):
    bot.add_cog(Casino(bot))