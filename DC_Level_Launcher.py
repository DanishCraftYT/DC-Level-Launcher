import subprocess
import datetime
import shutil
import sys
import os

# TODO: test updated settings editor.
# TODO: implement make command.
# TODO: implement open command.
# TODO: implement modifying player models.
# TODO: implement no steam support.
# TODO: implement 32 bit support.
# TODO: add config var to determine if the backup directory should be deleted or not after unmounting mod files.

# global varibles.
launcher_version: str = "0.0.1"
launcher_dirs: dict = {"Mods": "Mods", "Campaigns": "Campaigns"}
settings_file: [str] = []
settings_file_exists = True
settings_filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "DC_Settings.ini")
log_filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Launcher.log")

# logging.
SESSION_LOG_LEVEL = "SESSION"
INFO_LOG_LEVEL = "INFO"
NOTE_LOG_LEVEL = "NOTE"
WARN_LOG_LEVEL = "WARNING"
ERR_LOG_LEVEL = "ERROR"
CRITICAL_LOG_LEVEL = "CRITICAL"

# handles platform specific paths.
if sys.platform == "win32":
    olexe_filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "OutlastLauncher.exe")
    oldir_filepath = os.path.dirname(olexe_filepath)
elif sys.platform == "linux":
    olexe_filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Binaries", "Linux", "OLGame.x86_64")
    oldir_filepath = os.path.dirname(os.path.dirname(os.path.dirname(olexe_filepath)))
else:
    print(f"CRITICAL: Platform: {sys.platform} is not supported.")
    print("exiting...")
    sys.exit()

# TERMINAL TEXT COLORS #

# ARGS (term_text_* functions):
# str string - the message to print with a certain color.

def term_text_green(string: str) -> None: # SESSION_LOG_LEVEL.
    print("\033[92m{}\033[00m".format(string))

def term_text_red(string: str) -> None: # ERR_LOG_LEVEL.
    print("\033[91m{}\033[00m".format(string))

def term_text_yellow(string: str) -> None: # WARN_LOG_LEVEL.
    print("\033[93m{}\033[00m".format(string))

def term_text_cyan(string: str) -> None: # INFO_LOG_LEVEL.
    print("\033[96m{}\033[00m".format(string))

def term_text_blue(string: str) -> None: # NOTE_LOG_LEVEL.
    print("\033[94m{}\033[00m".format(string))

def term_text_magenta(string: str) -> None: # CRITICAL_LOG_LEVEL.
    print("\033[95m{}\033[00m".format(string))

# CONFIG #

# ARGS:
# [string] file_content - contains the content of the config file.
# string section_name - the name of the section containing the varible.
# string varible_name - the name of the varible to read it's value.
def config_read(file_content: [str], section_name: str, varible_name: str) -> str:
    section_found: bool = False
    varible: [str, str] = []
    for line in file_content: # loops through the file contents.
        if line == "" or line == "\n" or line[0] == ";": # handles empty and comment lines.
            continue
        elif line[0] == "[": # checks if a open curly bracket is in the line which indicates a section in the config file.
            if line.rstrip("\n") == f"[{section_name}]" and section_found == False: # checks if it has found the correct section.
                section_found = True
            elif section_found == True: # throws error if the correct section was found but the varible wasn't in it.
                raise Exception(f"ERROR: config varible: {varible_name} not found in section {section_name}")
            continue
        elif section_found == False and section_name != "": # skips over finding the varible if the section hasn't been found unless no section name has been specified.
            continue
        varible = line.split("=")
        varible[0] = varible[0].strip(" ")
        if varible[0] != varible_name: # checks if it has found the correct varible.
            continue
        return varible[1].rstrip("\n").strip(" ")
    # raises a error if the config varible or section wasn't found in the config file.
    if section_found == True:
        raise Exception(f"ERROR: config varible: {varible_name} not found in section {section_name}")
    else:
        raise Exception(f"ERROR: section: {section_name} not found in config file.")

