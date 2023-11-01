import time
import openai
import os, pickle
import traceback
from typing import List
import numpy as np

if os.path.exists('./cache/ebd.pickle'):
    with open('./cache/ebd.pickle', 'rb') as f:
        cache = pickle.load(f)
else:
    cache = {}


def cal_embedding(text, model_name='text-embedding-ada-002'):
    if type(text) == str:
        return cal_embedding([text], model_name)[0]
    to_call_text = [x for x in text if x not in cache]
    if len(to_call_text) > 0:
        while True:
            try:
                result = openai.Embedding.create(
                    model=model_name,
                    input=to_call_text
                )
                break
            except Exception as e:
                traceback.print_exc()
                time.sleep(2)

        for idx, d in enumerate(result['data']):
            cache[to_call_text[idx]] = d['embedding']
        with open('./cache/ebd.pickle', 'wb') as f:
            pickle.dump(cache, f)
    return [cache[x] for x in text]


def cal_similarity(v1, v2):
    vec1 = np.array(v1)
    vec2 = np.array(v2)
    return vec1.dot(vec2) #/ (np.linalg.norm(vec1) * np.linalg.norm(vec2))

def sort_by_similarity(q: str, a_list: List[str]):
    q_ebd = cal_embedding(q)
    a_ebds = cal_embedding(a_list)

    extend_a = [(a, cal_similarity(q_ebd, a_ebd)) for a, a_ebd in zip(a_list, a_ebds)]
    return extend_a
def cal_similarity_one(q:str, a:str):
    q_ebd = cal_embedding(q)
    a_ebd = cal_embedding(a)
    return cal_similarity(q_ebd, a_ebd)
