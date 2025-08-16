import json
import getpass
import os.path
def load_key(keyname: str) -> object:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_name = os.path.join(script_dir, "Keys.json")
    # file_name = "Keys.json"
    if os.path.exists(file_name):
        with open(file_name, "r") as file:
            Key = json.load(file)
        if keyname in Key and Key[keyname]:
            return Key[keyname]
        else:
            keyval = getpass.getpass("配置文件中没有相应键，请输入对应配置信息:").strip()
            Key[keyname] = keyval
            with open(file_name, "w") as file:
                json.dump(Key, file, indent=4)
            return keyval
    else:
        keyval = getpass.getpass("配置文件中没有相应键，请输入对应配置信息:").strip()
        Key = {
            keyname:keyval
        }
        with open(file_name, "w") as file:
            json.dump(Key, file, indent=4)
        return keyval
if __name__ == "__main__":
    print(load_key("LANGSMITH_API_KEY"))