# ARGS:
# [string] file_content - contains the content of the config file.
# string section_name - the name of the section containing the varible.
# string varible_name - the name of the varible to overwrite it's value.
# string new_value - the new value of the varible.
def config_write(file_content: [str], section_name: str, varible_name: str, new_value: str) -> [str]:
    section_found: bool = False
    file_varible_name: str = ""
    for i, line in enumerate(file_content): # loops through the file contents.
        if line == "" or line == "\n" or line[0] == ";": # handles empty and comment lines.
            continue
        elif line[0] == "[": # checks if a open curly bracket is in the line which indicates a section in the config file.
            if line.rstrip("\n") == f"[{section_name}]" and section_found == False: # checks if it has found the correct section.
                section_found = True
            elif section_found == True: # throws error if the correct section was found but the varible wasn't in it.
                raise Exception(f"ERROR: config varible: {varible_name} not found in section {section_name}")
            continue
        elif section_found == False and section_name != "": # skips over finding the varible if the section hasn't been found unless no section name has been specified.
            continue
        file_varible_name = line.split("=")[0].strip(" ")
        if file_varible_name != varible_name: # checks if it has found the correct varible.
            continue
        file_content[i] = f"{file_varible_name}={new_value}\n"
        return file_content
    # raises a error if the config varible or section wasn't found in the config file.
    if section_found == True:
        raise Exception(f"ERROR: config varible: {varible_name} not found in section {section_name}")
    else:
        raise Exception(f"ERROR: section: {section_name} not found in config file.")

# ARGS:
# [string] file_content - contains the content of the config file.
# [string] exclude_sections - contains the section names for the sections you don't want to get varibles from.
# bool read_var_comments - determines if the commented line above some varibles will be read.
def config_read_vars(file_content: [str], exclude_sections: [str], read_var_comments: bool = False) -> dict:
    varibles: dict = {}
    current_comment = ""
    current_section = ""
    skip_section = False
    for line in file_content: # loops through the file contents.
        if line == "" or line == "\n": # handles empty lines.
            continue
        elif line[0] == ";": # handles comment lines.
            if read_var_comments == True:
                current_comment = line.replace(";", "").strip(" ")
            continue
        elif line[0] == "[": # checks if a open curly bracket is in the line which indicates a section in the config file.
            skip_section = False
            current_section = line.rstrip("\n").rstrip("]").replace("[", "")
            if current_section in exclude_sections: # skips the section if it's part of the excluded sections list.
                skip_section = True
            continue
        elif skip_section == True: # if true. it skips the varibles in the section.
            continue
        varible: [str, str] = line.split("=")
        varible[0] = varible[0].strip(" ")
        varible[1] = varible[1].rstrip("\n").strip(" ")
        varibles[varible[0]] = [current_section, varible[1], current_comment]
        current_comment = "" # resets the current comment.
    return varibles

# ARGS:
# [string] file_content - contains the content of the config file.
# dict new_vars - the varibles to overwrite in the config file.
def config_write_vars(file_content: [str], new_vars: dict) -> [str]:
    for new_var in new_vars: # loops through all the modified varibles.
        for i, line in enumerate(file_content): # loops through the file contents.
            if new_var in line: # checks if the line contains a modified varible.
                file_content[i] = f"{new_var}={new_vars[new_var][1]}\n"
                break
    return file_content

# ARGS:
# string config_filepath - the path to the settings file to generate.
# string launcher_version - the version of the Level Launcher.
# string olexe_path - the path to the Outlast Executable file.
def config_generate(config_filepath: str, launcher_version: str, olexe_path: str) -> [str]:
    with open(config_filepath, "w") as f:
        f.writelines(f"""
[INFO]
; DO NOT EDIT: contains Launcher version.
LauncherVersion={launcher_version}

[LAUNCHER]
; contains the path to the Outlast executable.
OutlastEXEPath={olexe_path}
; determines if the original Level Launcher directories will be used instead of the new ones. can also be equal to None which determines if it should be true or false when the Level Launcher is initialized.
CompatibilityMode=True
; determines if it should print all logs or only important logs to the console.
PrintLogs=True
""")
    log(log_filepath, "generated settings file.", NOTE_LOG_LEVEL, True, term_text_blue)
    input("hit enter to continue...")
    with open(config_filepath, "r") as f:
        return f.readlines()

# LOGGING #

