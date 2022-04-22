from string import Template
import ast
import os
import sys
import re


class StaticCodeAnalyzer:
    max_len = 79
    indentation = 4
    msg = Template("$filename: Line $line: $msg_code $msg")
    msgs = {"S001": "Too long",
            "S002": "Indentation is not a multiple of four",
            "S003": "Unnecessary semicolon",
            "S004": "At least two spaces required before inline comments",
            "S005": "TODO found",
            "S006": "More than two blank lines used before this line",
            "S007": Template("Too many spaces after '$name'"),
            "S008": Template("Class name '$name' should use CamelCase"),
            "S009": Template("Function name '$name' should use snake_case"),
            "S010": Template("Argument name '$name' should be snake_case"),
            "S011": Template("Variable '$name' in function should be snake_case"),
            "S012": "Default argument value is mutable"
            }

    def __init__(self) -> None:
        self.dir = None
        self.filenames = list()
        self.code = dict()
        self.issues = dict()

    def get_user_input(self) -> None:
        """Get a filename or a directory with python code"""
        arg = sys.argv
        if len(arg) != 2:
            print("Wrong number of arguments!")
            exit()
        self.dir = arg[1]

    def get_filenames(self) -> None:
        """Check the given directory and make a list of files in it"""
        if os.path.isdir(self.dir):
            self.filenames = [os.path.join(self.dir, i)
                              for i in os.listdir(self.dir)
                              if os.path.isfile(os.path.join(self.dir, i))]
        else:
            self.filenames.append(self.dir)

    def get_code(self) -> None:
        """Read the files and store the code"""
        for name in self.filenames:
            with open(name, 'r') as file:
                self.code[name] = file.readlines()
                self.issues[name] = {i: set() for i in range(1, len(self.code[name]) + 1)}

    def make_analyze(self) -> None:
        """Analyze all python files according to PEP8;
        Only several issues are implemented"""
        self.get_filenames()
        self.get_code()
        for file in self.filenames:
            self.check_s001(file)
            self.check_s002(file)
            self.check_s003(file)
            self.check_s004(file)
            self.check_s005(file)
            self.check_s006(file)
            self.check_s007(file)
            self.check_ast(file)

    def show_msg(self, **kwargs) -> None:
        """Show one particular issue"""
        msg_code = kwargs.get("msg_code")
        if msg_code in {"S007", "S008", "S009", "S010", "S011"}:
            name = kwargs.get("name")
            print(self.msg.substitute(filename=kwargs.get("file"),
                                      line=kwargs.get("line"),
                                      msg_code=msg_code,
                                      msg=self.msgs.get(msg_code).substitute(name=name)))
        else:
            print(self.msg.substitute(filename=kwargs.get("file"),
                                      line=kwargs.get("line"),
                                      msg_code=msg_code,
                                      msg=self.msgs.get(msg_code)))

    def show_msgs(self) -> None:
        """Show all messages stored during the analysis"""
        for file, lines in sorted(self.issues.items()):
            for line, issues in sorted(lines.items()):
                for issue in sorted(issues, key=lambda x: x[0] if isinstance(x, tuple) else x):
                    if isinstance(issue, tuple):
                        self.show_msg(file=file, line=line, msg_code=issue[0], name=issue[1])
                    else:
                        self.show_msg(file=file, line=line, msg_code=issue)

    def check_s001(self, file) -> None:
        """Check the code if length of a line > 79 symbols"""
        for i, line in enumerate(self.code.get(file), start=1):
            if bool(len(line) > self.max_len):
                self.issues[file][i].add("S001")

    def check_s002(self, file) -> None:
        """Check the code if an indentation is not a multiple of four"""
        for i, line in enumerate(self.code.get(file), start=1):
            if len(line.lstrip()) > 0 and (len(line) - len(line.lstrip())) % 4 > 0:
                self.issues[file][i].add("S002")

    @staticmethod
    def find_boundaries(line) -> dict:
        """Return indexes of the boundaries of all strings and a comment if it exists"""
        quotes = [i for i in range(len(line)) if line[i] in ('\'', '"', '#')]
        string_opened = False
        quote = None
        res = {"head": list(), "tail": list(), "comment": None}
        for i in quotes:
            if line[i] == '#' and not string_opened:
                res["comment"] = i
                return res
            if not string_opened:
                quote = line[i]
                string_opened = True
                res["head"].append(i)
            else:
                if line[i] != quote or line[i - 1] == '\\':
                    continue
                string_opened = False
                res["tail"].append(i)
        return res

    def check_s003(self, file) -> None:
        """Check if an unnecessary semicolon is placed in a line of code."""
        for i, line in enumerate(self.code.get(file), start=1):
            semicolons = [j for j in range(len(line)) if line[j] == ';']
            for j in semicolons:
                borders = self.find_boundaries(line)
                found = False
                for h, t in zip(borders["head"], borders["tail"]):
                    if h < j < t:
                        found = True
                        break
                if borders["comment"] is not None and j > borders["comment"]:
                    found = True
                if not found:
                    self.issues[file][i].add("S003")
                    break

    def check_s004(self, file) -> None:
        """Check if 2 spaces are placed before a comment"""
        for i, line in enumerate(self.code.get(file), start=1):
            borders = self.find_boundaries(line)
            pos = borders["comment"]
            if pos is not None and pos != 0:
                if pos == 1 or (pos > 2 and line[pos - 2:pos] != '  '):
                    self.issues[file][i].add("S004")

    def check_s005(self, file) -> None:
        """Check if a todo exists"""
        for i, line in enumerate(self.code.get(file), start=1):
            borders = self.find_boundaries(line)
            pos = borders["comment"]
            if pos is not None:
                pattern = re.compile(r"#.*\s+TODO\s+.*", re.IGNORECASE)
                if bool(pattern.match(line[pos:])):
                    self.issues[file][i].add("S005")

    def check_s006(self, file) -> None:
        """Check if more than 2 empty lines placed in the code"""
        count = 0
        for i, line in enumerate(self.code.get(file), start=1):
            if len(line.strip()) == 0:
                count += 1
            else:
                if count > 2:
                    self.issues[file][i].add("S006")
                count = 0

    def check_s007(self, file) -> None:
        """Check if more than 1 space placed after def/class keyword"""
        pattern_def = re.compile(r"\s*def\s{2,}[\w\S\D]+([(].*[)])?:")
        pattern_class = re.compile(r"\s*class\s{2,}[\w\S\D]+([(].*[)])?:")
        for i, line in enumerate(self.code.get(file), start=1):
            if pattern_def.match(line):
                self.issues[file][i].add(("S007", "def"))
            elif pattern_class.match(line):
                self.issues[file][i].add(("S007", "class"))

    def check_s008(self, file, node) -> None:
        """Check if a class name in CamelCase"""
        if isinstance(node, ast.ClassDef):
            name = node.name
            if not self.is_camel_case(name):
                self.issues[file][node.lineno].add(("S008", name))

    def check_s009(self, file, node) -> None:
        """Check if a function definition in snake_case"""
        if isinstance(node, ast.FunctionDef):
            name = node.name
            if not self.is_snake_case(name):
                self.issues[file][node.lineno].add(("S009", name))

    def check_ast(self, file) -> None:
        """Make a tree object, call the methods using the ast module"""
        tree = ast.parse(''.join(self.code.get(file)))
        for node in ast.walk(tree):
            self.check_s008(file, node)
            self.check_s009(file, node)
            self.check_s010(file, node)
            self.check_s011(file, node)
            self.check_s012(file, node)

    @staticmethod
    def is_snake_case(s) -> bool:
        """Return if a string is in snake_case"""
        return bool(re.match(r"^[a-z\d_]+$", s))

    @staticmethod
    def is_camel_case(s) -> bool:
        """Return if a string is in CamelCase"""
        return bool(re.match(r"^([A-Z][a-z\d]+)+$", s))

    def check_s010(self, file, node) -> None:
        """Check if the function/method arguments are not in snake_case"""
        if isinstance(node, ast.FunctionDef):
            arguments = ((a.arg, a.lineno) for a in node.args.args)
            for a in arguments:
                if not self.is_snake_case(a[0]):
                    self.issues[file][a[1]].add(("S010", a[0]))

    def check_s011(self, file, node) -> None:
        """Check if function/method variables definition in snake_case"""
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            if not self.is_snake_case(node.id):
                self.issues[file][node.lineno].add(("S011", node.id))
        if isinstance(node, ast.Attribute) and isinstance(node.ctx, ast.Store):
            if not self.is_snake_case(node.attr):
                self.issues[file][node.lineno].add(("S011", node.attr))

    def check_s012(self, file, node) -> None:
        """Check if default arguments in function/method definition are mutable"""
        if isinstance(node, ast.FunctionDef):
            for d in node.args.defaults:
                if isinstance(d, (ast.List, ast.Dict, ast.Set)):
                    self.issues[file][d.lineno].add("S012")


def main():
    a = StaticCodeAnalyzer()
    a.get_user_input()
    a.make_analyze()
    a.show_msgs()


if __name__ == "__main__":
    main()