if __name__ == '__main__':
    q = '''
system:
You are a mobile UI expert acting as a "Judger". Your specialized role focuses on guiding the user to complete the user task on specific UI screen.
Your job is to choose the next UI element to be operated considering the user task, the history operation sequence, and the current UI. You should rate the available UI elements on the current page.

Task: "enable phone call & SMS for the user named Alice".
History operation sequence: [].
Current UI:
\'\'\'HTML
<p class='android:id/title'  > Storage </p>
<p class='android:id/summary'  > 37% used - 5.02 GB free </p>
<div id=1 class=''  > Storage
    <p> 37% used - 5.02 GB free </p> </div>
<p class='android:id/title'  > Privacy </p>
<p class='android:id/summary'  > Permissions, account activity, personal data </p>
<div id=2 class=''  > Privacy
    <p> Permissions, account activity, personal data </p> </div>
<p class='android:id/title'  > Location </p>
<p class='android:id/summary'  > On - 5 apps have access to location </p>
<div id=3 class=''  > Location
    <p> On - 5 apps have access to location </p> </div>
<p class='android:id/title'  > Security </p>
<p class='android:id/summary'  > Screen lock, fingerprint </p>
<div id=4 class=''  > Security
    <p> Screen lock, fingerprint </p> </div>
<p class='android:id/title'  > Accounts </p>
<p class='android:id/summary'  > Google </p>
<div id=5 class=''  > Accounts
    <p> Google </p> </div>
<p class='android:id/title'  > Accessibility </p>
<p class='android:id/summary'  > Screen readers, display, interaction controls </p>
<div id=6 class=''  > Accessibility
    <p> Screen readers, display, interaction controls </p> </div>
<p class='android:id/title'  > Digital Wellbeing & parental controls </p>
<p class='android:id/summary'  > Screen time, app timers, bedtime schedules </p>
<div id=7 class=''  > Digital Wellbeing & parental controls
    <p> Screen time, app timers, bedtime schedules </p> </div>
<p class='android:id/title'  > Google </p>
<p class='android:id/summary'  > Services & preferences </p>
<div id=8 class=''  > Google
    <p> Services & preferences </p> </div>
<p class='android:id/title'  > System </p>
<p class='android:id/summary'  > Languages, gestures, time, backup </p>
<div id=9 class=''  > System
    <p> Languages, gestures, time, backup </p> </div>
<p class='android:id/title'  > About emulated device </p>
<p class='android:id/summary'  > sdk_gphone_x86_64 </p>
<div id=10 class=''  > About emulated device
    <p> sdk_gphone_x86_64 </p> </div>
\'\'\'
Please output the next element to be operated.
'''
#Successive results of current UI:
#{"<div id=1 class=''  > Storage\n    <p> 37% used - 5.02 GB free </p> </div>\n": {'description': '', 'comp': "('Storage-2.98 GB-Total used of 8.00 GB-DEVICE STORAGE-Internal shared storage-2.98 GB used of 8.00 GB-PORTABLE STORAGE-SDCARD-113 kB used of 535 MB',)"}, "<div id=2 class=''  > Privacy\n    <p> Permissions, account activity, personal data </p> </div>\n": {'description': '', 'comp': "('Privacy-Accessibility usage-1 app has full access to your device-Permission manager-Control app access to your data-Show passwords-Display characters briefly as you type-Notifications on lock screen-Show all notification content-Advanced-App content; Autofill service from Google; Google location history; Activity controls; Ads; Usage & diagnostics',)"}, "<div id=3 class=''  > Location\n    <p> On - 5 apps have access to location </p> </div>\n": {'description': '', 'comp': "('Location-Use location-Location may use sources like GPS; Wi‑Fi; mobile networks; and sensors to help estimate your device’s location. Google may collect location data periodically and use this data in an anonymous way to improve location accuracy and location-based services.-RECENT LOCATION REQUESTS-Google-See all-App access to location-5 of 14 apps have access to location-Wi‑Fi and Bluetooth scanning-Wi‑Fi scanning is on; Bluetooth scanning is off-Advanced-Emergency Location Service; Google Location Accuracy; Google Location History; Google Location Sharing',)"}, "<div id=4 class=''  > Security\n    <p> Screen lock, fingerprint </p> </div>\n": {'description': '', 'comp': "('Security-SECURITY STATUS-Google Play Protect-Find My Device-On-Security update-August 5; 2021-DEVICE SECURITY-Fingerprint-Device admin apps-No active apps-SIM card lock-Encryption & credentials-Screen lock-None-Smart Lock-To use; first set a screen lock',)"}, "<div id=5 class=''  > Accounts\n    <p> Google </p> </div>\n": {'description': '', 'comp': "('Accounts-ACCOUNTS FOR ADMIN-kinnplh@gmail.com-Google-laixiruyun@gmail.com-Google-Automatically sync app data-Let apps refresh data automatically-Add account',)"}, "<div id=6 class=''  > Accessibility\n    <p> Screen readers, display, interaction controls </p> </div>\n": {'description': '', 'comp': "('Privacy-Accessibility usage-1 app has full access to your device-Permission manager-Control app access to your data-Show passwords-Display characters briefly as you type-Notifications on lock screen-Show all notification content-Advanced-App content; Autofill service from Google; Google location history; Activity controls; Ads; Usage & diagnostics',)"}, "<div id=7 class=''  > Digital Wellbeing & parental controls\n    <p> Screen time, app timers, bedtime schedules </p> </div>\n": [], "<div id=8 class=''  > Google\n    <p> Services & preferences </p> </div>\n": {'description': '', 'comp': "('Accounts-ACCOUNTS FOR ADMIN-kinnplh@gmail.com-Google-laixiruyun@gmail.com-Google-Automatically sync app data-Let apps refresh data automatically-Add account',)"}, "<div id=9 class=''  > System\n    <p> Languages, gestures, time, backup </p> </div>\n": {'description': '', 'comp': "('System-Languages\\xa0& input-Gboard-Gestures-Date & time-GMT+00:00-Backup-Off-Advanced-Reset options; Multiple users; Developer options; System update',)"}, "<div id=10 class=''  > About emulated device\n    <p> sdk_gphone_x86_64 </p> </div>\n": {'description': '', 'comp': "('Accounts-ACCOUNTS FOR ADMIN-kinnplh@gmail.com-Google-laixiruyun@gmail.com-Google-Automatically sync app data-Let apps refresh data automatically-Add account',)"}}

    a_list = [
        '<div id=1 class=''  > Storage <p> 37% used - 5.02 GB free </p> </div>',
        '<div id=2 class=''  > Privacy <p> Permissions, account activity, personal data </p> </div>',
        '<div id=3 class=''  > Location <p> On - 5 apps have access to location </p> </div>',
        '<div id=4 class=''  > Security <p> Screen lock, fingerprint </p> </div>',
        '<div id=5 class=''  > Accounts <p> Google </p> </div>',
        '<div id=6 class=''  > Accessibility <p> Screen readers, display, interaction controls </p> </div>',
        '<div id=7 class=''  > Digital Wellbeing & parental controls <p> Screen time, app timers, bedtime schedules </p> </div>',
        '<div id=8 class=''  > Google <p> Services & preferences </p> </div>',
        '<div id=9 class=''  > System <p> Languages, gestures, time, backup </p> </div>',
        '<div id=10 class=''  > About emulated device <p> sdk_gphone_x86_64 </p> </div>'
    ]

    a_list = [
        'Storage <p> 37% used - 5.02 GB free </p>',
        'Privacy <p> Permissions, account activity, personal data </p>',
        'Location <p> On - 5 apps have access to location </p>',
        'Security <p> Screen lock, fingerprint </p>',
        'Accounts <p> Google </p>',
        'Accessibility <p> Screen readers, display, interaction controls </p>',
        'Digital Wellbeing & parental controls <p> Screen time, app timers, bedtime schedules </p>',
        'Google <p> Services & preferences </p>',
        'System <p> Languages, gestures, time, backup </p>',
        'About emulated device <p> sdk_gphone_x86_64 </p>'
    ]

    result = sort_by_similarity(q, a_list)
    result.sort(key=lambda x: -x[1])
    for x, y in result:
        print(x, y)
    