# ARGS:
# string log_filepath - the path to the log file.
# string msg - the message to write to the log file.
# string log_level - the severity of the log message (INFO, WARNING, ERROR, etc).
# bool print_to_console - determines if the log will be printed to the console or not.
# callable print_color - the function to call to print the msg with a different color.
def log(log_filepath: str, msg: str, log_level: str, print_to_console: bool = False, print_color: callable = None) -> None:
    with open(log_filepath, "a") as f:
        f.writelines(f"[{log_level}]: {msg}\n")
        
    if print_to_console == True:
        if print_color == None:
            print(f"[{log_level}]: {msg}")
        else:
            print_color(f"[{log_level}]: {msg}")

# LAUNCHER #

def init() -> None:
    global settings_file, settings_file_exists, launcher_version, settings_filepath, olexe_filepath, launcher_dirs, oldir_filepath, log_filepath

    # LOG FILE #
    if os.path.exists(log_filepath): # only attempts to read the log file if it exists.
        with open(log_filepath, "r") as f: # get's the length of the log file.
            log_file_length = len(f.readlines())
        if log_file_length != 0: # doesn't add a new line to the log file if it's empty.
            with open(log_filepath, "a") as f: # writes new line to the log file to seperate each session.
                f.write("\n")
    else:
        with open(log_filepath, "w") as f: # creates the log file if it doesn't exist.
            pass
    
    # cannot be printed because settings file has not been initialized yet.
    log(log_filepath, f"NEW - {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}", SESSION_LOG_LEVEL)
    log(log_filepath, "initializing the Level Launcher.", INFO_LOG_LEVEL)

    # SETTINGS FILE / OL PATHS #
    if not os.path.exists(settings_filepath): # throws warning if the settings file doesn't exist.
        settings_file_exists = False
        log(log_filepath, "no DC Level Launcher settings file found.", WARN_LOG_LEVEL, True, term_text_yellow)

        if not os.path.exists(olexe_filepath): # checks if OL EXE path is valid.
            log("Outlast Executable not found.", ERR_LOG_LEVEL, True, term_text_red)
            init_olpath()
    else:
        with open(settings_filepath, "r") as f:
            settings_file = f.readlines()
        if config_read(settings_file, "INFO", "LauncherVersion") != launcher_version:
            log(log_filepath, "Launcher Version mismatch between script and settings file: \"DC_Settings.ini\"", WARN_LOG_LEVEL, True, term_text_yellow)
        else:
            log(log_filepath, "Launcher Version matches \"LauncherVersion\" setting in settings file.", INFO_LOG_LEVEL, config_read(settings_file, "LAUNCHER", "PrintLogs").lower() == "true", term_text_cyan)

        if not os.path.exists(olexe_filepath): # checks if OL EXE path is valid.
            print("NOTE: checking settings file for Outlast Executable path.")
            if not os.path.exists(config_read(settings_file, "LAUNCHER", "OutlastEXEPath")): # checks if config OL EXE path is valid.
                log(log_filepath, "Outlast Executable not found.", ERR_LOG_LEVEL, True, term_text_red)
                init_olpath()
            else:
                olexe_filepath = config_read(settings_file, "LAUNCHER", "OutlastEXEPath")

                # platform specific code.
                if sys.platform == "win32":
                    oldir_filepath = os.path.dirname(olexe_filepath)
                elif sys.platform == "linux":
                    oldir_filepath = os.path.dirname(os.path.dirname(os.path.dirname(olexe_filepath)))

    if not os.path.exists(os.path.join(oldir_filepath, "OLGame")): # checks if the OL EXE path is correct.
        log(log_filepath, f"OLGame directory not found: \"{oldir_filepath}\"", ERR_LOG_LEVEL, True, term_text_red)
        init_olpath()
    log(log_filepath, "Outlast Executable found.", INFO_LOG_LEVEL, config_read(settings_file, "LAUNCHER", "PrintLogs").lower() == "true", term_text_cyan)
    config_write(settings_file, "LAUNCHER", "OutlastEXEPath", olexe_filepath)
    with open(settings_filepath, "w") as f:
        f.writelines(settings_file)
    log(log_filepath, "saved Outlast Executable path to the \"DC_Settings.ini\" file.", NOTE_LOG_LEVEL, True, term_text_blue)
    
    log(log_filepath, f"Print Logs is set to {config_read(settings_file, "LAUNCHER", "PrintLogs")}", INFO_LOG_LEVEL, config_read(settings_file, "LAUNCHER", "PrintLogs").lower() == "true", term_text_cyan)

    # COMPATIBILITY MODE #
    if config_read(settings_file, "LAUNCHER", "CompatibilityMode").lower() == "none": # determines if compatibility mode should be enabled or not.
        if os.path.exists(os.path.join(oldir_filepath, "custom")) or os.path.exists(os.path.join(oldir_filepath, "OLGame", "CookedPCConsole", "Custom", "Campaign")) or os.path.exists(os.path.join(oldir_filepath, "OLGame", "COokedLinux", "Custom", "Campaign")):
            config_write(settings_file, "LAUNCHER", "CompatibilityMode", "True")
        else:
            config_write(settings_file, "LAUNCHER", "CompatibilityMode", "False")
        with open(settings_filepath, "w") as f:
            f.writelines(settings_file)
        log(log_filepath, f"Compatibility Mode has been set to {config_read(settings_file, "LAUNCHER", "CompatibilityMode")}.", NOTE_LOG_LEVEL, True, term_text_blue)

    if config_read(settings_file, "LAUNCHER", "CompatibilityMode").lower() == "true": # handles compatibility mode.
        log(log_filepath, "Compatibility Mode is enabled.", INFO_LOG_LEVEL, True, term_text_cyan)
        launcher_dirs["Mods"] = "custom"
        if sys.platform == "win32":
            launcher_dirs["Campaigns"] = os.path.join("OLGame", "CookedPCConsole", "Custom", "Campaign")
        elif sys.platform == "linux":
            launcher_dirs["Campaigns"] = os.path.join("OLGame", "CookedLinux", "Custom", "Campaign")
    else:
        log(log_filepath, "Compatibility Mode is disabled.", INFO_LOG_LEVEL, config_read(settings_file, "LAUNCHER", "PrintLogs").lower() == "true", term_text_cyan)

    # LAUNCHER DIRECTORIES #
    # makes sure the launcher directories exists.
    if not os.path.exists(os.path.join(oldir_filepath, launcher_dirs["Mods"])):
        os.mkdir(os.path.join(oldir_filepath, launcher_dirs["Mods"]))
        log(log_filepath, f"created {launcher_dirs["Mods"]} folder.", NOTE_LOG_LEVEL, True, term_text_blue)
    if not os.path.exists(os.path.join(oldir_filepath, launcher_dirs["Campaigns"])):
        os.makedirs(os.path.join(oldir_filepath, launcher_dirs["Campaigns"]), exist_ok=True)
        log(log_filepath, f"created {launcher_dirs["Campaigns"]} folder.", NOTE_LOG_LEVEL, True, term_text_blue)
    log(log_filepath, "all Launcher folders found.", INFO_LOG_LEVEL, config_read(settings_file, "LAUNCHER", "PrintLogs").lower() == "true", term_text_cyan)
    log(log_filepath, "Level Launcher initialization successful.", INFO_LOG_LEVEL, config_read(settings_file, "LAUNCHER", "PrintLogs").lower() == "true", term_text_cyan)
    get_command()

