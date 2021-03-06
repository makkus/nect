from nect import Nect
from operator import itemgetter
import pipes
from subprocess import PIPE, Popen, check_output
import time
import random

import logging
log = logging.getLogger(__name__)


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
            result = self.dict_sort_channel(self.get_config("sort_key"), self.get_channel(), reverse=self.get_config("reverse", False))
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

class PositionListFilter(Nect):

    def nect(self):
        return self.get_channel()[self.get_config("index")]

class DummyList(Nect):

    def list_generator(self):

        for i in range(1, self.get_config("items", 9)+1):

            time.sleep(self.get_config("pause") / 1000)
            log.debug("Sleeping for {} ms".format(self.get_config("pause") / 1000))

            format = self.get_config("format", "int")

            if format == "int":
                item =  random.randint(1000, 9999)
            elif format == "str":
                item = "xxx"

            yield item

    def nect(self):
        return self.list_generator()


class Dict(Nect):

    def __init__(self):
        super().__init__()
        self.slots = {}

    def nect(self):

        slot_name = self.get_config("slot_name")
        action = self.get_config("action")
        filter_key = self.get_config("filter_key")

        if "store" == action:

            self.slots[slot_name] = self.get_channel()

        if "pass" == action or "store" == action:

            result = (item.get(filter_key) for item in self.get_channel() if item.get(filter_key, False))

        elif "retrieve" == action:

            retrieve_key = self.get_config("retrieve_key")

            match_values = [item_inner.get(filter_key, None) for item_inner in self.get_channel()]

            result = (item for item in self.get_channel() if item.get(filter_key, False) and item.get(filter_key, None) in (item_inner.get(filter_key, None) for item_inner in self.get_slot(slot_name) ))

            print("SSS")
            print(list(result))
            for r in result:
                print(r)

        else:
            raise Exception("Unsupported action {}".format(action))



        return result
