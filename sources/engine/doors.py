"""
Subclass for event doors
"""


class WalkerDoors:
    """ Answers for event doors"""

    def __init__(self, send: callable, register: callable, wait: callable, config: any):
        self.send = send
        self.wait = wait
        self.config = config
        register(self.doDoorAdms, r"перед которым расположены 4 рычага с именами Адмов")
        register(self.doDoorBottle, r"который отдается протяжным эхом: \"ВСЕ ИСПОЛЬЗУЮТ ЗЕЛЬЕ")
        register(self.doDoorColor, r"который отдается протяжным эхом: \"КАКОВ ЦВЕТ СЕРДЦА")
        register(self.doDoorElf, r"на крышке которого изображен тяжелораненый эльф")
        register(self.doDoorHeart, r"Где в настоящее время находится истинный спуск на путь к Сердцу Глубин")
        register(self.doDoorKings, r"Хтофтёмэд отфтпин")
        register(self.doDoorMap, r"Видимо, их нужно расставить по карте, чтобы сундук открылся")
        register(self.doDoorNames, r"На сундуке оставлены 3 практически стертых имени искателей приключений")
        register(self.doDoorQuit, r"какую из четырех Великих Рас никогда не примут в гильдию магов")
        register(self.doDoorRosa, r"В груди моей горел пожар, но сжег меня дотла")
        register(self.doDoorSarko, r"Сяэпьчео рущэр")
        register(self.doDoorStone, r"Видимо, этот камень нужно вложить в одну из вытянутых рук")
        register(self.doDoorWeapon, r"Докажи, что ты умеешь подбирать правильный подход к противнику")
        register(self.doDoorYear, r"Каждую плиту украшает символ, обозначающий конкретное время года")

    def doDoorNames(self, _match: []):
        """ Дверь """

        def sub():
            """ Delayed action """
            self.send("Гер")
            self.send("Натаниэль")
            self.send("Эмбер")

        self.wait(_match, sub)

    def doDoorKings(self, _match: []):
        """ Дверь """

        def sub():
            """ Delayed action """
            self.send("Сокровище королей")

        self.wait(_match, sub)

    def doDoorMap(self, _match: []):
        """ Дверь """

        def sub():
            """ Delayed action """
            self.send("Северо-восток")
            self.send("Северо-запад")
            self.send("Юг материка")

        self.wait(_match, sub)

    def doDoorQuit(self, _match: []):
        """ Дверь """

        def sub():
            """ Delayed action """
            self.send("Уйти")

        self.wait(_match, sub)

    def doDoorAdms(self, _match: []):
        """ Дверь """

        def sub():
            """ Delayed action """
            self.send("Грах")
            self.send("Ева")
            self.send("Трор")
            self.send("Смотритель")

        self.wait(_match, sub)

    def doDoorYear(self, _match: []):
        """ Дверь """

        def sub():
            """ Delayed action """
            self.send("Осень")
            self.send("Зима")
            self.send("Весна")
            self.send("Лето")

        self.wait(_match, sub)

    def doDoorHeart(self, _match: []):
        """ Дверь """

        def sub():
            """ Delayed action """
            self.send("Темнолесье")

        self.wait(_match, sub)

    def doDoorElf(self, _match: []):
        """ Дверь """

        def sub():
            """ Delayed action """
            self.send("Пещерный корень")
            self.send("Первозданная вода")
            self.send("Рыбий жир")

        self.wait(_match, sub)

    def doDoorBottle(self, _match: []):
        """ Дверь """

        def sub():
            """ Delayed action """
            self.send(str(self.config.memoryBottles))

        self.wait(_match, sub)

    def doDoorColor(self, _match: []):
        """ Дверь """

        def sub():
            """ Delayed action """
            self.send("Фиолетовый")

        self.wait(_match, sub)

    def doDoorWeapon(self, _match: []):
        """ Дверь """

        def sub():
            """ Delayed action """
            self.send("Разрезать мечом")
            self.send("Ударить молотом")
            self.send("Уколоть кинжалом")

        self.wait(_match, sub)

    def doDoorStone(self, _match: []):
        """ Дверь """

        def sub():
            """ Delayed action """
            self.send("Человек")

        self.wait(_match, sub)

    def doDoorSarko(self, _match: []):
        """ Дверь """

        def sub():
            """ Delayed action """
            self.send("Гробница веков")

        self.wait(_match, sub)

    def doDoorRosa(self, _match: []):
        """ Дверь """

        def sub():
            """ Delayed action """
            self.send("Роза")

        self.wait(_match, sub)