def init_olpath() -> None:
    global olexe_filepath, oldir_filepath
    olexe_filepath = input("please specify the path to the Outlast Executable here: ")
    if not os.path.exists(olexe_filepath): # asks the user for a valid path until a valid path is given.
        log(log_filepath, f"Outlast Executable not found: \"{olexe_filepath}\"", ERR_LOG_LEVEL, True, term_text_red)
        init_olpath()
    
    # platform specific code.
    if sys.platform == "win32":
        oldir_filepath = os.path.dirname(olexe_filepath)
    elif sys.platform == "linux":
        oldir_filepath = os.path.dirname(os.path.dirname(os.path.dirname(olexe_filepath)))

    if not os.path.exists(os.path.join(oldir_filepath, "OLGame")): # asks the user for a valid path until a valid path is given.
        log(log_filepath, f"OLGame directory not found: \"{oldir_filepath}\"", ERR_LOG_LEVEL, True, term_text_red)
        init_olpath()

# MAIN #

def get_command() -> None:
    global settings_filepath, launcher_version, olexe_filepath, settings_file_exists, settings_file
    #print("Commands:\nplay <mod_name> [p]\nopen <campaign_name> [o]\nmake [m]\nlist [l]", end="")
    print("Commands:\nplay <mod_name> [p]\nopen <campaign_name> [o]\nlist [l]", end="")
    if settings_file_exists:
        print("settings [s]\n", end="")
    if config_read(settings_file, "LAUNCHER", "PrintLogs") == "True":
        print("displaylog [d]\n", end="")
    print("about [a]\nhelp [h]\nexit [e]")
    command_n_args = input("please type command here: ")
    command, args = ["", ""]

    # get's command and args from input.
    if len(command_n_args.split(" ")) == 1:
        command = command_n_args.split(" ")[0]
    else:
        command, args = command_n_args.split(" ")

    # checks which command was typed and calls the function for the command.
    if command.replace(" ", "") == "play" in command_n_args or command.replace(" ", "") == "p":
        command_play(args)
    elif command.replace(" ", "") == "open" or command.replace(" ", "") == "o":
        command_open(args)
    #elif command.replace(" ", "") == "make" or command.replace(" ", "") == "m":
    #    command_make()
    elif command.replace(" ", "") == "list" or command.replace(" ", "") == "l":
        print("Mods:\n")
        for dir in os.listdir(os.path.join(oldir_filepath, launcher_dirs["Mods"])):
            print(f"{dir}\n")
        print("\nCampaigns:\n")
        for dir in os.listdir(os.path.join(oldir_filepath, launcher_dirs["Campaigns"])):
            print(f"{dir}\n")
        input("press enter to continue...")
        print() # adds empty line to terminal.
    elif command.replace(" ", "") == "settings" or command.replace(" ", "") == "s":
        command_settings()
    elif command.replace(" ", "") == "generatesettings" or command.replace(" ", "") == "g":
        settings_file = config_generate(settings_filepath, launcher_version, olexe_filepath)
        settings_file_exists = True
    elif command.replace(" ", "") == "displaylog" or command.replace(" ", "") == "d":
        command_displaylog()
    elif command.replace(" ", "") == "about" or command.replace(" ", "") == "a":
        print(f"Creator: Danish Craft\nLauncher Version: {launcher_version}\nConfig File Launcher Version: {config_read(settings_file, "INFO", "LauncherVersion")}")
        input("press enter to continue...")
        print() # adds empty line to terminal.
    elif command.replace(" ", "") == "help" or command.replace(" ", "") == "h":
        print("play <mod_name> - plays a mod (shortcut: p).\nopen <campaign_name> - opens a campaign (shortcut: o).\nlist - lists all installed mods and campaigns (shortcut: l)\n", end="")
        if settings_file_exists:
            print("settings - allows you to change settings for the level launcher (shortcut: s)\n", end="")
        else:
            print("generatesettings - generates a settings file for the DC Level Launcher (shortcut: g)\n", end="")
        if config_read(settings_file, "LAUNCHER", "PrintLogs") == "True":
            print("displaylog - (shortcut: d).\n", end="")
        print("about - info about the creator and Launcher version (shortcut: a)\nhelp - contains infomation about each command (shortcut: h).\nexit - exits the launcher (shortcut: e).")
        input("press enter to continue...")
        print() # adds empty line to terminal.
    elif command.replace(" ", "") == "exit" or command.replace(" ", "") == "e":
        print("exiting program")
        sys.exit()
    else:
        print(f"invalid command: {command}")
    get_command()

