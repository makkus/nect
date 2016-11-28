from nect.nect import Nect
from operator import itemgetter
import pipes
from subprocess import PIPE, Popen, check_output

class StaticList(Nect):

    def nect(self):

        result = []

        for i in self.get_channel("config"):
            result.append(i)

        return result

class Sort(Nect):

    def dict_sort_channel(self, sort_key, channel_data, reverse=False):

        sorted_list = sorted(channel_data, key=itemgetter(sort_key), reverse=reverse)
        return sorted_list


    def nect(self):

        if self.get_config("sort_key"):
            # we assume channel is list of dicts
            result = self.dict_sort_channel(self.get_config("sort_key"), self.get_channel(), reverse=self.get_config("reverse"))
        else:
            result = sorted(self.get_channel(), reverse=self.get_config("reverse"))

        return result

class Shell(Nect):

    def nect(self):

        shell_output = check_output(self.get_config('command'), shell=True, cwd=self.get_config('working_dir')).split()

        output = []
        for o in shell_output:
            l = o.decode("utf-8")
            output.append(l)

        return output


class ShellPipe(Nect):

    # TODO: build a cached list on certain conditions, to also enable generator inputs
    def find_list_element_via_key_and_value(self, key, value):

        result = []

        for line in self.get_channel():
            if line.get(key, False) == value:
                result.append(line)

        if len(result) == 0:
            raise Exception("can't find element for key '{}' and value '{}'".format(key, value))
        elif len(result) > 1:
            raise Exception("more than one result for key '{}' and value '{}'".format(key, value))
        else:
            return result[0]

    def nect(self):

        command = self.get_config('command')
        if not command:
            raise Exception("no command specified")

        display_key = self.get_config('display_key')
        value_key = self.get_config('value_key')

        if not display_key and value_key:
            display_key = value_key
        if not value_key and display_key:
            value_key = display_key

        t = pipes.Template()
        t.append(command, '--')
        f = t.open('pipefile', 'w')

        for line in self.get_channel():
            if type(line) is str:
                f.write(str(line)+'\n')
            elif type(line) is dict:
                display_value = line.get(display_key, None)
                if not display_value:
                    raise Exception("display_key {} not specified".format(display_key))
                f.write(str(display_value)+'\n')

        f.close()
        sel = open('pipefile').read().strip()
        if display_key == value_key:
            return sel
        elif value_key == '<full>':
            return self.find_list_element_via_key_and_value(display_key, sel)
        else:
            result = self.find_list_element_via_key_and_value(display_key, sel)
            result_value = result.get(value_key, False)
            if not result_value:
                raise Exception("could not find value key '{}' in: '{}'".format(value_key, result))
            return result_value
