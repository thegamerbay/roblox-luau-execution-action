import os
import sys
import urllib.request
import urllib.error
import json
import time

def set_github_output(key, value):
    output_file = os.environ.get('GITHUB_OUTPUT')
    if output_file:
        with open(output_file, 'a', encoding='utf-8') as f:
            # Use EOF for multiline output
            f.write(f"{key}<<EOF\n{value}\nEOF\n")

def print_error(msg):
    print(f"::error::{msg}", file=sys.stderr)

def make_request(url, headers, data=None, method=None):
    if data and not isinstance(data, bytes):
        data = data.encode('utf-8')
    
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        print_error(f"HTTP {e.code}: {e.reason}\n{error_body}")
        sys.exit(1)
    except Exception as e:
        print_error(f"Request failed: {str(e)}")
        sys.exit(1)

def upload_place(api_key, universe_id, place_id, place_file, publish):
    print(f"::group::Uploading Place ({place_file})")
    version_type = "Published" if publish.lower() == 'true' else "Saved"
    url = f"https://apis.roblox.com/universes/v1/{universe_id}/places/{place_id}/versions?versionType={version_type}"
    
    headers = {
        "x-api-key": api_key,
        "Content-Type": "application/xml",
        "Accept": "application/json"
    }

    try:
        with open(place_file, "rb") as f:
            file_data = f.read()
    except Exception as e:
        print_error(f"Failed to read place file {place_file}: {e}")
        sys.exit(1)

    print(f"Uploading to Universe {universe_id}, Place {place_id} as {version_type}...")
    response_data = make_request(url, headers, data=file_data, method="POST")
    place_version = response_data.get("versionNumber")
    print(f"Upload successful. New Place Version: {place_version}")
    print("::endgroup::")
    return place_version

def create_task(api_key, universe_id, place_id, place_version, script_file):
    print("::group::Creating Luau Execution Task")
    url = f"https://apis.roblox.com/cloud/v2/universes/{universe_id}/places/{place_id}/versions/{place_version}/luau-execution-session-tasks"
    
    headers = {
        "x-api-key": api_key,
        "Content-Type": "application/json"
    }

    try:
        with open(script_file, "r", encoding="utf-8") as f:
            script_content = f.read()
    except Exception as e:
        print_error(f"Failed to read script file {script_file}: {e}")
        sys.exit(1)

    payload = json.dumps({"script": script_content})
    print(f"Submitting script ({script_file}) for execution...")
    task_data = make_request(url, headers, data=payload, method="POST")
    print(f"Task created successfully. Task Path: {task_data.get('path')}")
    print("::endgroup::")
    return task_data.get('path')

def poll_task_and_get_logs(api_key, task_path):
    print("::group::Polling Task Execution")
    url_poll = f"https://apis.roblox.com/cloud/v2/{task_path}"
    url_logs = f"https://apis.roblox.com/cloud/v2/{task_path}/logs"
    
    headers = {"x-api-key": api_key}
    
    while True:
        task_data = make_request(url_poll, headers, method="GET")
        state = task_data.get("state")
        print(f"Current State: {state}")
        
        if state != "PROCESSING":
            break
        time.sleep(3)
        
    print("::endgroup::")

    # Fetch Logs
    print("::group::Luau Execution Logs")
    logs_data = make_request(url_logs, headers, method="GET")
    
    logs_text = ""
    try:
        messages = logs_data['luauExecutionSessionTaskLogs'][0]['messages']
        logs_text = '\n'.join(messages)
        print(logs_text)
    except (KeyError, IndexError):
        print("No logs produced or failed to parse logs.")
    print("::endgroup::")

    return state, logs_text

def main():
    api_key = os.environ.get("INPUT_API_KEY")
    universe_id = os.environ.get("INPUT_UNIVERSE_ID")
    place_id = os.environ.get("INPUT_PLACE_ID")
    place_file = os.environ.get("INPUT_PLACE_FILE")
    script_file = os.environ.get("INPUT_SCRIPT_FILE")
    publish = os.environ.get("INPUT_PUBLISH", "false")

    if not all([api_key, universe_id, place_id, place_file, script_file]):
        print_error("Missing required inputs.")
        sys.exit(1)

    place_version = upload_place(api_key, universe_id, place_id, place_file, publish)
    task_path = create_task(api_key, universe_id, place_id, place_version, script_file)
    state, logs = poll_task_and_get_logs(api_key, task_path)

    set_github_output("task_status", state)
    set_github_output("task_logs", logs)

    if state != "COMPLETE":
        print_error(f"Luau task failed with state: {state}")
        sys.exit(1)
    
    print("✅ Luau task completed successfully!")

if __name__ == "__main__":
    main()