# COMMANDS #

# ARGS:
# string arg - name of the mod to play.
def command_play(arg: str):
    global oldir_filepath, launcher_dirs, log_filepath

    config_names = ["config.ini", "Config.ini"]
    config_file_name = ""

    # making sure the mod and it's config file exists.
    if not os.path.exists(os.path.join(oldir_filepath, launcher_dirs["Mods"], arg)):
        log(log_filepath, f"Mod: \"{arg}\" not found. make sure you typed it correctly.", ERR_LOG_LEVEL, True, term_text_red)
        input("hit enter to continue...")
        get_command()
    print(os.path.join(oldir_filepath, launcher_dirs["Mods"], arg))
    for config_name in config_names:
        if os.path.exists(os.path.join(oldir_filepath, launcher_dirs["Mods"], arg, config_name)):
            config_file_name = config_name
            break
    else:
        log(log_filepath, f"Mod: \"{arg}\" is missing a \"config.ini\" file.", ERR_LOG_LEVEL, True, term_text_red)
        input("hit enter to continue...")
        get_command()
    
    # create backup dir if it doesn't exist.
    if not os.path.exists(os.path.join(oldir_filepath, "backup")):
        os.mkdir(os.path.join(oldir_filepath, "backup"))
        log(log_filepath, "created backup folder.", NOTE_LOG_LEVEL, True, term_text_blue)
        log(log_filepath, "copying OLGame files to backup folder.", NOTE_LOG_LEVEL, True, term_text_blue)
        shutil.copytree(os.path.join(oldir_filepath, "OLGame"), os.path.join(oldir_filepath, "backup"), dirs_exist_ok=True)
        log(log_filepath, "copied OLGame files to backup folder.", NOTE_LOG_LEVEL, True, term_text_blue)
    log(log_filepath, "backup folder found.", INFO_LOG_LEVEL, config_read(settings_file, "LAUNCHER", "PrintLogs").lower() == "true", term_text_cyan)
    
    # reads mod config file.
    with open(os.path.join(oldir_filepath, launcher_dirs["Mods"], arg, config_file_name), "r") as f:
        mod_config = f.readlines()

    # mounts mod to game.
    if config_read(mod_config, "", "Content").lower() == "true":
        if sys.platform == "win32":
            shutil.copytree(os.path.join(oldir_filepath, launcher_dirs["Mods"], arg, "Content"), os.path.join(oldir_filepath, "OLGame", "CookedPCConsole"), dirs_exist_ok=True)
        elif sys.platform == "linux":
            shutil.copytree(os.path.join(oldir_filepath, launcher_dirs["Mods"], arg, "Content"), os.path.join(oldir_filepath, "OLGame", "CookedLinux"), dirs_exist_ok=True)
        log(log_filepath, "Content mounted.", NOTE_LOG_LEVEL, True, term_text_blue)
    if config_read(mod_config, "", "Config").lower() == "true":
        shutil.copytree(os.path.join(oldir_filepath, launcher_dirs["Mods"], arg, "Config"), os.path.join(oldir_filepath, "OLGame", "Config"), dirs_exist_ok=True)
        log(log_filepath, "Config mounted.", NOTE_LOG_LEVEL, True, term_text_blue)
    if config_read(mod_config, "", "Localization").lower() == "true":
        shutil.copytree(os.path.join(oldir_filepath, launcher_dirs["Mods"], arg, "Localization"), os.path.join(oldir_filepath, "OLGame", "Localization"), dirs_exist_ok=True)
        log(log_filepath, "Localization mounted.", NOTE_LOG_LEVEL, True, term_text_blue)
    if config_read(mod_config, "", "Movies").lower() == "true":
        shutil.copytree(os.path.join(oldir_filepath, launcher_dirs["Mods"], arg, "Movies"), os.path.join(oldir_filepath, "OLGame", "Movies"), dirs_exist_ok=True)
        log(log_filepath, "Movies mounted.", NOTE_LOG_LEVEL, True, term_text_blue)
    if config_read(mod_config, "", "SaveData").lower() == "true":
        shutil.copytree(os.path.join(oldir_filepath, launcher_dirs["Mods"], arg, "SaveData"), os.path.join(oldir_filepath, "OLGame", "SaveData"), dirs_exist_ok=True)
        log(log_filepath, "SaveData mounted.", NOTE_LOG_LEVEL, True, term_text_blue)

    # launches Outlast.
    if sys.platform == "win32":
        pass
    elif sys.platform == "linux":
        subprocess.run(["chmod", "+x", "OLGame.x86_64"], cwd=f"{os.path.join(oldir_filepath, "Binaries", "Linux")}")
        subprocess.run(["./OLGame.x86_64", "-NoSteam"], cwd=f"{os.path.join(oldir_filepath, "Binaries", "Linux")}")
    
    # unmounts mod from game.
    log(log_filepath, "unmounting Mod.", NOTE_LOG_LEVEL, True, term_text_blue)
    shutil.rmtree(os.path.join(oldir_filepath, "OLGame"))
    shutil.copytree(os.path.join(oldir_filepath, "backup"), os.path.join(oldir_filepath, "OLGame"), dirs_exist_ok=True)
    log(log_filepath, "Mod unmounted.", NOTE_LOG_LEVEL, True, term_text_blue)
    print() # adds empty line to terminal.

