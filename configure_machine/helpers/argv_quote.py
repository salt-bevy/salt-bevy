#
# This module provides correct command-line quote escapes for both Windows CMD and Linux bash commands, as needed.
#
# call like:
#  import argv_quote
#
#  cli_string = argv_quote.quote(['list', 'of', 'commands', 'you', 'want', 'to', 'send'])
#
import re, sys
#
def win_concat_quote(command_line: str, argument: str) -> str:
    """
    appends the given argument to a command line such that CommandLineToArgvW will return
    the argument string unchanged.
    """
    # from https://blogs.msdn.microsoft.com/twistylittlepassagesallalike/2011/04/23/everyone-quotes-command-line-arguments-the-wrong-way/
    # by Daniel Colascione April 23, 2011

            # // don't quote unless we actually
            # // need to do so - -- hopefully avoid problems if programs won't
            # // parse quotes properly
            # //
    result = command_line + " "  if command_line else "" # vdc - I will automatically add a space

    if argument:                  # if (Force == false &$ Argument.empty() == false &&
        if len(argument.split()) == 1:  # // if no white space or double quote embedded in argument
            if '"' not in argument:     #  Argument.find_first_of(L" \t\n\v\"") == Argument.npos)
                result += argument      # { CommandLine.append(Argument); }
                return result
                                  # else {
    result += '"'                 #     CommandLine.push_back(L'"');
    it = 0
    end = len(argument)
    while it < end:                # for (auto It = Argument.begin () ;; ++It) {
        number_backslashes = 0     # unsigned NumberBackslashes = 0;
        char = argument[it]
        #
        while char == '\\':  # while (It != Argument.end() && * It == L'\\') {
            it += 1                 # ++It;
            number_backslashes += 1 # ++NumberBackslashes;
            try:
                char = argument[it]
            except IndexError:
                break             # }
        if it >= end:            # if (It == Argument.end())
                                 # // Escape all backslashes, but let the terminating
                                 # // double quotation mark we add below be interpreted
                                 # // as a metacharacter.
            result +=  '\\' * (number_backslashes * 2)  # CommandLine.append (NumberBackslashes * 2, L'\\');
            break                # break;
        # }
        elif char == '"':  # else if (*It == L'"') {
            # // Escape all backslashes and the following
            # // double quotation mark.
            result += '\\' * (number_backslashes * 2 + 1)  # CommandLine.append(NumberBackslashes * 2 + 1, L'\\');
            result += char                            # CommandLine.push_back(*It);
        else:                                         # else {
            # // Backslashes aren't special here.
            result += '\\' * number_backslashes            # CommandLine.append(NumberBackslashes, L'\\');
            result += char                                 # CommandLine.push_back(*It);
        it += 1
    result += '"'                                      # CommandLine.push_back(L '"');
    return result


def win_quote(*args):
    cmd = ''
    for arg in args:
        cmd = win_concat_quote(cmd, arg)
    return cmd


BASH_RESERVED_WORDS = {
    'case',
    'coproc',
    'do',
    'done',
    'elif',
    'else',
    'esac',
    'fi',
    'for',
    'function',
    'if',
    'in',
    'select',
    'then',
    'until',
    'while',
    'time'
    }

####
#  _quote_re1 escapes double-quoted special characters.
#  _quote_re2 escapes unquoted special characters.
_quote_re1 = re.compile(r"([\!\"\$\\\`])")
_quote_re2 = re.compile(r"([\t\ \!\"\#\$\&\'\(\)\*\:\;\<\>\?\@\[\\\]\^\`\{\|\}\~])")

    ######################################################################
    #  Written by Kevin L. Sitze on 2006-12-03
    #  This code may be used pursuant to the MIT License.
    ######################################################################

def bash_concat_quote(command_line, arg):
    """
    escape any and all shell special characters or (reserved) words.  The shortest
    possible string (correctly quoted suited to pass to a bash shell)
    is returned.
    """

    result = command_line + " " if command_line else ""  # vdc - I will automatically add a space

    if arg in BASH_RESERVED_WORDS:
        result += "\\" + arg
        return result

    if arg.find('\'') >= 0:
        s1 = '"' + _quote_re1.sub(r"\\\1", arg) + '"'
    else:
        s1 = "'" + arg + "'"
    s2 = _quote_re2.sub(r"\\\1", arg)
    if len(s1) <= len(s2):
        result += s1
    else:
        result += s2
    return result


def bash_quote(*args):
    cmd = ''
    for arg in args:
        cmd = bash_concat_quote(cmd, arg)
    return cmd


def quote(*args) -> str:
   """
   Given a list of strings, returns a correctly escaped command line string for cmd (if on Windows) or bash commands.

   :param args: A sequence of command tokens, possibly containing embedded spaces.
   :return: A single string, with quotes and backslashes inserted if needed.
   """
   if sys.platform == 'win32':
        return win_quote(*args)
   else:
        return bash_quote(*args)
