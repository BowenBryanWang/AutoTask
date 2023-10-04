import openai
prompt = [
    {
        "role": "system",
        "content": """You are an expert in UI automation and robust error handling. Your task is to critically evaluate an action trace on UI produced by a [primitive LLM], which follows human instruction but is known for its inaccuracies. 
Basically, the working process of [primitive LLM] is:
    Follow the user's intent -> observe UI elements on UI screen -> select UI elements and rate them -> select the top one and execute it
Utilizing the log files from each module of current step of the [primitive LLM], you should determine whether this step caused error or not.
The only way you could do in correction is to control the rating scores by outputing different weights to them.
[primitive LLM] works in which they cannot see further information on UI, but as an error handling expert in the backtracking process you should utilize further information that you observed on subsequent UI to help correct possible errors.
In some situations there is no error and is relatively correct, it depends so you should think step by step.
Follow the steps below and think step by step:
a. Understand the information given and synthize;
b, determine whether this step caused error;
c, if so, think step by step about the scoring result, try to identify error-cause and give Punishment coefficient from 0-10;
d, if you identify no error in this step,we could move on to previous steps, so output "no error".
Finally, output a JSON format like this example:
{
    "result": "error" or "no error",
    "punishment":
    {
        "id_x": 1,
        "id_y": 2,
        ......(for UI elements selected with id , output your punishment coefficient from 0-10)
    }
}
"""
    },
    {
        "role": "user",
        "content": """
        {
    "@User_intent": "aaccess all mails in gmail",
    "@Page_components": [
        "<button id=1 class='' description='Meet'>  </button>\n",
        "<div id=2 class='com.google.android.gm:id/compose_button' description='Compose'> Compose </div>\n",
        "<div id=3 class='com.google.android.gm:id/open_search' description='Open navigation drawer,Signed in as Bowen Wang saltyp0rridge20@gmail.com\nAccount and settings.'> Search in mail\n    <p> Search in mail </p> </div>\n",
        "<button id=4 class='com.google.android.gm:id/selected_account_disc_gmail' description='Signed in as Bowen Wang saltyp0rridge20@gmail.com\nAccount and settings.'>  </button>\n",
        "<div id=5 class='' description='Open navigation drawer'>  </div>\n"
    ],
    "@Module": [
        {
            "Name": "Predict",
            "Description": "This module is a prediction model, predicting what will appear after clicking each components on current screen",
            "Output": {
                "<button id=1 class='' description='Meet'>  </button>\n": "Lead to a page where you can meet or video chat with contacts",
                "<div id=2 class='com.google.android.gm:id/compose_button' description='Compose'> Compose </div>\n": [
                    " <div  class='com.google.android.gm:id/composearea_tap_trap_bottom' >  </div><div  class='' > Compose email </div><div  class='com.google.android.gm:id/subject' > Subject </div><button  class='com.google.android.gm:id/add_cc_bcc' description='Add Cc/Bcc'>  </button><div  class='' >  </div><div  class='com.google.android.gm:id/peoplekit_autocomplete_to_prefix' > To </div><div  class='com.google.android.gm:id/from_label' description='From'> From </div><button  class='' description='More options'>  </button><div  class='com.google.android.gm:id/send' description='Send'>  </div><div  class='com.google.android.gm:id/add_attachment' description='Attach file'>  </div><div  class='' description='Navigate up'>  </div>"
                ],
                "<div id=3 class='com.google.android.gm:id/open_search' description='Open navigation drawer,Signed in as Bowen Wang saltyp0rridge20@gmail.com\nAccount and settings.'> Search in mail\n    <p> Search in mail </p> </div>\n": [
                    " <div  class='com.google.android.gm:id/hub_drawer_label_container' > Help & feedback </div><div  class='com.google.android.gm:id/hub_drawer_label_container' > Settings </div><div  class='com.google.android.gm:id/hub_drawer_label_container' > Contacts </div><div  class='com.google.android.gm:id/hub_drawer_label_container' > Calendar </div><div  class='com.google.android.gm:id/hub_drawer_label_container' > Notes </div><div  class='com.google.android.gm:id/hub_drawer_label_container' > Trash    <p> 3 </p> </div><div  class='com.google.android.gm:id/hub_drawer_label_container' > Spam    <p> 23 </p> </div><div  class='com.google.android.gm:id/hub_drawer_label_container' > All mail    <p> 53 </p> </div><div  class='com.google.android.gm:id/hub_drawer_label_container' > Drafts </div><div  class='com.google.android.gm:id/hub_drawer_label_container' > Outbox </div><div  class='com.google.android.gm:id/hub_drawer_label_container' > Scheduled </div><div  class='com.google.android.gm:id/hub_drawer_label_container' > Sent </div><div  class='com.google.android.gm:id/hub_drawer_label_container' > Important </div><div  class='com.google.android.gm:id/hub_drawer_label_container' > Snoozed </div><div  class='com.google.android.gm:id/hub_drawer_label_container' > Starred </div><button  class='' description='Meet'>  </button><div  class='com.google.android.gm:id/compose_button' description='Compose'> Compose </div><div  class='com.google.android.gm:id/open_search' description='Open navigation drawer;;Signed in as Bowen Wang saltyp0rridge20@gmail.comAccount and settings.'> Search in mail    <p> Search in mail </p>    <button  class='com.google.android.gm:id/selected_account_disc_gmail' description='Signed in as Bowen Wang saltyp0rridge20@gmail.comAccount and settings.'>  </button>    <div  class='' description='Open navigation drawer'>  </div> </div>"
                ],
                "<button id=4 class='com.google.android.gm:id/selected_account_disc_gmail' description='Signed in as Bowen Wang saltyp0rridge20@gmail.com\nAccount and settings.'>  </button>\n": "Display account and settings page for the user Bowen Wang",
                "<div id=5 class='' description='Open navigation drawer'>  </div>\n": "Open the navigation drawer which contains various options and settings"
            }
        },
        {
            "Name": "Select",
            "Description": "This module is a selection model, selecting the 5 possible component without relativity ranking to be acted on catering to user's intent",
            "Note": "This individual module only select 5 highly related components,without ranking them,and without analyzing the correctness of the components aligning with user's content ",
            "Output": {
                "<button id=1 class='' description='Meet'>  </button>\n": "This component is a natural starting point for interactions on the Gmail interface.",
                "<div id=2 class='com.google.android.gm:id/compose_button' description='Compose'> Compose </div>\n": "This component is a prominent part of the user interface and could potentially lead to the mail viewing area.",
                "<div id=3 class='com.google.android.gm:id/open_search' description='Open navigation drawer,Signed in as Bowen Wang saltyp0rridge20@gmail.com\nAccount and settings.'> Search in mail\n    <p> Search in mail </p> </div>\n": "This component contains an 'All mail' option that directly aligns with the user's intent.",
                "<button id=4 class='com.google.android.gm:id/selected_account_disc_gmail' description='Signed in as Bowen Wang saltyp0rridge20@gmail.com\nAccount and settings.'>  </button>\n": "This component represents the account and settings, which could potentially lead to relevant features.",
                "<div id=5 class='' description='Open navigation drawer'>  </div>\n": "This component opens the navigation drawer which likely contains options related to managing and viewing emails."
            }
        },
        {
            "Name": "Plan",
            "Description": "This module is a plan module, planning the next action based on the selected components, whether click or edit",
            "Output": {
                "candidate1": {
                    "action": "click",
                    "text": null,
                    "reason": "Switching to the 'Meet' feature is not relevant to accessing emails."
                },
                "candidate2": {
                    "action": "click",
                    "text": null,
                    "reason": "To compose a new email, not relevant to accessing all emails."
                },
                "candidate3": {
                    "action": "click",
                    "text": null,
                    "reason": "To open the navigation drawer and search for emails."
                },
                "candidate4": {
                    "action": "click",
                    "text": null,
                    "reason": "To open the account and settings, not relevant to accessing all emails."
                },
                "candidate5": {
                    "action": "click",
                    "text": null,
                    "reason": "To open the navigation drawer, not relevant to accessing all emails."
                }
            }
        },
        {
            "Name": "Evaluate",
            "Description": "This module is an evaluation module, evaluating the selected components of their contribution to fulfilling the user's intent",
            "Output": {
                "<button id=1 class='' description='Meet'>  </button>\n": 6,
                "<div id=2 class='com.google.android.gm:id/compose_button' description='Compose'> Compose </div>\n": 1,
                "<div id=3 class='com.google.android.gm:id/open_search' description='Open navigation drawer,Signed in as Bowen Wang saltyp0rridge20@gmail.com\nAccount and settings.'> Search in mail\n    <p> Search in mail </p> </div>\n": 2,
                "<button id=4 class='com.google.android.gm:id/selected_account_disc_gmail' description='Signed in as Bowen Wang saltyp0rridge20@gmail.com\nAccount and settings.'>  </button>\n": 1,
                "<div id=5 class='' description='Open navigation drawer'>  </div>\n": 5
            }
        },
        {
            "Name": "Decide",
            "Description": "This module is a decision module, deciding the final action based on the evaluation result, whether complete or wrong or go on",
            "Output": {
                "status": "wrong",
                "reason": "clicking on meet does not go to all mails in mailbox"
            }
        }
    ],
    "@Page_description": "Main interface of the Gmail application",
    "@Previous_Step": " -> Page:Main interface of the Gmail application",
    "@Action": "Action: Click on <div id=1 class='' description='Meet'>  </div>\n",
    "@Similar_task": [
        "Clear chat history on WeChat group 2:['Long press the chat you want to clear', 'Delete Chat', 'Delete']",
        "View my notifications or messages on Zhihu:['Tap the profile icon on the bottom right', 'Tap the bell icon or the message icon on the top left', 'Select a notification or message from the list']",
        "log out of my WeChat account:['Me', 'Settings', 'Log Out', 'Confirm']",
        "Change the language on my WeChat app into English:['Me', 'Settings', 'General', 'Language', 'English']"
    ],
    "@Successive_Page": "<div id=1 class='com.google.android.gm:id' > Start meeting </div>\n<div id=2 class='com.google.android.gm:id/hub_drawer_label_container' > End Meeting\n    <p> 3 </p> </div>"
}
        """
    },
]
response = openai.ChatCompletion.create(
    model="gpt-4",
    messages=prompt,
    temperature=1,
)
print(response)