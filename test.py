
import openai
openai.api_key = "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"

intention = [
    {"role": "system",
     "content": """You are a highly intelligent assistant capable of deriving and predicting GUI interface information. You would be given a page and the selected components, you should predict the after-page."""},
    {"role": "user",
     "content": """The page:['1{}-{}-{More function buttons}-{Tab}', '2{}-{}-{Search}-{Tab}', '3{Me}-{Me}-{}-{Tab}', '4{Discover}-{Discover}-{}-{Tab}', '5{Contacts}-{Contacts}-{}-{Tab}', '6{Bowen}-{Bowen,3/22/23,398178}-{}-{}']."""},
    {"role": "assistant",
     "content": """After-page:{"1{}-{}-{More function buttons}-{Tab}":['1{Money}-{Money}-{}-{}', '2{Scan}-{Scan}-{}-{}', '3{Add Contacts}-{Add Contacts}-{}-{}', '4{New Chat}-{New Chat}-{}-{}'],
     "2{}-{}-{Search}-{Tab}":['1{页面设置}-{页面设置}-{}-{}', '2{Channels}-{Channels}-{}-{}', '3{Mini Programs}-{Mini Programs}-{}-{}', '4{Official Accounts}-{Official Accounts}-{}-{}', '5{Moments}-{Moments}-{}-{}', '6{Cancel}-{Cancel}-{Cancel button}-{Title}', '7{Search}-{Search}-{}-{}'],
     "3{Me}-{Me}-{}-{Tab}":['1{Me}-{Me}-{}-{Tab}', '2{Discover}-{Discover}-{}-{Tab}', '3{Contacts}-{Contacts}-{}-{Tab}', '4{Chats}-{Chats}-{}-{Tab}', '5{Settings}-{Settings}-{}-{}', '6{Sticker Gallery}-{Sticker Gallery}-{}-{}', '7{My Posts}-{My Posts}-{}-{}', '8{Favorites}-{Favorites}-{}-{}', '9{Services}-{Services}-{}-{}', "10{}-{}-{Friends' Status}-{}", '11{Status}-{Status}-{Add Status}-{}', '12{}-{}-{My QR Code}-{Tab}', '13{Weixin ID: saltyp0}-{Weixin ID: saltyp0}-{}-{Title}'],
     "4{Discover}-{Discover}-{}-{Tab}":['1{}-{}-{More function buttons}-{Tab}', '2{}-{}-{Search}-{Tab}', '3{Me}-{Me}-{}-{Tab}', '4{Discover}-{Discover}-{}-{Tab}', '5{Contacts}-{Contacts}-{}-{Tab}', '6{Chats}-{Chats}-{}-{Tab}', '7{Games}-{Games}-{}-{}', '8{Nearby}-{Nearby}-{}-{}', '9{Search}-{Search}-{}-{}', '10{Top Stories}-{Top Stories}-{}-{}', '11{Shake}-{Shake}-{}-{}', '12{Scan}-{Scan}-{}-{}', '13{Live Stream}-{Live Stream}-{}-{}', '14{Channels}-{Channels}-{Channels}-{}', '15{Moments}-{Moments}-{}-{}'],
     "5{Contacts}-{Contacts}-{}-{Tab}":['1{}-{}-{More function buttons}-{Tab}', '2{}-{}-{Search}-{Tab}', '3{Me}-{Me}-{}-{Tab}', '4{Discover}-{Discover}-{}-{Tab}', '5{Contacts}-{Contacts}-{}-{Tab}', '6{Chats}-{Chats}-{}-{Tab}','13{Official Accounts}-{Official Accounts}-{}-{}', '14{Tags}-{Tags}-{}-{}', '15{Group Chats}-{Group Chats}-{}-{}', '16{New Friends}-{New Friends}-{}-{Tab}'],
     "6{Bowen}-{Bowen,3/22/23,398178}-{}-{}":['1{}-{}-{Hide more function buttons}-{Icon}', '2{}-{}-{Stickers}-{Icon}', '3{}-{}-{}-{}', '4{}-{}-{Switch to "Hold to Talk}-{Icon}', '5{398178}-{398178}-{}-{Title}', '6{}-{}-{BowenProfile Photo}-{Icon}', '7{}-{}-{Chat Info}-{Icon}', '8{Bowen}-{Bowen}-{}-{}', '9{}-{}-{Back}-{}']
     }"""},
    {"role": "user",
        "content":"""The page:['1{Me}-{Me}-{}-{Tab}', '2{Discover}-{Discover}-{}-{Tab}', '3{Contacts}-{Contacts}-{}-{Tab}', '4{Chats}-{Chats}-{}-{Tab}', '5{Settings}-{Settings}-{}-{}', '6{Sticker Gallery}-{Sticker Gallery}-{}-{}', '7{My Posts}-{My Posts}-{}-{}', '8{Favorites}-{Favorites}-{}-{}', '9{Services}-{Services}-{}-{}', "10{}-{}-{Friends' Status}-{}", '11{Status}-{Status}-{Add Status}-{}', '12{}-{}-{My QR Code}-{Tab}', '13{Weixin ID: saltyp0}-{Weixin ID: saltyp0}-{}-{Title}']"""},
]
response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=intention,
    temperature=0.7,
)
print(response)
