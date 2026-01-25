import json
import time
import os
import subprocess

os.environ["PATH"] = r"C:\msys64\mingw64\bin;" + os.environ["PATH"]

try:
    data = json.load(open("data.json", "r"))
    data["extensions"] = {}
    extmarkers = []
except Exception as e:
    print(f"data loading error: {e}")

try:
    settings = json.load(open("settings.json", "r"))
    compilerpath = settings["compilerpath"]
except Exception as e:
    print(f"settings loading error: {e}")

try:
    for extension in os.listdir("extensions"):
        content = json.load(open("extensions/" + extension, "r"))
        data["extensions"][content["name"]] = content
        for marker in content["markers"]:
            extmarkers.append(marker)
        print(f"loaded {content['name']} as {extension}")
except Exception as e:
    print(f"extension loading error: {e}")

helptxt = """
FireflyCompiler v0.2 by Dsg2 (github)

commands:
    help / h - display help message again
    exit

    r - read file
        it reads a file
        
    t - transpile file
        it transpiles a .FF file to .C
        
    c - compile file
        select a .c file to compile to an .exe
        can add flags, each separate entry is a separate item in python subprocess call list
            (pretty much, anything separated by a space is a separate entry)
            e.g.:
            > c
            filename: wdasdwsdwa.c
            add flag: -o
            add flag: wasdwasdwa.exe
        after adding wanted flags, type start.
            add flag: start
        or if you don't want to compile:
            add flag: abort

base(vanillla) Firefly documentation:
    include: include <name> (includes a header or library)
    var: var <name> <type> (initialises a variable of a type)
    set: set <name> <expr> (sets a variable to something)
    func: func <name> <type> <args> (initialises a function with arguments, needed for main())
    return: return <expr> (returns something)
    call: call <name> (calls a function)
    if: if <cond>
    else: else
    while: while <cond>
    for: for <cond> (for loop, SPACES MATTERS, example: for i = 0 i < 10 i++)
    end: end (pretty much end brackets)

basics of Firefly:
    each line in Firefly consist of:
    a marker: the first word in the line, used for the entire transpiling brance. make sure no two markers in your extensions are conflicting
    the rest: probably useful stuff

creating your own extensions:
    file format:
        the program isn't too strict or picky about extensions :)))
        
        the only essential keys in the json file are:
            "name": what your extension is called (and used as while compiling), so make sure that there aren't any libraries with the same names
            "markers": the markers that your extension identifies (refer to above)
            "sequence": the C equivalent of your marker, where you give your equivalent and "{expr}" as the variable parameter
            
        there is also an additional key that you probably will use:
            "scripts": the python program that runs to add custom rules or parsing of a Firefly line to a line in c
            
            here are the basics of a script:
                pretty much just exec()
                each line is separated by "\\n" and indents = 4 spaces
                currently, the local namespace gives dict "temp" and string "line" if you need it
                temp structure:
                temp = {"vars":{<variable name>:<type>}}
                
                after you finish doing whatever, set variable "out" to your final result, which will replace {expr}
            
            note that there is only 1 parameter available
            to counteract this, just be creative with your script parsing :)
            for example, custom var1 var2 -> custom(var1, var2) can be done with sequence being "custom({expr})" and the script reading the two variables using split()
"""

task = None
file = None
cache = []
env = None
lsopt = []

def spaceformat(inp, letter=",", spacing=1):
    cache = ""
    num = 0
    for char in inp:
        if char != " ":
            cache += char
        else:
            if num < spacing:
                num = num + 1
                cache += " "
            else:
                num = 0
                cache += f"{letter} "
    return cache

def istype(string):
    types = ["char", "float", "double", "int"]
    if string in types:
        return 1
    else:
        return 0

def ext(line):
    global data, env
    marker = line.split(maxsplit=1)[0]
    for extension in data["extensions"]:
        if marker in data["extensions"][extension]["markers"]:
            content = data["extensions"][extension]
            break
    if marker not in content["scripts"]:
        return content["sequence"][marker].replace("{expr}", line.split(maxsplit=1)[1])
    else:
        try:
            env = {"temp":data["temp"], "line":line}
            exec(str(content["scripts"][marker]), {}, env)
            return content["sequence"][marker].replace("{expr}", env["out"])
        except Exception as e:
            print(f"extension script '{marker}' error {e}")
            return f"// extension script '{marker}' error {e}"

