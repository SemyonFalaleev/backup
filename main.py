import requests
import json
import configparser
import datetime
from tqdm import tqdm
config = configparser.ConfigParser()

class VKApi():
    """Класс VKApi создан для работы с API VK
    При создании класса необходимо ввести параметр login - 
    - Этот параметр создаст ячейку в фаул setting.ini, который хранит
    защещённые данные , такие как токены доступа и id вконтакте.
    - Если ранее такой логин уже вводился, то все методы класса будут 
    использовать введённые ранее переменные, которые храняться в файле
    setting.ini 
    Для корректной работы методов класса, необходимо указать корректный
    secure_token для VK API, это можно сделатьуказав токен в файле 
    setting.ini в формате:
    [vk_api] 
    secure_token = "токен"
    Либо если он не указан можно ввести его во время первого запуска
    программы.
    """

    base_url = "https://api.vk.com/method/"

    def __init__(self, login):
        self.login = login
        self.__check_secure_token()

    def __check_secure_token(self):
        """Этот метод проверяет наличие в файлу setting.ini
        secure_tokena для VK API, записанного в таком формате: 
        [vk_api] 
        secure_token = "токен"
        """
        try:
            config["vk_api"]["secure_token"]
        except LookupError:
            config.add_section("vk_api")
            config.set("vk_api", 'secure_token',
            f'{input("Введите secure_token для API VK: ")}')
            with open('setting.ini', 'w') as config_file:
                config.write(config_file)
              
    def __same_name_check(self, photos_names_list, photos_json):
        """Этот метод нужен для присваивания фотогрфиям с одинаковыми 
        именами дополнительно к их имени, дату загрузки фотографии в ВК.
        Это происходит посредством добавления в
        конец списока содержащего необходимую ссылку,
        даты загрузки фотографии в формате: dd_mm_YY
        Метод принимает на вход: 
        - 'photos_names_list': список состоящий из списков формата:
        [url, кол-во лайков(int), размер фото(str)]
        - 'photos_json': json объект содержащий формат ответа VK API на
        запрос photos.get
        Метод выдаёт: список состоящий из списков формата:
        Если внутри основного списка есть списки в одинаковыми значениями
        'кол-во лайков', то каждый такой элемент будет заменён на такой же
        список но с добавленной вконце датой загрузки фотографии.
        Индекс списка в главном списке не измениться. 
        Остальные елементы(списки) остануться нетронутыми 
        Пример изменённого элемента:
        [url, кол-во лайков(int), размер фото(str), 
        дата загрузки в формате dd_mm_YY(str)]
        """
        uniq_name_list = []
        for indx,name in enumerate(photos_names_list):
            items_list = photos_json["response"]['items'][indx]
            check_element = photos_names_list.pop(indx)
            if any(name[1] in photo_name for photo_name in photos_names_list):
                name.append(datetime.datetime.fromtimestamp
                (items_list['date'],datetime.UTC).strftime('%d_%m_%Y'))
                uniq_name_list.append(name)
                photos_names_list.insert(indx, check_element)
            else:
                uniq_name_list.append(name)
                photos_names_list.insert(indx, check_element)
        return uniq_name_list
    
    def __album_selection(self):
        """Этот метод необходим для выбора из какого 
        альбома будут загружены фотографии
        Этот метод вызвывает функцию Input, которая должна принять
        одно из 2х значений:
        '1' - в таком случае метод вернёт объект str: 'profile'
        '2' - в таком случае метод вернёт объект str: 'wall'
        Если будет введено любое другое значение, функция input
        будет вызываться до тех пор, пока не будет введено одно из 
        необходимых значений
        """
        album_id = input("Выберите альбом для скачивания"
                         ":\nВведите '1' для загрузки аваторок "
                         "или '2' для загрузки фотографий со стены\n:")
        count = 0
        while count == 0:
            if album_id == "1":
                album_id = "profile"
                break
            elif album_id == "2":
                album_id = "wall"
                break
            else:
                album_id = input("Выберите альбом для скачивания"
                        ":\nВведите '1' для загрузки аваторок "
                        "или '2' для загрузки фотографий со стены\n:")
        return album_id   
    
    def __save_photo_info(self, photos_list):
        """Этот метод необходим для создания json файла содержащего
        информацию о фотографиях полученных с помощью метода 'photo_get'
        На вход функция принимает:
        'photos_list' - список из списков формата: 
        [[url, кол-во лайков(int), размер фото(str), ...], ...]
        Ничего не возвращает, а создаёт файл 'photo_info.json',
        который содержит информацию в формате:
        [{
        "file_name": "34.jpg",
        "size": "z"
        }]
        """
        dict_name_list = []
        for photo in photos_list:
            if len(photo) == 3:
                dict_name = {}
                dict_name["file_name"] = f'{photo[1]}.jpeg'
                dict_name["size"] = photo[2]
                dict_name_list.append(dict_name)
            elif len(photo) == 4:
                dict_name = {}
                dict_name["file_name"] = f'{photo[1]}|{photo[3]}.jpeg'
                dict_name["size"] = photo[2]
                dict_name_list.append(dict_name)
        with open("photo_info.json", "w") as file:
            file.write(json.dumps(dict_name_list))
    
    def _max_photo_quality(self, photos_json):
        """Этот метод нужен чтобы преобразовывать json объект в список
        из списков содержащих :
        [
        url ссылка на фото в максимальном качестве(размер),
        кол-во лайков(int), 
        размер фото(str)
        ]
        Внутри этого метода используется метод '__same_name_check'
        На вход функция принимает: 
        'photos_json' - json объект формата
        ответа на запрос к VK API с помощью метода photos.get
        Возвращает: 
        - список состоящий из списков формата:
        [[url, кол-во лайков(int), размер фото(str), ...], ...]
        Если внутри основного списка есть списки в одинаковыми значениями
        'кол-во лайков', то каждый такой элемент будет заменён на такой же
        список но с добавленной вконце датой загрузки фотографии.
        Индекс списка в главном списке не измениться. 
        Остальные елементы(списки) остануться нетронутыми 
        Пример изменённого элемента:
        [url, кол-во лайков(int), размер фото(str), 
        дата загрузки в формате dd_mm_YY(str)]
        """
        max_quality_list = []
        count = 0
        for x in range(photos_json["response"]["count"]):
            items_list = photos_json["response"]['items'][count]
            max_size = [[x["url"], items_list["likes"]["count"], x["type"]] 
                        for x in items_list['sizes'] if x["type"] == "w"]
            if max_size == []:
                max_size = [[x["url"], items_list["likes"]["count"], x["type"]] 
                            for x in items_list['sizes'] if x["type"] == "z"]
            if max_size == []:
                max_size = [[x["url"], items_list["likes"]["count"], x["type"]] 
                            for x in items_list['sizes'] if x["type"] == "y"] 
            max_quality_list.extend(max_size)
            count += 1
        return self.__same_name_check(max_quality_list, photos_json)
    
    def photo_get(self, number_photo = 5, album_id='profile'):
        """Этот метод нужен для обращения к методу photos.get VK API
        Для корректного исполнения метода, необходимо указать корректный
        id странички ВК во время создания объекта класса, к которому 
        применяется метод
        Внутри этого метода используются защещённые методы:
        '__album_selection'
        '__save_photo_info'
        '_max_photo_quality'
        Функия принимаетна вход:
        -Номер сколько фото необходимо загрузить, по умолчанию 5
        -Название альбома из которого необходимо загрузить фото
        Функция выдаёт:
        - Создаёт json файл с информацией о полученных фото, метод:
        '__save_photo_info'
        -Вовзращает список из списков формата: 
        [[url, кол-во лайков(int), размер фото(str), ...], ...]
        метод: '_max_photo_quality'
        '"""
        number_photo = int(
        input("Сколько фотографий необходимо загрузить на диск?\n"
        "Укажите число: "))
        album_id = self.__album_selection()
        method = "photos.get/"
        config.read("setting.ini")
        params = {"access_token": config["vk_api"]["secure_token"],
                  "extended": 1,
                  "photo_sizes": 1,
                  "owner_id": config[self.login]["id"],
                  "album_id": album_id,
                  "v": 5.199,
                  "count": number_photo
                  }
        response = requests.get(f"{self.base_url}{method}",
                                 params=params).json()
        if response['response']['count'] < number_photo:
            self.__save_photo_info(self._max_photo_quality(response))
            return self._max_photo_quality(response)
        else:
            response['response']['count'] = number_photo
            self.__save_photo_info(self._max_photo_quality(response))
            return self._max_photo_quality(response)