# ARGS:
# string arg - name of the campaign to play.
def command_open(arg: str):
    global oldir_filepath, launcher_dirs, log_filepath

    config_names = ["config.ini", "Config.ini"]
    config_file_name = ""

    # making sure the mod and it's config file exists.
    if not os.path.exists(os.path.join(oldir_filepath, launcher_dirs["Campaigns"], arg)):
        log(log_filepath, f"Mod: \"{arg}\" not found. make sure you typed it correctly.", ERR_LOG_LEVEL, True, term_text_red)
        input("hit enter to continue...")
        get_command()
    print(os.path.join(oldir_filepath, launcher_dirs["Campaigns"], arg))
    for config_name in config_names:
        if os.path.exists(os.path.join(oldir_filepath, launcher_dirs["Campaigns"], arg, config_name)):
            config_file_name = config_name
            break
    else:
        log(log_filepath, f"Mod: \"{arg}\" is missing a \"config.ini\" file.", ERR_LOG_LEVEL, True, term_text_red)
        input("hit enter to continue...")
        get_command()

    campaign_path = os.path.join(oldir_filepath, launcher_dirs["Campaigns"], arg)
    campaign_config = os.path.join(oldir_filepath, launcher_dirs["Campaigns"], arg, config_file_name)

    # create backup dir if it doesn't exist.
    if not os.path.exists(os.path.join(oldir_filepath, "backup")):
        os.mkdir(os.path.join(oldir_filepath, "backup"))
        log(log_filepath, "created backup folder.", NOTE_LOG_LEVEL, True, term_text_blue)
        log(log_filepath, "copying OLGame files to backup folder.", NOTE_LOG_LEVEL, True, term_text_blue)
        shutil.copytree(os.path.join(oldir_filepath, "OLGame"), os.path.join(oldir_filepath, "backup"), dirs_exist_ok=True)
        log(log_filepath, "copied OLGame files to backup folder.", NOTE_LOG_LEVEL, True, term_text_blue)
    log(log_filepath, "backup folder found.", INFO_LOG_LEVEL, config_read(settings_file, "LAUNCHER", "PrintLogs").lower() == "true", term_text_cyan)

    # reads campaign config file.
    with open(os.path.join(oldir_filepath, launcher_dirs["Campaigns"], arg, config_file_name), "r") as f:
        campaign_config = f.readlines()

    if config_read(campaign_config, "", "Localization").lower() == "true":
        shutil.copytree(os.path.join(oldir_filepath, launcher_dirs["Campaigns"], arg, "Localization"), os.path.join(oldir_filepath, "OLGame", "Localization"), dirs_exist_ok=True)
        log(log_filepath, "Localization mounted.", NOTE_LOG_LEVEL, True, term_text_blue)
    
    if config_read(campaign_config, "", "ModFileName").lower() == "none":
        if sys.platform == "win32":
            pass
        elif sys.platform == "linux":
            subprocess.run(["chmod", "+x", "OLGame.x86_64"], cwd=f"{os.path.join(oldir_filepath, "Binaries", "Linux")}")
            subprocess.run(["./OLGame.x86_64", os.path.join(campaign_path, campaign_name, ".udk"), "-NoSteam"], cwd=f"{os.path.join(oldir_filepath, "Binaries", "Linux")}")
    else:
        if sys.platform == "win32":
            pass
        elif sys.platform == "linux":
            subprocess.run(["chmod", "+x", "OLGame.x86_64"], cwd=f"{os.path.join(oldir_filepath, "Binaries", "Linux")}")
            subprocess.run(["./OLGame.x86_64", os.path.join(campaign_path, config_read(campaign_config, "", "ModFileName")), "-NoSteam"], cwd=f"{os.path.join(oldir_filepath, "Binaries", "Linux")}")

    # unmounts mod from game.
    log(log_filepath, "unmounting Mod.", NOTE_LOG_LEVEL, True, term_text_blue)
    shutil.rmtree(os.path.join(oldir_filepath, "OLGame"))
    shutil.copytree(os.path.join(oldir_filepath, "backup"), os.path.join(oldir_filepath, "OLGame"), dirs_exist_ok=True)
    log(log_filepath, "Mod unmounted.", NOTE_LOG_LEVEL, True, term_text_blue)
    print() # adds empty line to terminal.

