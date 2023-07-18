import requests
from bs4 import BeautifulSoup
import os

def login_credentials(token,username,password):
    return {
        'logintoken': token,
        'username': username,
        'password': password
     }

def get_sesskey(MoodleSession,url):
    session = requests.Session()
    sess_key_url = f'https://{url}/calendar/export.php?'
    form_key = MoodleSession.get(sess_key_url)
    soup = BeautifulSoup(form_key.content, 'html.parser')
    return soup.find('input', attrs={'name': 'sesskey'})['value']

def get_cookie_key(username,password,urls):
    headers = {'Connection': "keep-alive"}
    with requests.Session() as s:
        url = f'https://{urls}/login/index.php'
        secure = f'https://{urls}/my/'
        if not os.path.isfile('./somefile') or os.path.isfile('./somefile'):
            init = s.get(url)
            soup = BeautifulSoup(init.content, 'html.parser')
            data = login_credentials(soup.find('input', attrs={'name': 'logintoken'})['value'],username,password)
            s.post(url, data=data, headers=headers, cookies=s.cookies)
            s.get(secure)
            return [s.cookies, get_sesskey(s,urls)]

def run_get_tugas(username,password,url):
    data = {
                "url": 'https://' + url + '/lib/ajax/service.php',
                "headers": {
                    "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:96.0) Gecko/20100101 Firefox/96.0",
                    "Accept": "application/json, text/javascript, */*; q=0.01",
                    "Accept-Language": "pt-BR,pt;q=0.8,en-US;q=0.5,en;q=0.3",
                    "Accept-Encoding": "gzip, deflate, br",
                    "Content-Type": "application/json",
                    "X-Requested-With": "XMLHttpRequest",
                    "Connection": "keep-alive"
                    },
                "body": [{
                    "index": 0,
                    "methodname": "core_calendar_get_action_events_by_timesort",
                    "args": {
                        "timesortfrom": 1649869200, 
                        "limittononsuspendedevents": True
                    }
                }]
            }

    credentials = get_cookie_key(username,password,url)
    calendar = requests.post(
        data['url'],
        params={'sesskey': credentials[1], 'info': 'core_calendar_get_action_events_by_timesort'},
        headers=data['headers'],
        cookies=credentials[0],
        json=data['body']
    ).json()

    konten = calendar[0]['data']['events']

    link = list()
    for index, tugas in enumerate(konten) :
        waktu_html = BeautifulSoup(tugas['formattedtime'],'html.parser')
        waktu = (' on ' + waktu_html.get_text())
        link.append(
            str(
                '\n' + str(index + 1) + '\n' + tugas['course']['fullname'] +
                '\n\n' + tugas['name'] + waktu + '\n' +
                tugas['action']['name'] +
                ' ON ' +
                tugas['action']['url'] + '\n'
            )
        )

    if link :
        return ''.join(link)
    return 'Tidak ada tugas dalam daftar'