class YADisck:
    """Класс YADisk создан для работы с API Яндекс диска
    При создании класса необходимо ввести параметр login - 
    - Этот параметр создаст ячейку в фаул setting.ini, который хранит
    защещённые данные , такие как токены доступа и id вконтакте.
    - Если ранее такой логин уже вводился, то все методы класса будут 
    использовать введённые ранее переменные, которые храняться в файле
    setting.ini 
    Для корректной работы методов класса, необходимо указать корректный
    token доступа для Яндекс диска, это можно сделать при создании профиля
    (указав ранее неиспользуемый логин) либо если он был указан неккоректно
    его можно изменить в файле setting.in в формате:
    [login] 
    token = "токен"
    """
    base_url = "https://cloud-api.yandex.net"

    def __init__(self, login):
        self.login = login
    
    def _create_a_folder(self):
        """Этот метод необходим для создания папки на яндекс диске
        которая будет называться:
        'Photo_{логин указанный при создании объекта класса}'
        Для корректной работы функции , должен быть указан корректный
        токен для Яндекс диска при создании объёкта класа, иначе 
        программа будет предлогать ввести корректный токен до тех пор
        пока он не будет получен.
        Функция ничего не принимает и ничего не возвращает"""
        method = "/v1/disk/resources"
        params = {"path": f"Photo_{self.login}"}
        headers = {'Authorization': config[self.login]["token"]}
        response = requests.put(self.base_url+method,
                                params=params, 
                                headers=headers)
        while response.status_code == 400 or response.status_code == 401:
            token = input("Введённый токен для Яндекс диска неккоректный,"
                          " введите корректный токен: ")
            config.set(self.login, "token", token)
            with open('setting.ini', 'w') as config_file:
                config.write(config_file)
            headers = {'Authorization': config[self.login]["token"]}
            response = requests.put(self.base_url+method,
                                params=params, 
                                headers=headers)
        
    def upload_photo(self, get_photo_list):
        """Этот метод нужен для загрузки фотографий
        из 'get_phot_list' в папку созданную методом
        '_create_a_folder' на Яндекс диске.
        использует приватный метод '_create_a_folder'
        Принимает на вход: 'get_phot_list' список формата:
        [[url, кол-во лайков(int), размер фото(str), ...], ...]
        предпологается что он будет получен с помощью метода 
        'photo_get' объекта класса VKApi
        Выдаёт: 
        Создаёт папку и загружает в неё фото
        Выводит на экран прогресс бар, который визуализирует процесс
        загрузки фотографий на диск.
        """
        self._create_a_folder()
        method = "/v1/disk/resources/upload"
        headers = {'Authorization': config[self.login]["token"]}
        for indx, photo in enumerate(tqdm((get_photo_list))):
            if len(photo) <= 3:
                params = {"path": f"Photo_{self.login}/{photo[1]}",
                          "url": photo[0]}
                response = requests.post(self.base_url+method,
                                         params=params, headers=headers)
            else:
                params = {"path": f"Photo_{self.login}/{photo[1]},{photo[3]}",
                              "url": photo[0]}
                response = requests.post(self.base_url+method,
                                         params=params, headers=headers)