def command_make():
    pass

def command_make_config():
    pass

def command_make_localization():
    pass

def command_make_content():
    pass

def command_settings() -> None:
    global settings_file, settings_file_exists, settings_filepath, log_filepath, olexe_filepath
    if not settings_file_exists:
        return

    varibles: dict = config_read_vars(settings_file, "INFO", True) # get's settings except ones from the "INFO" section.
    print("\nSettings:")
    for varible in varibles: # prints all available settings.
        print(varible)
    print("\nCommands:\nreset [r]\nexit [e]") # prints available commands.

    setting = input("type the setting you want to modify or command here: ")
    if setting == "reset" or setting == "r":
        settings_file = config_generate(settings_filepath, launcher_version, olexe_filepath)
        with open(settings_filepath, "w") as f: # overwrites the setting file with the default settings.
            f.writelines(settings_file)
        command_settings()
    elif setting == "exit" or setting == "e":
        print() # adds empty line to terminal.
        get_command()

    for varible in varibles: # loops through the varibles from the settings file.
        if setting == varible:
            var_type: str = "unknown"
            # determines data type of varible.
            if varibles[varible][1].lower() == "true" or varibles[varible][1].lower() == "false":
                var_type = "bool"
            elif varibles[varible][1].isdecimal():
                var_type = "int"
            else:
                try:
                    float(var_type)
                    var_type = "float"
                except ValueError:
                    var_type = "string"

            # displays varible infomation.
            if varibles[varible][2] != "":
                print(f"comment: {varibles[varible][2]}")
            print(f"current value (Type: {var_type}): {varibles[varible][1]}")

            # handles data type of varible and getting the new value of the varible.
            if var_type == "bool":
                setting_var_value = command_settings_bool()
            elif var_type == "float":
                setting_var_value = command_settings_float()
            elif var_type == "int":
                setting_var_value = command_settings_int()
            else:
                setting_var_value = input("type the new value of the setting here: ")
            varibles[varible][1] = setting_var_value
            with open(settings_filepath, "w") as f: # overwrites the setting file with the modified settings.
                f.writelines(config_write_vars(settings_file, varibles))
            log(log_filepath, f"Setting: {varible} set to \"{varibles[varible][1]}\".", NOTE_LOG_LEVEL, True, term_text_blue)
            input("hit enter to continue...")
            command_settings()
    print(f"varible: {setting} doesn't exist")
    command_settings()

