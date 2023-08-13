"""
Walker bot module
"""
import json
import random
import sys

from .books import WalkerBooks
from .captcha2 import *
from .classes import SellerItem, WalkerFight, AUHelper
from .doors import WalkerDoors
from .engine import *


class Walker(Engine):
    """ Движок обработки команд """

    # Текущая версия
    VERSION = 3.21

    # Идентификатор игрового бота
    GAME_BOT_ID = -182985865

    API_URL = "https://vip3.activeusers.ru/app.php?act=%s&auth_key=%s&group_id=182985865&api_id=7055214"
    ACT_TYPE_PAGE = "pages&id=%s"
    ACT_TYPE_ITEM = "item&id=%s"
    ACT_TYPE_USER = "user"
    API_PAGE_STAT = 615
    API_PAGE_REP = 616

    # Состояние неизвестно
    STATE_NONE = 0
    # В бою
    STATE_BATTLE = 1
    # В комнате
    STATE_EXPLORE = 2
    # В походе
    STATE_OUTDOOR = 3
    # Идем сдавать трофеи и шкуры
    STATE_DUMP = 4
    # Сдача трофеев
    STATE_HUNTER_TROPH = 5
    # Покушать
    STATE_HONGER = 6
    # Ночной отдых
    STATE_SLEEP = 7

    # Дропа нет
    DROP_NONE = 0
    # Дроп с ожиданием
    DROP_WAIT = 1
    # Дроп без ожидания
    DROP_SKIP = 2

    def __init__(self, config: callable, name: str):
        """ Конструктор """
        super().__init__(config(), name)
        self.active = True
        self.skipBattle = False
        self.nextLevel = False
        self.nextWay = None
        self.trade = None
        self.fight = WalkerFight()
        self.captcha = WalkerCaptcha(os.getcwd() + "/sources/captcha/v2/")
        self.books = WalkerBooks(self.sendAction, self.addrule)
        self.books = WalkerDoors(self.sendAction, self.addrule, self.doWaitRes, self.config)
        self.channel = self.GAME_BOT_ID
        self.drop = self.DROP_NONE
        self.state = self.STATE_NONE
        self.retry = ""
        self.answer = ""
        self.wing = ""
        self.match = []
        self.sells = {}
        self.transfers = {}
        self.actions = {}
        self.tasksList = []
        self.tasksCount = 0
        self.tasksDone = False
        self.tasksDecline = False
        self.injuries = 0
        self.cloaks = 0
        self.speed = 100
        self.honger = 100
        self.hongerTime = datetime.min
        self.inventory = 100
        self.troph = 0
        self.reputation = 0
        self.labData = []
        self.labX = 0
        self.labY = 0
        self.apiInjur = self.compile(r"7c441f6b.+?(\d+)")
        self.apiTroph = self.compile(r"a8137703.+?(\d+)")
        self.apiLevel = self.compile(r"ea8f9b23.+?(\d+)")
        self.apiItems = self.compile(r'<a href=\"/app\.php\?act=item&id=(\d+)&auth_key=\w+&viewer_id=\d+&group_id=\d+&api_id=\d+\" class=\"resitem\">')
        self.apiBooks = self.compile(r'<a href=\"/app\.php\?act=item&id=(\d+)&auth_key=\w+&viewer_id=\d+&group_id=\d+&api_id=\d+\" class=\"resitem\"><div data-toggle=\"tooltip\" data-placement=\"top\" data-html=\"true\" title=\"\" data-original-title=\"Страница - (.+?)\".+?right\"> (\d+)</span>')
        self.addrule(self.doBackToCitadel, r"👑Текущий правитель")
        self.addrule(self.doBackToHome, r"Здесь проживают только самые")
        self.addrule(self.doBeginHunt, r"⌛Вы начинаете охоту")
        self.addrule(self.doBeginLabirint, r"^Вы обнаруживаете, что заплутали во время исследований")
        self.addrule(self.doBeginRuins, r"⌛Вы начинаете поиски")
        self.addrule(self.doBeginWork, r"⌛Время выполнения")
        self.addrule(self.doHunterView, r"^📜Текущее задание: (нет|.+?)\b.+?(\d+).+?(\d+)")
        self.addrule(self.doHunterTaskShow, r"^📌Листок на доске:.+📜Цель задания: (.+?)👝")
        self.addrule(self.doHunterTaskAccept, r"^✅Задание .+? принято")
        self.addrule(self.doHunterTroph, r"^Какие трофеи Вы хотите обменять")
        self.addrule(self.doHunterStats, r"^Привратник готов.+?(Зелье силы) - (\d+).+?(Зелье ловкости) - (\d+).+?(Зелье выносливости) - (\d+).+?📜Текущая репутация: (\d+)")
        self.addrule(self.doCaptchaWall, r"Свечи освещают пять пронумерованных")
        self.addrule(self.doCaptchaComing, r"^Пол под Вами неожиданно провалился")
        self.addrule(self.doCaptchaSend, r"^У Вас есть минута, чтобы воспроизвести")
        self.addrule(self.doCloakLow, r"Осталось зарядов маскировки: (\d+)")
        self.addrule(self.doClosedDoor, r"На двери имеется углубление для вставки какого-то небольшого предмета")
        self.addrule(self.doControlStart, r"валли старт")
        self.addrule(self.doControlStop, r"валли стоп")
        self.addrule(self.doControlBooks, r"валли книги")
        self.addrule(self.doControlDrop, r"валли сдай")
        self.addrule(self.doDice, r"Правила просты: Вы кидаете кости")
        self.addrule(self.doExplore, r"^🚩Локация:.+?💀Трофеев: (\d+).💚HP: (\d+)\/(\d+).+?(\d+)%")
        self.addrule(self.doExploreSpeed, r"^🧭Скорость.+?(\d+)%(.+?👁Кажется)?")
        self.addrule(self.doExploreDrop, r"Больше здесь нечего добыть")
        self.addrule(self.doFarmCoat, r".+? покоится рядом с Вами")
        self.addrule(self.doFarmHerb, r"^.Вы обнаруживаете (адский)*.+")
        self.addrule(self.doFarmRes, r"^.Вы обнаружили (?:подходящий|лен|подходящее|небольшую)")
        self.addrule(self.doFarmView, r"^[🗳💀🛡⚔📚🏮]Вы обнаружили")
        self.addrule(self.doFightDead, r"^🖤Вы получили критическое ранение и травму")
        self.addrule(self.doFightEnd, r"(?:(🖤Грубым ударом).+?)?Бой завершен")
        self.addrule(self.doFightOnePunch, r"^🚫Вы оглушены громким рыком")
        self.addrule(self.doFightOneSkill, r"^🚫У Вас не осталось времени")
        self.addrule(self.doFightOneSkill, r"^❌Вам не хватило точности")
        self.addrule(self.doFightOneSkill, r"^❓Вам не хватило концентрации")
        self.addrule(self.doFightOneSkill, r"^🔥Ваш факел светит очень ярко")
        self.addrule(self.doFightOneSkill, r"^🖤Вы нанесли противнику")
        self.addrule(self.doFightOneSkill, r"^🛡Вы приготовились принять удар на щит")
        self.addrule(self.doFightOneSkill, r"^🤢Вы отравили противника")
        self.addrule(self.doFightOneSkill, r"🏮Вы выпили зелье здоровья и восстановили")
        self.addrule(self.doFightNoBag, r"^У Вас нет зелий")
        self.addrule(self.doFightNoBag, r"^У Вас не осталось зелий")
        self.addrule(self.doFightNext, r"🎲Дополнительный ход")
        self.addrule(self.doFightNext, r"🏳Вы предлагаете противнику отказаться")
        self.addrule(self.doFightPvpSkip, r"^🏳Противник предлагает отказаться от поединка")
        self.addrule(self.doFightPvp, r"^(?:👥Гильдия: (.+?)|👤Ваш противник: .+?)$.+?(?:Хар-ки: ⚔(\d+) 🛡(\d+)%.+?)?%.+?: 🎯(\d+)% 💫(\d+)%.+?❤(?:HP|Противник): (\d+)\/(\d+)(?: \((.?\d+)\))*.+?(\d+)%.+?💚(?:HP|Персонаж): (\d+)\/(\d+)(?: \((.?\d+)\))*.+?(\d+)%(.+?🎲Ваш ход)?")
        self.addrule(self.doFightPve, r"^❤.+?: (\d+)/(\d+).+?(\d+)%.⚔(\d+) 🛡(\d+)% 💫\d+% (.)(\d+)%..💚.+?: (\d+)/(\d+).+?(\d+)%.👞\d+% 🛡\d+% 💫(\d+)% 🎯(\d+)%")
        self.addrule(self.doFightStep, r"(?:Ваша точность \(🎯(\d+)% 💫(\d+)%\).+)?(⛔Противник ловко.+?)?(?:увеличена на \d+% до конца боя \((\d+)%\).+)?(?:раскололи его экипировку \(🛡(\d+)%\).+?)?(?:(⚔Навязав Вам).+?)?(?:(🖤Грубым).+?)?(?:(🖤Противник).+?)?(?:(🗣Противник).+?)?❤(?:HP|Противник): (\d+)\/(\d+)(?: \((.?\d+)\))*.+?(\d+)%.+?💚(?:HP|Персонаж): (\d+)\/(\d+)(?: \((.?\d+)\))*.+?(\d+)%(.+?🎲Ваш ход)?")
        self.addrule(self.doFightStand, r"^⚔Вы приняли .+?тойку (?:для .+? \(🎯(\d+)%\))?")
        self.addrule(self.doFisher, r"Наживки осталось: (\d+)")
        self.addrule(self.doFisherFound, r"Поплавок полностью ушел под воду")
        self.addrule(self.doFisherLeave, r"Вы уверены, что хотите прервать рыбалку")
        self.addrule(self.doGoblin, r"В темном зале Вам повстречался шустрый гоблин")
        self.addrule(self.doInHome, r"^💖Отдых в доме")
        self.addrule(self.doInjuriesStationary, r"^💖Все травмы успешно излечены")
        self.addrule(self.doInjuriesPartial, r"^💖Вы успешно излечили (\d+) травм")
        self.addrule(self.doInjuriesFull, r"^💖Вы успешно излечили все свои травмы")
        self.addrule(self.doInjuriesOne, r"^👝Вы собрали и съели: 🌼Жизнецвет")
        self.addrule(self.doInjuriesUpdate, r"^Вам стало лучше.+?🖤Количество травм: (\d+)")
        self.addrule(self.doKitchenDone, r"^Плотно подкрепившись приготовленной во время отдыха едой")
        self.addrule(self.doKitchenLeave, r"^⌛Шанс повышения")
        self.addrule(self.doLabirint, r"🧭 Ветер дует откуда-то с (.+?)\.")
        self.addrule(self.doLabirint, r"🧭 Ветер берет начало")
        self.addrule(self.doLabirint, r"🧭 Источник ветра совсем")
        self.addrule(self.doLeaveBattle, r"Вы уверены, что хотите покинуть битву")
        self.addrule(self.doLeaveFontan, r"^⌛Время отдыха.+?🖤Количество травм: (\d+)")
        self.addrule(self.doLeaveHealing, r"Исследуя подземные коридоры, Вы наткнулись на целебный источник")
        self.addrule(self.doLeaveHunt, r"❌На этой поляне больше не осталось добычи")
        self.addrule(self.doLeaveLabirint, r"Для подтверждения - нажмите кнопку выхода повторно")
        self.addrule(self.doLeaveRuins, r"^❌В этих руинах больше не осталось добычи")
        self.addrule(self.doLeaveSomething, r"^Завал разобран")
        self.addrule(self.doLeaveSomething, r"^Осколки собраны")
        self.addrule(self.doLeaveSomething, r"Руда добыта")
        self.addrule(self.doLevel, r"⌛Исследование уровня, подождите")
        self.addrule(self.doMushroom, r"^👝Вы собрали и съели: (?:🍄Пещерный гриб.+?💚HP: (\d+)/(\d+).+?(\d+)%)?")
        self.addrule(self.doNextLevel, r"^🚫Вы больше не получите добычи с противников такого уровня")
        self.addrule(self.doFlower, r"^👝Вы собрали и раскрыли: 🌷Цветок глубин")
        self.addrule(self.doOutdoorBreak, r"Боль разрывает Вас на части")
        self.addrule(self.doOutdoorBreak, r"Кажется, конец близок")
        self.addrule(self.doOutdoorBreak, r"Местность становится все опаснее и опаснее")
        self.addrule(self.doOutdoorBreak, r"Ноги дрожат от предчувствия беды")
        self.addrule(self.doOutdoorBreak, r"Нужно быть предельно осторожным")
        self.addrule(self.doOutdoorBreak, r"С каждым шагом чувство тревоги нарастает")
        self.addrule(self.doOutdoorBreak, r"Смерть таится за каждым поворотом")
        self.addrule(self.doOutdoorBreak, r"Становится сложно разглядеть дорогу впереди")
        self.addrule(self.doOutdoorBreak, r"Чувство тревоги бьет в колокол")
        self.addrule(self.doOutdoorStep, r"⌛Путешествие началось")
        self.addrule(self.doOutdoorStep, r"⌛Путешествие продолжается")
        self.addrule(self.doResp, r"^💀Благодаря особенности нежити")
        self.addrule(self.doResp, r"^🔥Благодаря пассивному умению")
        self.addrule(self.doRest, r"^⌛Вы присели у костра восстановить")
        self.addrule(self.doRetrySend, r"⌛Вы отправляете команды слишком часто")
        self.addrule(self.doSmug, r"Контрабандист готов купить все")
        self.addrule(self.doTaskDone, r"📜Вы успешно выполнили задание гильдии")
        self.addrule(self.doTradeTown, r"^В портовом квартале всегда кипит жизнь")
        self.addrule(self.doTradeTavern, r"^Снять комнату - \d+ золота")
        self.addrule(self.doTradeSleep, r"^Комнаты убраны! Во время разбора")
        self.addrule(self.doTradeMenu, r"^📜Меню таверны")
        self.addrule(self.doTradeMenuAccept, r"💖Перекусив, Вы полностью восстанавливаете")
        self.addrule(self.doTradeMenuDecline, r"^🚫Еда на кухне.+?⌛Осталось: (?:(\d+) час\. )?(?:(\d+) мин\. )?(?:(\d+) сек\.)?")
        self.addrule(self.doTrader, r"Мрачного вида торговец за странным прилавком")
        self.addrule(self.doTrapEasy, r"👞Исследуя коридор, Вы наткнулись на ловушку\. Однако, благодаря ловкости и удаче, Вам удалось не получить урона\.")
        self.addrule(self.doTrapHard, r"Вы пережили этот урон, но нужно немного времени, чтобы освободиться")
        self.addrule(self.doTreasureChest, r"Блуждая по коридорам, вы наткнулись на сундук с сокровищем")
        self.addrule(self.doTreasureWall, r"🌕В небольшой трещине в стене")
        self.addrule(self.doUseBottle, r"У Вас на поясе осталось (\d+) зелий")
        self.addrule(self.doUseStand, r"^🗡Текущий тип ударов:")
        self.addrule(self.doWaterHerbPour, r"В центре рощи виднеется недавно")
        self.addrule(self.doWaterHerbWait, r"Вы использовали первозданную воду")
        self.addrule(self.doWaterHerbLeave, r"🚫У Вас нет первозданной воды")
        self.addrule(self.doWaterHerbLeave, r"Вы вырастили и собрали")
        self.addrule(self.doZeroInventory, r"🔓Осталось места в инвентаре: (\d+)")
        self.caption("Walker v%s Py v%s" % (self.VERSION, sys.version), True)
        self.config.seller(self.regSell)
        self.config.transfer(self.regTransfer)
        self.thread(self.check)

    def check(self):
        """ Проверка текущего хода """
        if self.trade and self.trade(self.event):
            return
        # Признаки
        tmp_control = (self.event.peer_id == self.config.alertID) or (self.event.peer_id == self.config.selfID)
        tmp_game = (self.event.peer_id == self.GAME_BOT_ID)
        # Сохраним кнопочки
        if tmp_game:
            self.saveActions()
        elif not tmp_control:
            return
        # Выйдем если остановлен
        if (not self.active) and (not tmp_control):
            return
        # Переберем все действия
        if not self.work(True):
            return
        # Заменим заголовок
        self.caption("♥:%s M:%s I:%s T:%s - v%s" % (self.injuries, self.cloaks, self.inventory, self.troph, self.VERSION))

    def wait(self, extended: bool = False):
        """ Ожидание кванта времени """
        tmp_time = random.randint(self.config.waitMin, self.config.waitMax) // 1000
        # Для выхода с комнаты ждем подольше
        if extended:
            self.sleep(tmp_time * 4, "выхода с комнаты")
        else:
            self.sleep(tmp_time, "отправки действия")
        return

    def sendAction(self, text: str, force: bool = False):
        """ Отправка действия """
        self.wait()
        self.retry = text
        if force or text in self.actions:
            self.send(text)
        else:
            print(self.actions)
            self.alert("Walker wrong action " + text)
        # Всегда успешно
        return True

    def saveActions(self):
        """ Сохранение доступных действий """
        if not hasattr(self.event, "keyboard"):
            return
        # Заменяем кнопки, если он для управления
        if not ("inline" in self.event.keyboard):
            self.actions = {}
        # Если кнопок нет - выходим
        if not ("buttons" in self.event.keyboard):
            return
        # Перепишем действия
        for tmpButtonLines in self.event.keyboard["buttons"]:
            for tmpButton in tmpButtonLines:
                self.actions[tmpButton["action"]["label"]] = tmpButton["color"]
        return

    def goPortal(self, state: int = STATE_DUMP):
        """ Путешествие в портал """
        self.updateInjuries(False)
        self.state = state
        self.log("Флаг: %s травмы: %s маска: %s рюкзак: %s трофеи: %s" % (
            self.state, self.injuries, self.cloaks, self.inventory, self.troph))
        self.sendAction("В портал")

    def regSell(self, itemid: int, name: str, action: int):
        """ Регистрация закупки """
        tmp_item = SellerItem()
        tmp_item.id = itemid
        tmp_item.name = name
        tmp_item.action = action
        # Добавим в наш списочек
        self.sells[itemid] = tmp_item

    def regTransfer(self, itemid: int, name: str, action: int):
        """ Регистрация закупки """
        tmp_item = SellerItem()
        tmp_item.id = itemid
        tmp_item.name = name
        tmp_item.action = action
        # Добавим в наш списочек
        self.transfers[itemid] = tmp_item

    def checkMaps(self):
        """ Очистка инвентаря """
        if not self.config.api:
            return
        # Соберем предметы рюкзака
        tmp_items = self.apiItems.findall(self.apiUser())
        if not tmp_items:
            return
        # Скушаем / продадим
        for tmp_item in tmp_items:
            if not (tmp_item in self.sells):
                continue
            tmp_sell = self.sells[tmp_item]
            self.apiSell(tmp_sell.id, tmp_sell.action, tmp_sell.name)
            self.sleep(3, "следующего предмета инвентаря")
        # Выполним карту
        for tmp_item in tmp_items:
            # Карта источника
            if tmp_item == "14663" and self.injuries >= self.config.injuriesForFountain:
                return self.apiSell(tmp_item, 0, "Карта источника")
            # Карта испытаний
            if tmp_item == "14664":
                return self.apiSell(tmp_item, 0, "Карта испытаний")
            # Карта руин
            if tmp_item == "14963" and self.config.searching:
                return self.apiSell(tmp_item, 0, "Карта руин")
            # Карта угодий
            if tmp_item == "14662" and self.config.hunting:
                return self.apiSell(tmp_item, 0, "Карта угодий")
            # Карта озера
            if tmp_item == "14660":
                return self.apiSell(tmp_item, 0, "Карта озера")
            # Карта сокровищ
            if tmp_item == "14661":
                return self.apiSell(tmp_item, 0, "Карта сокровищ")

    def buildBooks(self):
        """ Сбор всех книг """
        if not self.config.api:
            return
        # Соберем предметы рюкзака
        tmp_items = self.apiBooks.findall(self.apiUser())
        if not tmp_items:
            return
        # Скушаем / продадим
        tmp_find: SellerItem
        for tmp_item in tmp_items:
            for tmp_find in self.transfers.values():
                if tmp_item[1] == tmp_find.name:
                    if tmp_find.action != 1:
                        continue
                    if int(tmp_item[2]) < 5:
                        continue
                    if not self.apiScrolls(tmp_item[0], tmp_find.name):
                        self.alert("- сбор встал")
                        return
                    self.sleep(10, "следующего предмента инвентаря")
                    break
        self.alert("+ сбор закончен")

    def dropItems(self):
        """ Передача предметов """
        if not self.config.api:
            return
        # Соберем предметы рюкзака
        tmp_items = self.apiItems.findall(self.apiUser())
        if not tmp_items:
            return
        # Скушаем / продадим
        tmp_dict = {}
        for tmp_item in tmp_items:
            if tmp_item in self.transfers:
                if not (tmp_item in tmp_dict):
                    tmp_dict[tmp_item] = 1
                else:
                    tmp_dict[tmp_item] += 1
        for tmp_item in tmp_dict:
            tmp_transfer = self.transfers[tmp_item].name.lower()
            tmp_count = tmp_dict[tmp_item]
            if tmp_count == 1:
                if not self.send("передать %s" % tmp_transfer, self.config.storageChannel, self.config.storageMessage):
                    self.alert("- передача встала")
                    return
            else:
                if not self.send("передать %s - %s штук" % (tmp_transfer, tmp_count), self.config.storageChannel, self.config.storageMessage):
                    self.alert("- передача встала")
                    return
            self.sleep(random.randint(10000, 20000) // 1000, "перед сдачей")
        self.alert("+ сдача закончена")

    def updateInjuries(self, add: bool):
        """ Уточнение количества травм """
        if add:
            self.injuries += 1
        # Уточним у api
        if self.config.api and self.injuries >= self.config.injuriesForHome:
            self.injuries = self.apiResult(self.apiInjur, self.apiUser)

    def getStand(self):
        """ Текущая стойка в бою """
        for tmp_button in self.actions:
            if tmp_button[0] == "#":
                return tmp_button
        return None

    def apiSell(self, itemid: str, action: int, name: str):
        """ Использование предмета """
        tmp_data = {
            "id": itemid,
            "m": action
        }
        tmp_referer = self.API_URL % (self.ACT_TYPE_ITEM % itemid, self.config.api)
        tmp_url = self.API_URL % ("a_sell_item", self.config.api)
        # Отправим
        tmp_response = requests.post(tmp_url, tmp_data, headers=AUHelper.buildHeaders(7 + len(itemid), tmp_referer))
        if tmp_response.ok:
            self.inventory -= 1
            self.log("%s утилизирован - %s" % (name, tmp_response.text))
            return True
        else:
            self.log("%s не утилизирован - %s" % (name, tmp_response.reason))
            return False

    def apiScrolls(self, itemid: str, name: str):
        """ Использование предмета """
        # Откроем страницу
        tmp_referer = self.API_URL % (self.ACT_TYPE_ITEM % itemid, self.config.api)
        tmp_response = requests.get(self.API_URL % (self.ACT_TYPE_ITEM % itemid, self.config.api), headers=AUHelper.buildHeaders(0, tmp_referer))
        if not tmp_response.ok:
            return False
        # Считаем защиту
        tmp_params = json.loads(re.search(r"window.pv644 = ({.+})", tmp_response.text)[1])
        tmp_params = {
            "code": "51153l29le090c096fb1a4093",
            "pwid": "w_173",
            "context": 1,
            "hash": "",
            "channel": "",
            "vars": tmp_params
        }
        tmp_params = AUHelper.buildQuery(tmp_params)
        tmp_response = requests.post(self.API_URL % ("a_program_run", self.config.api), tmp_params, headers=AUHelper.buildHeaders(len(tmp_params), tmp_referer))
        if not tmp_response.ok:
            return False
        # Отправим сбор первый раз
        tmp_params = {
            "ch": "u" + str(self.config.selfID),
            "text": "Собрать все книги",
            "context": 1,
            "messages[0][message]": "Собрать все книги",
            "bid": "w_173"
        }
        tmp_url = self.API_URL % ("a_program_say", self.config.api)
        tmp_params = AUHelper.buildQuery(tmp_params)
        tmp_response = requests.post(tmp_url, tmp_params, headers=AUHelper.buildHeaders(len(tmp_params), tmp_referer))
        if not tmp_response.ok:
            return False
        # Через паузу отправим второй раз
        self.sleep(1, "подтверждения")
        tmp_response = requests.post(tmp_url, tmp_params, headers=AUHelper.buildHeaders(len(tmp_params), tmp_referer))
        if tmp_response.ok:
            self.inventory += 1
            self.log("%s собрано - %s" % (name, tmp_response.text))
            return True
        else:
            self.log("%s не собрано - %s" % (name, tmp_response.reason))
            return False

    def apiLoad(self, page: str):
        """ Загрузка страницы API """
        tmp_url = self.API_URL % (page, self.config.api)
        self.log("Грузим ссылку %s" % tmp_url)
        # Загрузим
        return requests.get(tmp_url).text

    def apiStat(self):
        """ Загрузка страницы API для статистики """
        return self.apiLoad(self.ACT_TYPE_PAGE % self.API_PAGE_STAT)

    def apiRep(self):
        """ Загрузка страницы API для репутации """
        return self.apiLoad(self.ACT_TYPE_PAGE % self.API_PAGE_REP)

    def apiUser(self):
        """ Загрузка страницы API рюкзака """
        return self.apiLoad(self.ACT_TYPE_USER)

    def apiResult(self, regex: re, func: callable):
        """ Получение результата API выборки """
        tmp_match = regex.search(func())
        if tmp_match:
            return self.toInt(tmp_match[1])
        else:
            return 0

    def doCaptchaComing(self, _match: []):
        """ Картинка капчи """
        if not self.config.api:
            return self.alert("Капча")
        # Если апи есть - распознаем
        tmpUrl = self.getphoto(self.GAME_BOT_ID, self.event.message_id, 1172)
        if tmpUrl:
            self.answer = self.captcha.fromurl(tmpUrl)
        else:
            self.alert("Картинка не найдена")
        # Проверим нахождение
        if self.answer:
            self.log("Капча распознана как %s" % self.answer)
        else:
            self.alert("Капча не распознана")

    def doCaptchaWall(self, _match: []):
        """ Капча """
        if self.answer:
            self.sendAction("Подойти к плитам")

    def doCaptchaSend(self, _match: []):
        """ Ввод капчи """
        if not self.answer:
            return
        # Долго подождем
        self.log("Делаем вид что смотрим")
        self.wait()
        self.log("Делаем вид что вводим")
        self.wait()
        # Введем капчу
        self.send(self.answer)

    def doControlStart(self, _match: []):
        """ Запуск управления """
        self.active = True
        self.send("+ запущен", self.event.peer_id)

    def doControlStop(self, _match: []):
        """ Остановка управления """
        self.active = False
        self.send("+ остановлен", self.event.peer_id)

    def doControlBooks(self, _match: []):
        """ Сбор всех книг """
        self.send("> собираю...", self.event.peer_id)
        self.buildBooks()

    def doControlDrop(self, _match: []):
        """ Передача лута на склад """
        self.send("> сдаю...", self.event.peer_id)
        self.dropItems()

    def doWaitResThread(self):
        """ Выполнение потока ожидания ресурса """
        self.log("Ждем появления ресурса...")
        self.wait(True)
        # Подождем сбор шкуры или травы
        if self.drop == self.DROP_NONE:
            self.log("Ничего нет :(")
            self.doExploreDrop(None)
        return

    def doWaitRes(self, _match: [], callback: object):
        """ Выполнение обхода комнаты """
        self.state = self.STATE_EXPLORE
        self.match = _match
        self.drop = self.DROP_NONE
        self.nextWay = callback
        Thread(target=self.doWaitResThread).start()

    def doRetrySend(self, _match: []):
        """ Повторная отправка """
        self.sendAction(self.retry, True)

    def doLevel(self, _match: []):
        """ Исследование уровня, заглушка для лога """
        return

    def doGoblin(self, _match: []):
        """ Исследование уровня, заглушка для лога """
        self.sendAction("Продолжить")

    def doInHome(self, _match: []):
        """ Вход в дом """
        if self.injuries == 0:
            self.sendAction("Покинуть дом")

    def doInjuriesStationary(self, _match: []):
        """ Все травмы излечены """
        self.honger = 100
        self.injuries = 0
        # Вернемся в колодец или уйдем с фонтана
        if "Кухня" in self.actions:
            if self.config.constat:
                self.sendAction("Кухня")
            else:
                self.doInHome(_match)
        else:
            self.doLeaveSomething(_match)

    def doInjuriesPartial(self, _match: []):
        """ Травмы излечены частично """
        self.injuries = max(0, self.injuries - self.toInt(_match[1]))

    def doInjuriesOne(self, _match: []):
        """ Одна травма излечена """
        self.injuries = max(0, self.injuries - 1)
        self.doExploreDrop(None)

    def doInjuriesFull(self, _match: []):
        """ Все травмы излечены """
        self.injuries = 0

    def doInjuriesUpdate(self, _match: []):
        """ Учет травм после костра """
        self.injuries = self.toInt(_match[1])

    def doTrader(self, _match: []):
        """ Продавец (Согласиться, Другой товар, Уйти) """
        if self.config.trader == 0:
            self.sendAction("Уйти")
        # Купить
        elif self.config.trader == 1:
            self.sendAction("Согласиться")
        # Уведомить
        elif self.config.trader == 2:
            self.alert("Walker trader")

    def doWaterHerbPour(self, _match: []):
        """ Полив шаг 1 """
        self.sendAction("Полить растение")

    def doWaterHerbWait(self, _match: []):
        """ Полив шаг 2 """
        self.sendAction("Ждать")

    def doWaterHerbLeave(self, _match: []):
        """ Полив шаг 3 """
        self.sendAction("Уйти")

    def doHunterView(self, _match: []):
        """ Обзор охотников """
        self.reputation = self.toInt(_match[2])
        self.tasksCount = self.toInt(_match[3])
        self.tasksList = []
        self.tasksDone = False
        # Определим состояние
        if self.state == self.STATE_DUMP:
            self.state = self.STATE_HUNTER_TROPH
            # Поищем задания
            if (self.tasksCount > 0) and (_match[1] == "нет"):
                return self.sendAction("Доска заданий")
            else:
                return self.sendAction("Обмен трофеев")
        # Обмен репутации
        elif self.state == self.STATE_HUNTER_TROPH:
            return self.sendAction("Лавка репутации")
        # В итоге назад
        self.sendAction("Вернуться")

    def doHunterTaskShow(self, _match: []):
        """ Учет доступных заданий """
        self.tasksList.append([len(self.tasksList), _match[1]])
        # Определим что загружены все
        if len(self.tasksList) < min(3, self.tasksCount):
            return
        # Списки
        tmp_accept = []
        tmp_reject = []
        tmp_skip = ["(PvP)",
                    "в таверне",
                    "вернуться живым",
                    "добыть пещерного",
                    "отразить в осаде",
                    "поймать рыбу весом более 6кг",
                    "поймать рыбу весом более 10кг",
                    "пройти подземный",
                    "выйти на элитную",
                    "купить любой предмет"]
        # Раздербаним в массив
        for tmpAction in self.actions:
            if "Принять задание" in tmpAction:
                tmp_accept.append(tmpAction)
            elif "Заменить задание" in tmpAction:
                tmp_reject.append(tmpAction)
        # Поищем смену или принятие невыполнимого задания
        for tmp_index, tmp_text in self.tasksList:
            for tmp_deceptor in tmp_skip:
                if not (tmp_deceptor in tmp_text):
                    continue
                self.tasksList = []
                # Почистим
                for tmpAction in tmp_accept:
                    self.actions.pop(tmpAction)
                for tmpAction in tmp_reject:
                    self.actions.pop(tmpAction)
                # Отправим
                if len(tmp_reject) > 0:
                    return self.sendAction(tmp_reject[tmp_index], True)
                else:
                    return self.sendAction(tmp_accept[tmp_index], True)
                    # Замен нет, берем первое наиболее доступное
        self.sendAction(tmp_accept[0])

    def doHunterTaskAccept(self, _match: []):
        """ Взятие задания """
        if len(self.tasksList) > 0:
            self.sendAction("Обмен трофеев")
        else:
            self.sendAction("Доска заданий")
        # Уменьшим количество задач, т.к.  взятая уменьшает список
        self.tasksCount -= 1

    def doHunterTroph(self, _match: []):
        """ Обмен трофеев """
        self.troph = 0
        self.inventory = 100
        self.sendAction("Обычные трофеи")
        self.sendAction("Охотничьи трофеи")
        self.sendAction("Назад")

    def doHunterStats(self, _match: []):
        """ Покупка стат """
        tmpHave = self.toInt(_match[7])
        tmpSort = [[self.toInt(_match[2]), 1],
                   [self.toInt(_match[4]), 3],
                   [self.toInt(_match[6]), 5]]
        tmpSort.sort()
        # Поищем
        if tmpHave >= tmpSort[0][0]:
            self.sendAction(_match[tmpSort[0][1]])
        # Вернемся
        self.state = self.STATE_NONE
        self.sendAction("Назад")

    def doBackToHome(self, _match: []):
        """ Вход домой """
        # Хил в доме
        if self.injuries >= self.config.injuriesForHome:
            self.sendAction("Свой дом")
        else:
            self.sendAction("Назад")
        return

    def doBackToCitadel(self, _match: []):
        """ Вход в цитадель """
        # Хочется спать
        if self.state == self.STATE_SLEEP:
            return self.sendAction("Портовый квартал")
        # Хочется кушать
        if self.state == self.STATE_HONGER:
            return self.sendAction("Портовый квартал")
        # Сдача ресурсов
        if self.state == self.STATE_DUMP:
            return self.sendAction("Гильдия охотников")
        # Хил в доме
        if self.injuries >= self.config.injuriesForHome:
            return self.sendAction("Верхний квартал")
        # Назад качаться
        self.sendAction("В колодец")

    def doLeaveHealing(self, _match: []):
        """ Отхил в фонтане """
        self.sendAction("Продолжить")

    def doLeaveHunt(self, _match: []):
        """ Уход с охоты """
        self.inventory = self.config.inventoryLow
        self.sendAction("Прервать охоту")

    def doFisherLeave(self, _match: []):
        """ Уход с рыбалки если кончилась наживка """
        self.sendAction("Прервать")

    def doFisherFound(self, _match: []):
        """ Рыба найдена """
        self.sendAction("Подсечь")

    def doFisher(self, _match: []):
        """ Ловля рыбы """
        if self.toInt(_match[1]) > 0:
            self.sendAction("Закинуть удочку")
        else:
            self.sendAction("Прервать рыбалку")

    def doLeaveBattle(self, _match: []):
        """ Уход с боя """
        self.sendAction("Подтвердить")

    def doZeroInventory(self, _match: []):
        """ Проверка рюкзака """
        self.inventory = self.toInt(_match[1])
        if self.inventory <= 10:
            self.checkMaps()
        if self.inventory <= self.config.inventoryLow:
            self.alert("Walker inventory low")
        # Цветочек показывается без уведомления
        if self.drop == self.DROP_WAIT:
            self.doExploreDrop(None)

    def doKitchenDone(self, _match: []):
        """ Обработка входа в кухню """
        if self.config.constat:
            self.sendAction("+50% прокачка " + self.config.constat)

    def doKitchenLeave(self, _match: []):
        """ Выход с кухни """
        self.sendAction("Назад")

    def doOutdoorStep(self, _match: []):
        """ Запуск похода за город """
        return

    def doResp(self, _match: []):
        """ Продолжение после воскреса """
        if "Продолжить" in self.actions:
            self.sendAction("Продолжить")
        elif "Отдых" in self.actions:
            self.sendAction("Отдых")

    def doRest(self, _match: []):
        """ Мясо у костра """
        if "Приготовить пищу" in self.actions:
            self.sendAction("Приготовить пищу")

    def doOutdoorBreak(self, _match: []):
        """ Прерывание похода за город """
        self.sendAction("Вернуться в город")

    def doCloakLow(self, _match: []):
        """ Проверка маскировки """
        self.cloaks = self.toInt(_match[1])
        if self.cloaks <= self.config.cloakLow:
            self.alert("Walker masks low")

    def doUseStand(self, _match: []):
        """ Смена стойки """
        self.sendAction(self.fight.myStand[1:])

    def doUseBottle(self, _match: []):
        """ Выпивание зелья, не пьется при ручном бое с элиткой """
        if not self.config.bottle(self.actions, self.sendAction):
            print(self.actions)
            self.alert("Walker not bottles found")
        return

    def doDice(self, _match: []):
        """ Бросок кубиков (Бросить кости, Уйти) """
        if self.config.rollDice:
            self.sendAction("Бросить кости")
        else:
            self.sendAction("Уйти")

    def doSmug(self, _match: []):
        """ Контрабандист """
        self.sendAction("Продать трофеи")

    def doTaskDone(self, _match: []):
        """ Задание выполнено """
        self.tasksDone = True

    def doTradeTown(self, _match: []):
        """ Вход в торговый район """
        if self.state == self.STATE_SLEEP:
            self.sendAction("Таверна")
        elif self.state == self.STATE_HONGER:
            self.sendAction("Таверна")
        else:
            self.sendAction("Вернуться")

    def doTradeTavern(self, _match: []):
        """ Вход в таверну """
        if self.state == self.STATE_SLEEP:
            self.sendAction("Уборка")
        elif self.state == self.STATE_HONGER:
            self.sendAction("Заказать еду")
        else:
            self.sendAction("Вернуться")

    def doTradeSleep(self, _match: []):
        """ Уборка завершена """
        self.state = self.STATE_NONE
        self.injuries = self.config.injuriesForHome
        self.sendAction("Прервать процесс")

    def doTradeMenu(self, _match: []):
        """ Выбор еды """
        self.state = self.STATE_DUMP
        self.sendAction("Дешевый обед")

    def doTradeMenuAccept(self, _match: []):
        """ Успех перекуса """
        self.honger = 100
        self.hongerTime = datetime.today() + timedelta(hours=4)
        # Вернемся
        self.sendAction("Назад")

    def doTradeMenuDecline(self, _match: []):
        """ Неуспех перекуса """
        tmpHours = self.toInt(_match[1])
        tmpMins = self.toInt(_match[2])
        tmpSecs = self.toInt(_match[3])
        # Установим время следущего запроса чтобы не циклиться
        self.honger = 100
        self.hongerTime = datetime.today() + timedelta(hours=tmpHours, minutes=tmpMins, seconds=tmpSecs)
        # Вернемся
        self.sendAction("Назад")

    def doClosedDoor(self, _match: []):
        """ Запертая дверь """
        if "Открыть силой" in self.actions:
            self.sendAction("Открыть силой")
        else:
            self.sendAction("Вставить камень судьбы")

    def doBeginHunt(self, _match: []):
        """ Отмена охоты """
        if self.config.hunting == 0:
            self.doLeaveHunt(_match)

    def doBeginRuins(self, _match: []):
        """ Уход с поисков """
        if self.config.searching == 0:
            self.doLeaveRuins(_match)

    def doBeginWork(self, _match: []):
        """ Уход с работы """
        if self.state == self.STATE_SLEEP:
            return
        if self.config.working == 0:
            self.doLeaveSomething(_match)

    def doLeaveRuins(self, _match: []):
        """ Покидание руин """
        self.sendAction("Прервать поиск")

    def doLeaveSomething(self, _match: []):
        """ Покидание чего либо """
        self.sendAction("Покинуть")

    def doLeaveFontan(self, _match: []):
        """ Уход с фонтана """
        self.injuries = self.toInt(_match[1])
        self.sendAction("Набрать воды")
        # Если травм мало - выходим
        if self.injuries < self.config.injuriesForFountain:
            self.doLeaveSomething(_match)

    def doBeginLabirint(self, _match: []):
        """ Уход с лабиринта """
        if self.config.labirint == 0:
            return
        # Заготовка для прохода
        self.labData = [[-1 for _ in range(200)] for _ in range(200)]
        self.labX = 100
        self.labY = 100

    def doLabirint(self, _match: []):
        """ Уход с лабиринта """
        if self.config.labirint == 0:
            return self.doLeaveLabirint(_match)
        # Запуск из лабиринта
        if len(self.labData) == 1:
            self.doBeginLabirint(_match)
        # Если ветер не известен - учиытваем последний видимый
        if len(_match.regs) > 1:
            self.wing = _match[1]
        # Обнулим
        tmp_vectors = []
        tmpPoints = [-1, 1]

        def dump():
            """ Подфункция вывода текущей карты """
            for y in range(self.labY - 10, self.labY + 10):
                for x in range(self.labX - 10, self.labX + 10):
                    if self.labX == x and self.labY == y:
                        print("{:2d}^".format(self.labData[y][x]), end="")
                    elif self.labData[y][x] == -3:
                        print(" * ", end="")
                    elif self.labData[y][x] == -2:
                        print(" + ", end="")
                    elif self.labData[y][x] == -1:
                        print(" ` ", end="")
                    elif self.labData[y][x] == 0:
                        print(" # ", end="")
                    else:
                        print("{:2d} ".format(self.labData[y][x]), end="")
                print()

        def check(x, y, path, vs, points):
            """ Подфункция невозврата """
            tmp_path = "На " + path
            if not (tmp_path in self.actions) or (self.actions[tmp_path] == "negative"):
                return
            # Проверим доступность слотов
            tmp_val = self.labData[self.labY + y][self.labX + x]
            if tmp_val == 0:
                return
            # Определим территорию
            tmp_vectors.append([tmp_val, x, y, path])
            if tmp_val < 0:
                points[1] = 0
                if vs in self.wing:
                    tmp_val = -2
                else:
                    tmp_val = -3
                self.labData[self.labY + y][self.labX + x] = tmp_val
            points[0] += 1

        # Заполним стороны
        check(0, -1, "север", "юг", tmpPoints)
        check(0, +1, "юг", "север", tmpPoints)
        check(-1, 0, "запад", "восток", tmpPoints)
        check(+1, 0, "восток", "запад", tmpPoints)
        # Клетки направлений минус выход, для тупика сразу закрываем
        if tmpPoints[0] == 0:
            tmpPoints[1] = 0
        self.labData[self.labY][self.labX] = tmpPoints[0] - tmpPoints[1]
        # Выведем
        dump()
        tmp_vectors.sort()
        # Определим куда идти в приоритете с ветром
        for tmpPoint, tmpX, tmpY, tmpPath in tmp_vectors:
            if tmpPoint < 0 and tmpPath in self.wing:
                self.labY += tmpY
                self.labX += tmpX
                return self.sendAction("На " + tmpPath)
        # Определим куда идти в приоритете без ветра
        for tmpPoint, tmpX, tmpY, tmpPath in tmp_vectors:
            if tmpPoint < 0:
                self.labY += tmpY
                self.labX += tmpX
                return self.sendAction("На " + tmpPath)
        # Определим куда идти в возврате с ветром
        for tmpPoint, tmpX, tmpY, tmpPath in tmp_vectors:
            if tmpPath in self.wing:
                self.labY += tmpY
                self.labX += tmpX
                return self.sendAction("На " + tmpPath)
        # Перейдем в первую доступную без ветра
        for tmpPoint, tmpX, tmpY, tmpPath in tmp_vectors:
            self.labY += tmpY
            self.labX += tmpX
            return self.sendAction("На " + tmpPath)

    def doLeaveLabirint(self, _match: []):
        """ Уход с лабиринта """
        self.sendAction("Покинуть лабиринт")

    def doTreasureChest(self, _match: []):
        """ Найден сундук """
        self.sendAction("Открыть")

    def doTreasureWall(self, _match: []):
        """ Сокровище в стене """
        self.sendAction("Продолжить")

    def doTrapEasy(self, _match: []):
        """ Выполнение обработки ловушки без урона """
        self.sendAction("Продолжить")

    def doTrapHard(self, _match: []):
        """ Выполнение обработки ловушки с уроном """
        self.sendAction("Освободиться")

    def doFarmHerb(self, _match: []):
        """ Выполнение сбора травы """
        if self.config.gatherHell or not _match[1]:
            self.drop = self.DROP_WAIT
            self.sendAction("Собрать")
        return

    def doFarmRes(self, _match: []):
        """ Выполнение сбора дерева, камня, льна и железа """
        self.drop = self.DROP_SKIP
        self.sendAction("Добыть")

    def doFarmView(self, _match: []):
        """ Выполнение сбора обнаруженных объектов """
        if not ("Осмотреть" in self.actions):
            return
        self.drop = self.DROP_SKIP
        self.sendAction("Осмотреть")

    def doFarmCoat(self, _match: []):
        """ Выполнение сбора шкур """
        self.drop = self.DROP_SKIP
        self.sendAction("Освежевать")

    def doFightDead(self, _match: []):
        """ Бой завершен проигрышем """
        self.updateInjuries(True)
        self.skipBattle = False
        self.state = self.STATE_NONE

    def doFightEnd(self, _match: []):
        """ Бой завершен выигрышем """
        self.updateInjuries(_match[1])
        self.skipBattle = False
        self.state = self.STATE_NONE

    def doFightOnePunch(self, _match: []):
        """ Навыки запрещены, атака с руки """
        self.sendAction("Атака")

    def doFightStand(self, _match: []):
        """ Смена боевой стойки оружия """
        self.fight.isStand = False
        # В защитной стойке нет процента
        if _match[1]:
            self.fight.myAccuracy = self.toInt(_match[1])
        # Перейдем к следующему ходу
        self.doFightNext(_match)

    def doFightOneSkill(self, _match: []):
        """ Бой надо продолжить без повторных скиллов """
        self.fight.isStand = False
        self.doFightNext(_match)

    def doFightNoBag(self, _match: []):
        """ Зелья кончились """
        self.fight.myBag = False
        self.doFightNext(_match)

    def doFightPvpSkip(self, _match: []):
        """ Принятие перемирия """
        if not self.config.warrior:
            self.send("Подтвердить")

    def doMushroom(self, _match: []):
        """ Съеден гриб на восстановление здоровья """
        self.fight.myLoHp = self.toInt(_match[1])
        self.fight.myHiHp = self.toInt(_match[2])
        self.fight.myPercent = self.toInt(_match[3])
        self.doExploreDrop(None)

    def doNextLevel(self, _match: []):
        """ Принудительный переход по уровням """
        self.nextLevel = True

    def doFlower(self, _match: []):
        """ Съеден цветок с кристалом """
        self.doExploreDrop(None)

    def doExploreDrop(self, _match: []):
        """ Завершен подбор найденного ресурса """
        if not self.nextWay:
            return
        self.nextWay()
        self.nextWay = None

    def doExploreSpeed(self, _match: []):
        """ Учет скорости исследования """
        self.honger = self.toInt(_match[1])
        if _match[2]:
            self.sendAction("Обыскать")
        return

    def doExplore(self, _match: []):
        """ Выполнение обхода комнаты с ожиданием """

        def sub():
            """ Delayed action """
            if self.state == self.STATE_BATTLE:
                return
            # Определим сон
            if self.config.sleepHour and (datetime.today() + timedelta(self.config.utc)).hour in range(self.config.sleepHour, self.config.sleepHour + 1):
                return self.goPortal(self.STATE_SLEEP)
            # Определим голод
            if self.honger <= self.config.honger and datetime.today() > self.hongerTime:
                return self.goPortal(self.STATE_HONGER)
            # Задание выполнено
            if self.tasksDone:
                return self.goPortal()
            # Лимит троп
            if self.troph > self.config.trophLimit:
                return self.goPortal()
            # Определим инвентарь
            if self.inventory <= self.config.inventoryLow:
                return self.goPortal()
            # Определим травмы
            if self.injuries >= self.config.injuriesForHome:
                return self.goPortal()
            # Нужно ли спускаться
            if (self.config.goDown or self.nextLevel) and ("Глубже" in self.actions) and (
                    self.actions["Глубже"] == "positive"):
                self.nextLevel = False
                return self.sendAction("Глубже")
            # Нажмем
            if self.fight.myPercent > self.config.restHp:
                self.checkMaps()
                return self.sendAction("Исследовать уровень")
            else:
                return self.sendAction("Отдых")

        # Определим параметры
        self.troph = self.toInt(_match[1])
        self.fight.myLoHp = self.toInt(_match[2])
        self.fight.myHiHp = self.toInt(_match[3])
        self.fight.myPercent = self.toInt(_match[4])
        # Запустим поток с каллбаком
        self.doWaitRes(_match, sub)

    def doFightPvp(self, _match: []):
        """ Выполнение запуска боевки PVP """
        self.state = self.STATE_BATTLE
        self.match = _match
        self.fight.isInit = True
        self.fight.isPVP = True
        self.fight.isPeace = True
        self.fight.myBag = True
        self.fight.isStand = self.match[14]
        self.fight.enemyGuild = self.match[1]
        self.fight.enemyAttack = self.toInt(self.match[2])
        self.fight.enemyArmor = self.toInt(self.match[3])
        self.fight.myAccuracy = self.toInt(self.match[4])
        self.fight.myConcentration = self.toInt(self.match[5])
        self.fight.enemyLoHp = self.toInt(self.match[6])
        self.fight.enemyHiHp = self.toInt(self.match[7])
        self.fight.enemyRegen = self.toInt(self.match[8])
        self.fight.enemyPercent = self.toInt(self.match[9])
        self.fight.myLoHp = self.toInt(self.match[10])
        self.fight.myHiHp = self.toInt(self.match[11])
        self.fight.myRegen = self.toInt(self.match[12])
        self.fight.myPercent = self.toInt(self.match[13])
        # Проведем бой если есть стойка
        self.doFightNext(_match)

    def doFightPve(self, _match: []):
        """ Выполнение запуска боевки PVE """
        self.state = self.STATE_BATTLE
        self.match = _match
        self.fight.myBag = True
        self.fight.isInit = True
        self.fight.isStand = True
        self.fight.isPVP = False
        self.fight.enemyLoHp = self.toInt(self.match[1])
        self.fight.enemyHiHp = self.toInt(self.match[2])
        self.fight.enemyPercent = self.toInt(self.match[3])
        self.fight.enemyAttack = self.toInt(self.match[4])
        self.fight.enemyArmor = self.toInt(self.match[5])
        self.fight.isElite = self.match[6] == "⭐"
        self.fight.enemySize = self.toInt(self.match[7])
        self.fight.myLoHp = self.toInt(self.match[8])
        self.fight.myHiHp = self.toInt(self.match[9])
        self.fight.myPercent = self.toInt(self.match[10])
        self.fight.myConcentration = self.toInt(self.match[11])
        self.fight.myAccuracy = self.toInt(self.match[12])
        self.skipBattle = self.fight.isElite and (self.config.eliteChoice == 0)
        if self.skipBattle:
            return self.alert("Walker elite found")
        # Проведем бой
        self.doFightNext(_match)

    def doFightStep(self, _match: []):
        """ Выполнение боевки PVE """
        self.state = self.STATE_BATTLE
        self.match = _match
        # Инициализация
        self.fight.isInit = False
        self.fight.isStand = (not self.fight.isPVP and not self.match[6]) or (self.match[18])
        # Удалим кнопки скиллов при ускорении [6] или допов при рыке [9]
        if (self.match[6]) or (self.match[9]):
            tmp_actions = {}
            for tmp_key, tmp_value in self.actions.items():
                tmp_add = (tmp_key == "Блок щитом") or (tmp_key == "Яркий свет") or (tmp_key == "Прерывание")
                if tmp_add:
                    if not self.match[6]:
                        tmp_actions[tmp_key] = tmp_value
                else:
                    if (not self.match[9]) or (tmp_value != "primary"):
                        tmp_actions[tmp_key] = tmp_value
            self.actions = tmp_actions
        # Переберем параметры
        if self.match[1]:
            self.fight.myAccuracy = self.toInt(self.match[1])
        if self.match[2]:
            self.fight.myConcentration = self.toInt(self.match[2])
        if self.match[3]:
            self.fight.myBag = False
        if self.match[4]:
            self.fight.enemyArmor = self.toInt(self.match[4])
        if self.match[5]:
            self.fight.enemyArmor = self.toInt(self.match[5])
        if self.match[7]:
            self.injuries += 1
        if self.match[8]:
            self.injuries += 1
        self.fight.enemyLoHp = self.toInt(self.match[10])
        self.fight.enemyHiHp = self.toInt(self.match[11])
        self.fight.enemyRegen = self.toInt(self.match[12])
        self.fight.enemyPercent = self.toInt(self.match[13])
        self.fight.myLoHp = self.toInt(self.match[14])
        self.fight.myHiHp = self.toInt(self.match[15])
        self.fight.myRegen = self.toInt(self.match[16])
        self.fight.myPercent = self.toInt(self.match[17])
        # Проведем бой
        self.doFightNext(_match)

    def doFightNext(self, _match):
        """ Повтор хода """
        self.fight.myStand = self.getStand()
        if self.fight.isPVP:
            if not self.fight.myStand:
                return
            if self.fight.isPeace and not self.config.warrior:
                self.fight.isPeace = False
                self.sendAction("Перемирие")
                self.sleep(random.randint(10000, 15000) // 1000, "перемирия")
        # Проведем бой
        if self.config.battle(self.actions, self.sendAction, self.fight):
            return
        # Если бой не проведен - уведомими
        print(self.actions)
        self.alert("Walker no fight buttons found")
