# Helper dla Admina

## Setup bota

przykład pliku .env znajduje się w `.env.example`
* w miejsce **DISCORD_TOKEN** wpisz token wygenerowany na portalu developera discord dla aplikacji bota. 
* w miejsce **GITHUB_TOKEN** wpisz token wygenrowany na https://github.com/settings/personal-access-tokens daj mu dostęp do czytania Pull Requests.



## Jak zmienić datę i czas wysyłki Notek?

wejdź w `services/scheduler_service.py` i zmień WEEKLY_SEND_WEEKDAY oraz WEEKLY_SEND_HOUR.

## Komendy Bota

Komendy w bocie są podzielone na trzy poziomy (Dostępne w zaleności od posiadanej DISCORD roli)

Dla członka organizacji MEMBER_ROLE_ID / Opiekuna koła SUPERVISOR_ROLE_ID:
* `create_event` - stwórz event zarówno w db bota jak i w kalendarzu podpiętym do bota (GOOGLE_CALENDAR_ID)
* `events` - wyświetl listę wszystkich nadchodzących wydarzeń w kalendarzu podpiętym do bota
* `horoscope` - wyświetl horoskop na dzisiaj dla wybranego znaku zodiaku. (https://freehoroscopeapi.com/api/v1/get-horoscope/daily)
* `meme` - wyświetl losowy mem z folderu `memes/`
* `ping` - Pong!

Dla zarządu: MANAGEMENT_ROLE_ID:
* `note` - Kompleksowa komenda do tworzenia/usuwania/zarządzania Notkami, które są wysyłane co tydzień do subkrybentów

Dla admina bota BOT_ADMIN_ROLE_ID:
* `subscribe` - subskrybuje podany email na notki
* `unsubscribe` - usuwa subskrybcje
* `subscribers` - pokazuje listę maili zasubskrybowanych na notki

## Jak działa Baza Danych?

Baza danych uzyta w projekcie to `sqlite`, więc jest to po prostu plik .db w folderze `data/`. Możesz ją odtworzyć za pomocą komendy `sqlite` w terminalu. 

Backupy wykonują się co tydzień, znajdziesz je w data/backups/

## Token do GH!

obecny token wygasa 30 Lipca 2027, trzeba go odnowić potem.

## WAŻNE UWAGI! 

Map rola: rola na serwerze/uprawnienia
* Member - Członek KN ALGO 
* Supervisor - Opiekun KN ALGO
* Management - Zarząd KN ALGO
* Bot Admin - Administrator

