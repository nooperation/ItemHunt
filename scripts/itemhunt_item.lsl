// Server data
string URL_REGISTER = "https://itemhunt.nooperation.net/server/register_item";
string URL_ACTIVATE = "https://itemhunt.nooperation.net/server/activate_item";
integer TYPE_CREDIT = 0;
integer TYPE_PRIZE = 1;

integer itemType = TYPE_CREDIT;
integer points = 0;
list prize_list = [];
integer prize_list_length = 0;

string CONFIG_PATH = "Config";
integer currentConfigLine = 0;
key configQueryId = NULL_KEY;
string privateToken = "";
key httpRequestId = NULL_KEY;
integer listen_channel = -12345; // Placeholder

string JSON_RESULT_SUCCESS = "success";
string JSON_RESULT_ERROR = "error";
string JSON_TAG_RESULT = "result";
string JSON_TAG_PAYLOAD = "payload";
string JSON_TAG_TARGET_UUID = "target_uuid";

string description = "";
string name = "";
vector position = <0, 0, 0>;

// Previous String Examples:
//   Sorry, you took too long to respond to the confirmation dialog!  Click on the prize box again if you would like to spend your points on this prize.
//   You have enough points for that :)
//   You have 280 points.
//   5 points recorded

Output(string message)
{
    llOwnerSay(message);
}

OutputTo(key target_uuid, string message)
{
    if(target_uuid != NULL_KEY)
    {
        llInstantMessage(target_uuid, message);
    }
    else
    {
        Output(message);
    }
}

/// <summary>
/// Processes a single line from the settings file
/// Each line must be in the format of: setting name = value
/// </summary>
/// <param name="line">Raw line from settnigs file</param>
processTriggerLine(string line)
{
    integer seperatorIndex = llSubStringIndex(line, "=");
    string name;
    string value;

    if(seperatorIndex <= 0)
    {
        Output("Missing separator: " + line);
        return;
    }

    name = llToLower(llStringTrim(llGetSubString(line, 0, seperatorIndex - 1), STRING_TRIM_TAIL));
    value = llStringTrim(llGetSubString(line, seperatorIndex + 1, -1), STRING_TRIM);

    if(name == "privatetoken")
    {
        privateToken = value;
    }
}

/// <summary>
/// Handles processing of a single line of our actions file.
/// </summary>
/// <param name="line">Line from actions notecard</param>
processConfigLine(string line)
{
    line = llStringTrim(line, STRING_TRIM_HEAD);

    if(line == "" || llGetSubString(line, 0, 0) == "#")
    {
        return;
    }

    processTriggerLine(line);
}

integer ReadConfig()
{
    privateToken = "";

    if(llGetInventoryType(CONFIG_PATH) != INVENTORY_NONE)
    {
        if(llGetInventoryKey(CONFIG_PATH) != NULL_KEY)
        {
            currentConfigLine = 0;
            configQueryId = llGetNotecardLine(CONFIG_PATH, currentConfigLine);
            return TRUE;
        }
        else
        {
            Output("Config file has no key (Never saved? Not full-perm?)");
        }
    }

    return FALSE;
}

CheckDescription()
{
    if(llGetObjectDesc() != description || llGetObjectName() != name || llGetPos() != position)
    {
        llResetScript();
    }
}

integer GetChannel()
{
    integer channel = (integer)("0x" + (string)llGetKey());
    while(channel <= 255 && channel >= -255)
    {
        channel = (integer)llFrand(65536) | ((integer)llFrand(65536) << 16);
    }

    return channel;
}

ActivateItem(key player_uuid)
{
    list details = llGetObjectDetails(player_uuid, [
      OBJECT_NAME,
      OBJECT_POS
    ]);

    string player_name = llList2String(details, 0);
    vector player_pos = llList2Vector(details, 1);

    string post_data_str =
      "private_token=" + privateToken +
      "&player_name=" + player_name +
      "&player_uuid=" + (string)player_uuid +
      "&player_x=" + (string)player_pos.x +
      "&player_y=" + (string)player_pos.y +
      "&player_z=" + (string)player_pos.z +
      "&points=" + (string)points;

    httpRequestId = llHTTPRequest(
      URL_ACTIVATE,
      [HTTP_METHOD, "POST",HTTP_MIMETYPE,"application/x-www-form-urlencoded"],
      post_data_str
    );
}

