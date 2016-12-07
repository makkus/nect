# -*- coding: utf-8 -*-

import types
import os.path
import abc
import six
import sys
import yaml
import collections


from stevedore import extension

import logging
log = logging.getLogger(__name__)


def load_extensions():

    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

    mgr = extension.ExtensionManager(
        namespace='nect.nects',
        invoke_on_load=True
    )

    log.debug("Registered plugins: {}".format(", ".join(ext.name for ext in mgr.extensions)))

    return {ext.name: ext.plugin() for ext in mgr.extensions}


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

    if type(data) is dict and data.get("default", False):
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
                keys = nect.keys()
                if len(keys) > 1:
                    raise Exception("Too many keys")
                nect_type = list(keys)[0]
                value = nect.get(nect_type)
                nect_channel = create_channel(value)

            log.info("Entering nect '{}'".format(nect_type))

            #TODO: what should be the default behaviours? Maybe merge? Who should get priority? Configurable?
            if not channels.get("config", False):
                channels["config"] = nect_channel

            temp_channels = self.execute_filter(execution_step, nect_type, channels)
            if is_channel_dict(temp_channels):
                channels = temp_channels
            else:
                channels = {"default": create_channel(temp_channels)}

            log.debug("Output channels for nect '{}':\n\t{}".format(nect_type, channels))
            execution_step = execution_step + 1

        for i in channels.get("default"):
            print(i)

    def execute_filter(self, execution_step, nect_type, channels):

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


    def validate_channel(self):
        return True

    @abc.abstractmethod
    def nect(self):
        pass

    def get_config(self, config_key, default=None):
        config = self.get_channel("config")
        if config:
            return next((config_tuple[1] for config_tuple in config if config_tuple[0] == config_key), default)
            return config.get(config_key, default)
        else:
            return default

    def get_available_channels(self):
        return self.channels[self.current_execution_step].keys()

    def get_channel(self, channel_name="default"):
        return self.channels[self.current_execution_step].get(channel_name, None)

    def process(self):

        validation_result_channels = self.validate_channel()
        if not validation_result_channels:
            raise Exception("Parameters not valid")

        result_channel = self.nect()

        return result_channel