def enc(line):
    global data
    marker = line.split(maxsplit=1)[0]
    if marker in data["sequence"]:
        match marker:
            case "include":
                name = line.split(maxsplit=1)[1]
                if name in data["extensions"]:
                    if "script" in data["extensions"][name]:
                        env = {"temp":data["temp"], "line":line}
                        exec(str(data["extensions"][name]["script"]), {}, env)
                        if isinstance(out, str):
                            return [data["sequence"][marker].replace("{name}", name), out]
                        elif isinstance(out, list):
                            return [data["sequence"][marker].replace("{name}", name)] + out
                return data["sequence"][marker].replace("{name}", name)
            case "var":
                parts = line.split()
                name, typ = parts[1], parts[2]
                if "[" in name:
                    fname = name.split("[")[0]
                else:
                    fname = name
                if "vars" not in data["temp"]:
                    data["temp"] = {"vars":{}}
                data["temp"]["vars"][fname] = typ
                if not istype(typ):
                    print(f"warning: {typ} is not a valid var type")
                return data["sequence"][marker].replace("{name}", name).replace("{type}", typ)
            case "set":
                parts = line.split(maxsplit=2)
                name, expr = parts[1], parts[2]
                return data["sequence"][marker].replace("{name}", name).replace("{expr}", expr)
            case "func":
                parts = line.split(maxsplit=3)
                name, typ, args_str = parts[1], parts[2], spaceformat(parts[3])
                if not istype(typ):
                    print(f"warning: {typ} is not a valid func type")
                return data["sequence"][marker].replace("{name}", name).replace("{type}", typ).replace("{args}", args_str)
            case "return":
                expr = line.split(maxsplit=1)[1]
                return data["sequence"][marker].replace("{expr}", expr)
            case "call":
                name = line.split(maxsplit=1)[1]
                return data["sequence"][marker].replace("{name}", name)
            case "if":
                cond = line.split(maxsplit=1)[1]
                return data["sequence"][marker].replace("{cond}", cond)
            case "else":
                return data["sequence"][marker]
            case "while":
                cond = line.split(maxsplit=1)[1]
                return data["sequence"][marker].replace("{cond}", cond)
            case "for":
                cond = spaceformat(line.split(maxsplit=1)[1], ";", 2)
                return data["sequence"][marker].replace("{cond}", cond)
            case "end":
                return data["sequence"][marker]

print("FireflyCompiler v0.2 by Dsg2 (github)")
print("type 'help' for help and documentation")
print()

while True:
    task = input("> ")
    print()
    match task:
        case "help":
            print(helptxt)
        case "h":
            print(helptxt)
        case "r":
            filename = input("filename: ")
            try:
                file = open(filename, "r").read()
                for line in file.splitlines():
                    print(line)
            except Exception as e:
                print(e)
            file = None
        case "t":
            cache = []
            filename = input("filename: ")
            data["temp"] = {}
            try:
                file = open(filename, "r").read().splitlines()
                for ind, line in enumerate(file):
                    if line:
                        try:
                            marker = line.split(maxsplit=1)[0]
                        except:
                            pass
                        
                        if marker in data["markers"]:
                            ret = enc(line)
                            if isinstance(ret, str):
                                cache.append(enc(line))
                            elif isinstance(ret, list):
                                for l in ret:
                                    cache.append(l)
                        else:
                            if marker in extmarkers:
                                ret = ext(line)
                                if isinstance(ret, str):
                                    cache.append(ret)
                                elif isinstance(ret, list):
                                    for l in ret:
                                        cache.append(l)
                            else:
                                print(f"unknown marker '{marker}' on line {ind + 1}")
                
                filename = f"{filename.rsplit('.',1)[0]}_{str(time.time()).split('.')[1]}.c"
                with open(filename, "w") as f:
                    for line in cache:
                        f.write(line + "\n")
                print(f"written to {filename}")
            except Exception as e:
                print(f"translation error: {e}")
        case "c":
            filename = input("filename: ")
            flags = []
            inp = None
            while inp != "start" and inp != "abort":
                inp = input("add flag: ")
                if inp != "start":
                    flags.append(inp)
            if inp == "start":
                result = subprocess.run([compilerpath] + [filename] + flags, capture_output=True, text=True)
                if result.returncode != 0:
                    print("compile failed:")
                    print(result.stderr)
                else:
                    print("compile succeeded")
            else:
                pass
        case "exit":
            break
        case "overload":
            arr = []
            string = ""
            while True:
                for i in range(26):
                    string += "qwertyuiopasdfghjklzxcvbnm"[i]
                arr.append(string)
        case "flush":
            with open(f"{str(time.time()).split('.')[1]}.flush", "w") as f:
                json.dump(data, f)
        case "ls":
            print("folders:")
            for path in os.listdir():
                if os.path.isdir(path):
                    print(path)
            print("\nfiles:")
            lsopt = []
            t = 0
            for path in os.listdir():
                if "." in path:
                    if path.split(".")[1] == "ff":
                        print(f"{t} - {path}")
                        lsopt.append(path)
                        t = t + 1
        case _:
            print(f"command {task} not recognised")
    print()