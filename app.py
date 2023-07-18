from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from get_tugas_dl import run_get_tugas
import requests
import io,sys
import traceback
import pymongo
import base64

class XOR :
    def encrypt(val, key = "secr3atC0d3") :
        res = ""

        for index, value in enumerate(val) :
            res += chr(ord(value) ^ ord(key[index % len(key)]) )

        return base64.b64encode(res.encode()).decode()

    def decrypt(cipher, key = "secr3atC0d3") :
        res = ""

        cipher = base64.b64decode(cipher.encode()).decode()

        for index, value in enumerate(cipher) :
            res += chr(ord(value) ^ ord(key[index % len(key)]))

        return res

class CRUD :
    def __init__(self) :
        self.client = pymongo.MongoClient("USE-YOUR-OWN-MONGO-CLIENT-KEY")
        self.db = self.client["user-moodle-bot"]
        self.user = self.db["user"]

    def update_one(self, primary_key, key, val, operator = "$set") :
        filteer = {
            "wa_id" : primary_key
        }

        query = {
            operator : {
                key : val
            }
        }

        try :
            self.user.update_one(filteer, query)
        except Exception as e :
            print("Gagal", e)

    def find_one(self, find_val, ret_val = None) :
        query = {
            "wa_id" : find_val
        }
        get_find = ""

        try :
            get_find = self.user.find_one(query)
        except Exception as e :
            print("Gagal", e)

        return get_find if not ret_val else get_find.get(ret_val) if get_find.get(ret_val) else ""

    def insert_one(self, key, val) :
        query = {
            key : val
        }

        try :
            get_find = self.user.insert_one(query)
        except Exception as e :
            print("Gagal", e)

    def delete_one(self, key, val) :
        query = {
            key : val
        }

        try :
            get_find = self.user.delete_one(query)
        except Exception as e :
            print("Gagal", e)


class Capturing(list):
    def __enter__(self):
        self._stdout = sys.stdout
        sys.stdout = self._stringio = io.StringIO()
        return self
    def __exit__(self, *args):
        self.extend(self._stringio.getvalue().splitlines())
        del self._stringio    # free up some memory
        sys.stdout = self._stdout

def inputAkun(wa_id, aksi, user_msg) :
    if not aksi :
        aksi = "Ketik Univ"
        crud.update_one(wa_id, "action", aksi)

    elif aksi == "Ketik Univ" :
        aksi = "Masukkan Username"
        crud.update_one(wa_id, "url", user_msg)
        crud.update_one(wa_id, "action", aksi)

    elif aksi == "Masukkan Username" :
        aksi = "Masukkan Password"
        crud.update_one(wa_id, "username", user_msg)
        crud.update_one(wa_id, "action", aksi)

    else :
        aksi = "Akun berhasil ditambahkan!\nUntuk melihat tugas deadline ketik \"mulai\" dan pilih No.2"
        crud.update_one(wa_id, "password", XOR.encrypt(user_msg) )
        crud.update_one(wa_id, "menu_action", "", "$unset")
        crud.update_one(wa_id, "action", "", "$unset")

    return aksi

def lihatTugas(wa_id) :
    crud.update_one(wa_id, "menu_action", "", "$unset")
    crud.update_one(wa_id, "action", "", "$unset")
    value = None
    data = crud.user.find_one( {"wa_id" : wa_id}, { "username" : 1, "password" : 1, "url" : 1, "_id" : 0 } )

    if not data :
        value = "Akun belum ditambahkan silahkan ketik \"mulai\"\nlalu pilih No. 1 untuk menambahkan akun baru"
    else :
        try :
            username = data["username"]
            password = XOR.decrypt(data["password"])
            url = data["url"]
            value = run_get_tugas(username, password, url)
        except Exception as e :
            value = f"Server Error Silahkan Coba Lagi!\n{e}"

    return value

