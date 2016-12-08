# -*- coding: utf-8 -*-

from nect import Nect, DEFAULT_CHANNEL, CONFIG_CHANNEL
from operator import itemgetter
import pipes
from subprocess import PIPE, Popen, check_output
import time
import random
import copy
from nect.nects.helpers import uniq
import logging

log = logging.getLogger(__name__)

DEFAULT_SLOT_NAME = "default_slot"

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
            result = sorted(self.get_channel(), reverse=self.get_config("reverse", False))

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


class Store(Nect):

    def __init__(self):
        super().__init__()
        self.slots = {}

    def nect(self):

        # we really only need to do this once, not for every channel seperately
        if self.get_current_channel_name() != DEFAULT_CHANNEL:
                return None

        action = self.get_config("action", "write")
        slot_name = self.get_config("slot_name", DEFAULT_SLOT_NAME)

        result = self.get_current_channels()

        if action == "write":

            for channel_name in self.get_available_channel_names():

                # TODO: check whether copy.copy is good enough (or too much...)
                self.slots[slot_name+"_"+channel_name] = copy.copy(self.get_channel(channel_name))

        elif action == "read":

            for slot_channel_name, slot_data in self.slots.items():

                if slot_channel_name.startswith(slot_name+"_"):
                    result[slot_channel_name] = slot_data

        else:
            raise Exception("No action {} available.".format(action))

        return result


class Uniq(Nect):

    def nect(self):

        seq = self.get_current_channel()

        key = self.get_config("key", None)
        if key:
            def idfun(x):
                return x.get(key)
        else:
            idfun = None

        return uniq(seq, idfun)


class DictToList(Nect):

    def nect(self):

        mode = self.get_config("mode", "dict")

        if mode == "dict":

            key = self.get_config("key")

            if not key:
                raise Exception("No filter key provided")

            return (item.get(key) for item in self.get_current_channel() if item.get(key, False))

        else:
            raise Exception("Mode {} not supported.".format(mode))


class ListToDict(Nect):

    def nect(self):

        target = self.get_channel(self.get_config("target_dict"))
        source = self.get_channel(self.get_config("source_list"))

        lookup_key = self.get_config("key")
        if self.get_current_channel_name() != DEFAULT_CHANNEL:
            return None

        print(self.get_current_channels())

        return (item for item in target if item.get(lookup_key) in source)