class Profile():
    """Класс Profile необходим для связи объектов класса VKApi и YADisk
    При создании объекта класса Profile, он создаёт внутри своих 
    атрибутов self.vk_api -  объект класса VKAp и self.ya_disk - 
    объект класса YADisck с единным логином. Это значит что в защещённом 
    файле setting.ini будут храниться данные связанные данные профиля,
    пользователь программы сможет сохранить несколько разных профилей и 
    использовать методы классов VKApi и YADisk со значениями параметров 
    заданными для конкретного логина.
    """
    def __init__(self):
        """Во время создания объекта пользователю предлгается ввести
        логин, если логин был уже ранее зарегестрирован в системе 
        будет выведенно на экрна: 'Ваш профиль авторизован'
        Если ранее такой логин не был использован, то будет предложенно
        ввести id от странички VK (необходимо для корректной работы 
        методов класса VKApi) и токен от Яндекс ДИска (необходимо для 
        корректной работы методов класса YADisk' и на экран будет 
        выведенно: 'Ваш профиль зарегестрирован'.
        """
        self.login = input("Введите логин: ")
        config.read("setting.ini")
        if config.has_section(self.login):
            self.__check_id()
            self.__check_token()
            print("Ваш профиль авторизован")
        else:
            config.add_section(self.login)
            self.__append_id()
            self.__append_token()
            print("Ваш профиль зарегестрирован")
        self.vk_api = VKApi(self.login)
        self.ya_disk = YADisck(self.login)

    def __check_id(self):
        """"Этот метод нужен для провреки есть ли у данного логина 
        ключь и значение 'id' в файле setting.ini, если его нет 
        то используется метод '__append_id', который добавляет в файл
        setting.ini   ключь и значение 'id'.
        """
        try:
            config[self.login]["id"]
        except LookupError:
            self.__append_id()
    
    def __append_id(self):
        """добавляет в файл
        setting.ini   ключь и значение 'id'
        """
        config.set(self.login, 'id', f'{input("Введите id профиля ВК: ")}')
        with open('setting.ini', 'w') as config_file:
            config.write(config_file)

    def __check_token(self):
        """"Этот метод нужен для провреки есть ли у данного логина 
        ключь и значение 'token' в файле setting.ini, если его нет 
        то используется метод '__append_token', который добавляет в файл
        setting.ini   ключь и значение 'token'.
        """
        try:
            config[self.login]["token"]
        except LookupError:
            self.__append_token()
    
    def __append_token(self):
        """добавляет в файл
        setting.ini   ключь и значение 'token'
        """
        config.set(self.login, 'token', 
        f'{input("Введите token от Яндекс Диска: ")}')
        with open('setting.ini', 'w') as config_file:
            config.write(config_file)

prof_1 = Profile()

prof_1.ya_disk.upload_photo(prof_1.vk_api.photo_get())