def command_settings_bool() -> str:
    value: str = input("set setting to True or False [T/F]: ")
    if value.lower() == "t" or value.lower == "true":
        return "True"
    elif value.lower() == "f" or value.lower == "false":
        return "False"
    print(f"value: \"{value}\" is not a bool. please try again.")
    command_settings_bool()

def command_settings_int() -> str:
    value: str = input("new value for setting: ")
    if value.isdecimal():
        return value
    print(f"value: \"{value}\" is not a whole number (int). please try again.")
    command_settings_int()

def command_settings_float() -> str:
    value: str = input("new value for setting: ")
    try:
        return float(value)
    except ValueError:
        print(f"value: \"{value}\" is not a decimal number (float). please try again.")
        command_settings_float()

def command_displaylog() -> None:
    global log_filepath
    with open(log_filepath, "r") as f:
        log_file = f.readlines()
    
    for line in log_file: # loops through the log file and prints the logs with their log level colors.
        if line == "":
            continue
        elif line == "\n":
            print() # adds empty line.
        elif "[SESSION]" in line:
            term_text_green(line.rstrip("\n"))
        elif "[INFO]" in line:
            term_text_cyan(line.rstrip("\n"))
        elif "[NOTE]" in line:
            term_text_blue(line.rstrip("\n"))
        elif "[WARNING]" in line:
            term_text_yellow(line.rstrip("\n"))
        elif "[ERROR]" in line:
            term_text_red(line.rstrip("\n"))
        elif "[CRITICAL]" in line:
            term_text_magenta(line.rstrip("\n"))

    input("press enter to continue...")
    get_command()

if __name__ == "__main__":
    init()