def lihatAkun(wa_id) :
    crud.update_one(wa_id, "menu_action", "", "$unset")
    crud.update_one(wa_id, "action", "", "$unset")

    data = crud.user.find_one(
        {"wa_id" : wa_id},
        { "username" : 1, "url" : 1, "password" : 1, "_id" : 0 }
    )
    res = "Akun Univ\n\n"

    if data :
        for key, val in data.items() :
            res += key + " : " + val + "\n"
    else :
        res += "Akun belum ditambahkan silahkan ketik \"mulai\"\nlalu pilih No. 1 untuk menambahkan akun baru"

    return res

## Init Flask APp
app = Flask(__name__)
crud = CRUD()

@app.route('/bot', methods=['POST'])
def bot():
    ## Get user message
    user_msg = request.values.get("Body", "")
    wa_id = request.values.get("WaId", "")

    if not crud.find_one(wa_id) :
        crud.insert_one("wa_id", wa_id)

    ## Init bot response
    bot_resp= MessagingResponse()
    msg = bot_resp.message()

    # Applying bot logic
    if "mulai" == user_msg.lower() :
        body_msg = f"""
BOT WHATSAPP JADWAL DEADLINE TUGAS UNIV.GUNADARMA

kontak ke saya jika terdapat masalah dalam penggunaan bot,
ke https://wa.me/+6281818475959 atau bisa join ke grup whatsapp
untuk diskusi bersama ke link https://chat.whatsapp.com/J0z6x3dRDNRDhkPPK2HR3f

MENU
1. Reset/Tambah Akun Univ
2. Lihat Tugas Deadline
3. Lihat Akun Univ"""
        crud.update_one(wa_id, "menu_action", "menu_utama", "$set")
        crud.update_one(wa_id, "action", "", "$unset")
        msg.body(body_msg)

    elif "menu_utama" in crud.find_one(wa_id, "menu_action") :

        if crud.find_one(wa_id, "menu_action") == "menu_utama" :
            crud.update_one(wa_id, "menu_action", "menu_utama_" + user_msg)

        menu_action = crud.find_one(wa_id, "menu_action")

        if menu_action == "menu_utama_1" :
            aksi = crud.find_one(wa_id, "action")
            body_msg = inputAkun(wa_id, aksi, user_msg)
        elif menu_action == "menu_utama_2" :
            body_msg = lihatTugas(wa_id)
        elif menu_action == "menu_utama_3" :
            body_msg = lihatAkun(wa_id)
        else :
            crud.update_one(wa_id, "menu_action", "", "$unset")
            body_msg = "Menu tidak dikenal silahkan masukkan dengan benar!\nUlangi dengan mengetik \"mulai\" pada chat"

        msg.body(body_msg)

    elif "python3" in user_msg.lower() :
        try :
            r = requests.post(
                f"https://{request.host}/api",
                data = {
                    'msg' : user_msg
                },
                timeout = 8
            )
            result = {
                'eval_code' : r.json()['eval_code'],
                'error_eval' : r.json()['error_eval']
            }
        except :
            result = {
                'eval_code' : 'None',
                'error_eval' : traceback.format_exc().splitlines()[-1]
            }
        msg.body(f'Result : \n{result.get("eval_code")} \n\nError : \n{result.get("error_eval")}')

    else :
        msg.body("Maaf perintah tidak dikenal" + "\n" + 'untuk memulai ketik "mulai"')

    return str(bot_resp)

@app.route('/api', methods=['POST'])
def api() : 
    if request.values.to_dict()['msg'] :
        error_eval,eval_code = "None","None"
        msg = request.values.to_dict()['msg']
        try :
            with Capturing() as eval_code : 
                exec(
                    '\n'.join(msg.splitlines()[1::]),globals(),globals()
                )
        except :
                error_eval = traceback.format_exc()

        return {'error_eval' : error_eval , 'eval_code' : '```' + '\n'.join(eval_code) + '```' }
    return 'None'

if __name__ == '__main__' :
    app.run(debug=True)
