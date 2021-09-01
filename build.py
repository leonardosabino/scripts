import argparse
import os.path
import pickle
import platform
import sys

BUILD_DIRECTORY = 'build_directory.py'

# Checa diretório e salva caso necessário
TEMPLATE_LIQUIDACAO_DIRECTORY = os.getcwd()
CONFIG_SERVER_DIRECTORY = os.getcwd().replace('service--template-liq', 'service--config-server-TESTE-LOCAL')
DATA_CONFIG_SERVER_DIRECTORY = os.getcwd().replace('service--template-liq', 'data--config-server')
if not os.path.isfile(BUILD_DIRECTORY):
    JAVA_8 = input('Insira o diretório da sua JDK8 (mantenha a default no 11): ')
    dict = {'JAVA_8': f'{JAVA_8}'}
    file = open(BUILD_DIRECTORY, 'wb')
    pickle.dump(dict, file)
    file.close()

file = open(BUILD_DIRECTORY, 'rb')
dict = pickle.load(file)
JAVA_8 = dict.get('JAVA_8')

# Status do processo de build
SQLSERVER_DB = 'WAITING'
LIQUIDACAO_TEMPLATE_ADQ = 'WAITING'
CONFIG_SERVER = 'WAITING'

SQLSERVER_DB_build = True
LIQUIDACAO_TEMPLATE_ADQ_build = True
CONFIG_SERVER_build = True

# Cores no terminal
RED = '\033[31m'
GREEN = '\033[32m'
YELLOW = '\033[33m'
BLUE = '\033[34m'
NC = '\033[0m'  # No Color

# Processo de --just ou --except do build
parser = argparse.ArgumentParser()
parser.add_argument('-j', '--just', help='Just Build', nargs='+', required=False)
parser.add_argument('-e', '--except', help='Except Build', nargs='+', required=False, dest='expt')
args = parser.parse_args()

if args.just is not None and args.expt is not None:
    print('Choose between --just or --except')
    sys.exit(1)

if args.just is not None:
    SQLSERVER_DB_build = False
    LIQUIDACAO_TEMPLATE_ADQ_build = False
    CONFIG_SERVER_build = False
    for opt in args.just:
        if 'service--template-liq' in opt:
            LIQUIDACAO_TEMPLATE_ADQ_build = True
        if 'sqlserver-db' in opt:
            SQLSERVER_DB_build = True
        if 'service--config-server' in opt:
            CONFIG_SERVER_build = True

if args.expt is not None:
    SQLSERVER_DB_build = True
    LIQUIDACAO_TEMPLATE_ADQ_build = True
    CONFIG_SERVER_build = True
    for opt in args.expt:
        if 'service--template-liq' in opt:
            LIQUIDACAO_TEMPLATE_ADQ_build = False
        if 'sqlserver-db' in opt:
            SQLSERVER_DB_build = False
        if 'service--config-server' in opt:
            CONFIG_SERVER_build = False

def set_color_text(word, color):
    if color is RED:
        return f'{RED}{word}{NC}'
    if color is BLUE:
        return f'{BLUE}{word}{NC}'
    elif color is YELLOW:
        return f'{YELLOW}{word}{NC}'
    elif color is GREEN:
        return f'{GREEN}{word}{NC}'

def set_log_status_color_text(word):
    if word == 'ERROR':
        return set_color_text(word, RED)
    elif word == 'WAITING':
        return set_color_text(word, YELLOW)
    elif word == 'PROCESSING':
        return set_color_text(word, BLUE)
    else:
        return set_color_text(word, GREEN)

def log_status():
    print('status process:')
    if SQLSERVER_DB_build:
        print(f'sqlserver-db: {set_log_status_color_text(SQLSERVER_DB)}')
    if LIQUIDACAO_TEMPLATE_ADQ_build:
        print(f'service--template-liq: {set_log_status_color_text(LIQUIDACAO_TEMPLATE_ADQ)}')
    if CONFIG_SERVER_build:
        print(f'service--config-server: {set_log_status_color_text(CONFIG_SERVER)}')

def set_gradlew_command():
    if platform.system() == 'Windows':
        return r'.\gradlew'
    else:
        return './gradlew'

def check_command_status(situation):
    if situation > 0:
        return 'ERROR'
    else:
        return 'PROCESSED'

sourceDir = os.path.abspath(os.path.join(os.getcwd(), os.pardir))

GRADLEW_COMMAND = set_gradlew_command()

# Comandos SQLSERVER
if SQLSERVER_DB_build:
    SQLSERVER_DB = 'PROCESSING'
    log_status()
    situation = os.system(f'docker pull mcr.microsoft.com/mssql/server:2017-latest')
    SQLSERVER_DB = check_command_status(situation)

# Comandos do liquidacao-template-adq
if LIQUIDACAO_TEMPLATE_ADQ_build:
    DOCKER_BUILD = f'{GRADLEW_COMMAND} docker'
    LIQUIDACAO_TEMPLATE_ADQ = 'PROCESSING'
    log_status()
    situation = os.system(f'{GRADLEW_COMMAND} build && {DOCKER_BUILD}')
    LIQUIDACAO_TEMPLATE_ADQ = check_command_status(situation)

# Comandos do config-server
if CONFIG_SERVER_build:
    os.environ['JAVA_HOME'] = JAVA_8
    CONFIG_SERVER_BUILD=f'cd {CONFIG_SERVER_DIRECTORY} && {GRADLEW_COMMAND} build'
    COPY_DATA_SOURCE=f'cd {DATA_CONFIG_SERVER_DIRECTORY}/../ && tar -czf {CONFIG_SERVER_DIRECTORY}/build/data--config-server.tar.gz data--config-server'
    CONFIG_SERVER_DOCKER_BUILD=f'cd {CONFIG_SERVER_DIRECTORY}/../ && docker build -f {TEMPLATE_LIQUIDACAO_DIRECTORY}/docker/config-server/Dockerfile --build-arg dataConfigServer=/service--config-server-TESTE-LOCAL/build/data--config-server.tar.gz --build-arg JAR_FILE=/service--config-server-TESTE-LOCAL/build/libs/*.jar -t pan/service--config-server .'
    CONFIG_SERVER = 'PROCESSING'
    log_status()
    situation = os.system(f'{CONFIG_SERVER_BUILD} && {COPY_DATA_SOURCE} && cd {CONFIG_SERVER_DIRECTORY}/../ && {CONFIG_SERVER_BUILD} && {CONFIG_SERVER_DOCKER_BUILD}')
    CONFIG_SERVER = check_command_status(situation)

log_status()
