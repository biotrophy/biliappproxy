import os, sys, inspect
import uuid
import yaml

def get_program_fullname():
    if getattr(sys, "frozen", False): # The application is frozen
        # starter is excutable file
        # return excutable file's directory
        return os.path.abspath(sys.executable)
    elif sys.argv[0]:  # starter is python script
        return os.path.abspath(sys.argv[0])
    else:
        return os.path.abspath(inspect.stack()[-1][1])

APP_FULLNAME = get_program_fullname()
BASE_PATH, APP_NAME_WEXT = os.path.split(APP_FULLNAME)
APP_NAME = os.path.splitext(APP_NAME_WEXT)[0]

DEFAULT_CONFIG = {'USERS':[{'access_key': None}], 'KEY': uuid.uuid4().hex}

class IndentDumper(yaml.Dumper):
    def increase_indent(self, flow=False, indentless=False):
        return super(IndentDumper, self).increase_indent(flow=False, indentless=False)

def load_yaml(filename):
    try:
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                users = config['USERS']
                if config['KEY'] and len(users) > 1 and users[0]['access_key']:
                    return {
                        "USERS": users,
                        "KEY": config["KEY"],
                        "HOST": config.get('HOST', '127.0.0.1'),
                        "PORT": int(config.get('PORT', 1211))
                    }
            return
        else:
            with open(filename, 'w', encoding='utf-8') as f:
                yaml.dump(DEFAULT_CONFIG, f, Dumper=IndentDumper, default_flow_style=False, sort_keys=False)
                return
    except Exception as e:
        pass

