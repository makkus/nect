# -*- coding: utf-8 -*-

import types
import os.path
import abc
import six
import sys
import yaml
import collections
import itertools

from stevedore import extension

import logging
log = logging.getLogger(__name__)

DEFAULT_CHANNEL = "default"
CONFIG_CHANNEL = "config"


def load_extensions():

    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

    mgr = extension.ExtensionManager(
        namespace='nect.nects',
        invoke_on_load=True
    )

    log.debug("Registered plugins: {}".format(", ".join(ext.name for ext in mgr.extensions)))

    return {ext.name: ext.plugin() for ext in mgr.extensions}


def construct_result(main_result, part_result):

    if not part_result:
        return

    if not is_channel_dict(part_result):
        part_result = {DEFAULT_CHANNEL: create_channel(part_result)}

    for channel_name, channel_data in part_result.items():

        # TODO: should I leave the config channel in so previous nects can configure the next nect?
        if channel_name == CONFIG_CHANNEL:
            continue

        if main_result.get(channel_name, False):
            log.debug("Merging channel '{}' into existing result.".format(channel_name))
            main_result[channel_name] = itertools.chain(main_result[channel_name], channel_data)
        else:
            log.debug("Creating new result channel '{}'".format(channel_name))
            main_result[channel_name] = channel_data


def create_channel(channel_data):

    if isinstance(channel_data, collections.Sequence) and not isinstance(channel_data, str):
        result = channel_data
    elif isinstance(channel_data, str) or isinstance(channel_data, int):
        result = [channel_data]
    elif isinstance(channel_data, dict):
        result = []
        for k, v in channel_data.items():
            result.append((k, v))
    elif isinstance(channel_data, types.GeneratorType):
        result = channel_data
    else:
        raise Exception("Can't create channel for {} (type: {})".format(channel_data, type(channel_data)))
    return result


def is_channel_dict(data):

    if type(data) is dict and (data.get(DEFAULT_CHANNEL, False) or data.get(CONFIG_CHANNEL, False)):
        return True
    else:
        return False


class Nector(object):

    @staticmethod
    def create(pipeline):

        if type(pipeline) is dict:
            # TODO: do some validation?
            pass
        elif os.path.isfile(pipeline):
            with open(pipeline, 'r') as f:
                pipeline = yaml.load(f)

        return Nector(pipeline)

    def __init__(self, pipeline):
        self.pipeline = pipeline
        # TODO: only load required extensions
        self.nects = load_extensions()

    def start_pipeline(self):

        channels = {}

        execution_step = 0
        for nect in self.pipeline:

            # no config, only name
            if type(nect) is str:
                nect_type = nect
                nect_channel = []
            # dict config (name & config)
            elif type(nect) is dict:
                nect_keys = list(nect.keys())

                if len(nect_keys) != 1:
                    raise Exception("Only one (nect) key per pipeline item allowed!")

                nect_type = nect_keys[0]

                nect_channel_data = nect.get(nect_keys[0])
                if is_channel_dict(nect_channel_data):
                    nect_channel = nect_channel_data
                else:
                    # means we have 'config' data
                    nect_channel = create_channel(nect_channel_data)

            log.info("Entering nect '{}'".format(nect_type))

            #TODO: what should be the default behaviours? Maybe merge? Who should get priority? Configurable?
            # if not channels.get(CONFIG_CHANNEL, False):
            channels[CONFIG_CHANNEL] = nect_channel

            temp_channels = self.execute_nect(execution_step, nect_type, channels)
            if is_channel_dict(temp_channels):
                channels = temp_channels
            else:
                channels = {DEFAULT_CHANNEL: create_channel(temp_channels)}

            log.debug("Output channels for nect '{}':\n\t{}".format(nect_type, channels))
            execution_step = execution_step + 1

        print("Channel: 'default'")
        print("-----------------")
        for i in channels.get(DEFAULT_CHANNEL):
            print(i)

        for channel_name in channels.keys():

            if channel_name != DEFAULT_CHANNEL:
                print("")
                print("Channel: '{}'".format(channel_name))
                print("-----------------")
                for i in channels.get(channel_name):
                    print(i)


    def execute_nect(self, execution_step, nect_type, channels):

        nect = self.nects.get(nect_type, None)

        if not nect:
            raise Exception("Can't find nect: {}".format(nect))

        nect.set_channels(execution_step, channels)
        result = nect.process()
        return result

@six.add_metaclass(abc.ABCMeta)
class Nect(object):

    def __init__(self):
        self.channels = {}

    def set_channels(self, execution_step, channels):

        self.channels[execution_step] = channels
        self.current_execution_step = execution_step

    def set_current_channel(self, current_channel_name):
        self.current_channel_name = current_channel_name

    def validate_channel(self):
        return True

    @abc.abstractmethod
    def nect(self):
        pass

    def get_config(self, config_key, default=None):
        config = self.get_channel(CONFIG_CHANNEL)
        if config:
            return next((config_tuple[1] for config_tuple in config if config_tuple[0] == config_key), default)
            return config.get(config_key, default)
        else:
            return default

    def get_available_channel_names(self):
        return [name for name in self.channels[self.current_execution_step].keys() if name != CONFIG_CHANNEL]

    def get_channel(self, channel_name=DEFAULT_CHANNEL):
        return self.channels[self.current_execution_step].get(channel_name, None)

    def get_current_channel(self):

        return self.channels[self.current_execution_step].get(self.current_channel_name)

    def get_current_channels(self):

        return self.channels[self.current_execution_step]

    def get_current_channel_name(self):

        return self.current_channel_name

    def process(self):

        validation_result_channels = self.validate_channel()
        if not validation_result_channels:
            raise Exception("Parameters not valid")

        result_channels = {}
        # first, process the 'default' channels
        log.debug("Processing channel 'default'")
        self.set_current_channel(DEFAULT_CHANNEL)
        temp_result = self.nect()
        construct_result(result_channels, temp_result)

        for channel_name in self.get_current_channels().keys():
            if channel_name != DEFAULT_CHANNEL and channel_name != CONFIG_CHANNEL:
                log.debug("Processing channel '{}'".format(channel_name))
                self.set_current_channel(channel_name)
                temp_result = self.nect()
                construct_result(result_channels, temp_result)


        return result_channels