default
{
    state_entry()
    {
        description = llGetObjectDesc();
        name = llGetObjectName();
        position = llGetPos();
        llSetTimerEvent(5);

        points = (integer)description;
        if((string)points != description)
        {
          Output("ERROR: Description must contain the point value");
          return;
        }

        if(points < 0)
        {
          Output("ERROR: Negative point value detected");
          return;
        }

        integer totalItems = llGetInventoryNumber(INVENTORY_OBJECT);
        if(totalItems > 0)
        {
          prize_list = [];
          integer itemIndex = 0;
          for(itemIndex = 0; itemIndex < totalItems; ++itemIndex)
          {
              string itemName = llGetInventoryName(INVENTORY_OBJECT, itemIndex);
              if(itemName == llGetScriptName() || llToLower(itemName) == "config")
              {
                Output("ERROR: Attempted to include sensitive items as a prize");
                return;
              }

              if(llGetInventoryPermMask(itemName, MASK_BASE) & PERM_COPY)
              {
                prize_list += itemName;
              }
          }

          prize_list_length = llGetListLength(prize_list);
          if(prize_list_length != totalItems)
          {
              Output("ERROR: Inventory contains some non-copyable items. These cannot be given away as a prize.");
              return;
          }
          else
          {
              itemType = TYPE_PRIZE;
          }
        }

        if(itemType == TYPE_CREDIT && points == 0)
        {
          Output("ERROR: Only store items can have a zero point value");
          return;
        }

        if(!ReadConfig())
        {
            Output("Failed to read config");
        }
    }

    timer()
    {
        CheckDescription();
    }

    dataserver(key queryId, string data)
    {
        if(queryId == configQueryId)
        {
            if(data == EOF)
            {
                if(privateToken == "")
                {
                    Output("ERROR: Missing auth token");
                    return;
                }

                string post_data_str =
                  "private_token=" + privateToken +
                  "&points=" + (string)points +
                  "&type=" + (string)itemType;

                httpRequestId = llHTTPRequest(
                  URL_REGISTER,
                  [HTTP_METHOD, "POST",HTTP_MIMETYPE,"application/x-www-form-urlencoded"],
                  post_data_str
                );

                return;
            }
            else
            {
              processConfigLine(data);
              configQueryId = llGetNotecardLine(CONFIG_PATH, ++currentConfigLine);
            }
        }
    }

    http_response(key request_id, integer status, list metadata, string body)
    {
        if(request_id != httpRequestId)
        {
            return;
        }

        string result = llJsonGetValue(body, [JSON_TAG_RESULT]);
        string payload = llJsonGetValue(body, [JSON_TAG_PAYLOAD]);

        if(result == JSON_RESULT_SUCCESS)
        {
            if(itemType == TYPE_CREDIT)
            {
              Output("Updated hunt item worth " + (string)points + " points");
              llSetText("", ZERO_VECTOR, 1.0);
            }
            else
            {
              Output("Updated prize costing " + (string)points + " points");
              llSetText((string)points + " points", <1, 1, 1>, 1.0);
            }
            state Initialized;
        }
    }

    on_rez(integer start_param)
    {
        llResetScript();
    }

    changed(integer change)
    {
        if(change & (CHANGED_OWNER | CHANGED_REGION | CHANGED_REGION_START | CHANGED_INVENTORY))
        {
            llResetScript();
        }
    }
}

state Initialized
{
    state_entry()
    {
        if(itemType == TYPE_PRIZE)
        {
          listen_channel = GetChannel();
          llListen(listen_channel, "", NULL_KEY, "Yes");
        }

        llSetTimerEvent(5);
    }

    listen(integer channel, string name, key id, string msg)
    {
      if(channel != listen_channel)
      {
        return;
      }

      if(llToLower(msg) == "yes")
      {
          ActivateItem(id);
      }
    }

    timer()
    {
        CheckDescription();
    }

    on_rez(integer start_param)
    {
        llResetScript();
    }

    touch_end(integer num_detected)
    {
        integer i = 0;
        for(i = 0; i < num_detected; ++i)
        {
            if(itemType == TYPE_CREDIT)
            {
                ActivateItem(llDetectedKey(i));
            }
            else if(itemType == TYPE_PRIZE)
            {
                llDialog(llDetectedKey(i), "Buy '" + llGetObjectName() + "' for " + (string)points + " points?", ["Yes", "No"], listen_channel);
            }
        }
    }

    changed(integer change)
    {
        if(change & (CHANGED_OWNER | CHANGED_REGION | CHANGED_REGION_START | CHANGED_INVENTORY))
        {
            llResetScript();
        }
    }

    http_response(key request_id, integer status, list metadata, string body)
    {
        string result = llJsonGetValue(body, [JSON_TAG_RESULT]);
        if(result == JSON_NULL)
        {
            Output("Unknown HTTP response: " + body);
            return;
        }

        string payload = llJsonGetValue(body, [JSON_TAG_PAYLOAD]);
        string target_uuid_string = llJsonGetValue(body, [JSON_TAG_TARGET_UUID]);
        key target_uuid = NULL_KEY;

        if(target_uuid_string != JSON_NULL)
        {
          target_uuid = (key)target_uuid_string;
        }

        if(result == JSON_RESULT_SUCCESS)
        {
            string points_redeemed = llJsonGetValue(payload, ["points"]);
            string total_points = llJsonGetValue(payload, ["total_points"]);

            if(itemType == TYPE_PRIZE)
            {
              OutputTo(target_uuid, "You have successfully purchased this prize! You have " + total_points + " points remaining");

              if(prize_list_length > 1)
              {
                string objectName = llGetObjectName();
                if(llStringLength(objectName) == 0)
                {
                  llGiveInventoryList(target_uuid, "Item hunt prize " + llGetDate(), prize_list);
                }
                else
                {
                  llGiveInventoryList(target_uuid, llGetObjectName(), prize_list);
                }
              }
              else
              {
                llGiveInventory(target_uuid, llList2String(prize_list, 0));
              }
            }
            else
            {
              OutputTo(target_uuid, points_redeemed + " points recorded. You have a total of " + total_points + " points");
            }
        }
        else
        {
            string error_code = llJsonGetValue(payload, ["code"]);
            if(error_code == "already_used")
            {
                OutputTo(target_uuid, "You already got points for that!  Keep searching!");
            }
            else if(error_code == "not_enough_points")
            {
                OutputTo(target_uuid, "You don't have enough points for this item");
            }
            else
            {
                OutputTo(target_uuid, "Server error: " + payload);
            }
        }
    }
}
