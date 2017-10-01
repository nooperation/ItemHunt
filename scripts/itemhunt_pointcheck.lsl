string URL_GET_TOTAL_POINTS = "https://itemhunt.nooperation.net/server/get_total_points";

string CONFIG_PATH = "Config";
integer currentConfigLine = 0;
key configQueryId = NULL_KEY;
string privateToken = "";

string JSON_RESULT_SUCCESS = "success";
string JSON_RESULT_ERROR = "error";
string JSON_TAG_RESULT = "result";
string JSON_TAG_PAYLOAD = "payload";
string JSON_TAG_TARGET_UUID = "target_uuid";

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

default
{
    state_entry()
    {
        if(!ReadConfig())
        {
            Output("Failed to read config");
        }
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

                Output("Ready");
                return;
            }
            else
            {
              processConfigLine(data);
              configQueryId = llGetNotecardLine(CONFIG_PATH, ++currentConfigLine);
            }
        }
    }

    touch_end(integer num_detected)
    {
        integer i = 0;
        for(i = 0; i < num_detected; ++i)
        {
            string player_uuid = llDetectedKey(i);

            string post_data_str =
              "private_token=" + privateToken +
              "&player_uuid=" + (string)player_uuid;

            llHTTPRequest(
              URL_GET_TOTAL_POINTS,
              [HTTP_METHOD, "POST",HTTP_MIMETYPE,"application/x-www-form-urlencoded"],
              post_data_str
            );
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
            string total_points = llJsonGetValue(payload, ["total_points"]);
            OutputTo(target_uuid, "You have " + total_points + " points");
        }
        else
        {
            string error_code = llJsonGetValue(payload, ["code"]);
            OutputTo(target_uuid, "Server error: " + payload);
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
