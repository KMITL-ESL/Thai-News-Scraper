import os
import yaml
from collections import namedtuple




def load_config(profile):
    if profile == 'DEPLOY':
        config_path = 'config-deploy.yaml'
    else:
        config_path = 'config.yaml'
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.load(f)
    return config
def assign_flag(config):
    config['db']['password'] = os.environ.get('DB_PASSWORD', config['db']['password'])
profile = os.environ.get('PROFILE', None)
config = load_config(profile)
assign_flag(config)