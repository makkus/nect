# -*- coding: utf-8 -*-

import click
import logging
import sys
from nect import Nector

@click.command()
@click.option('--verbose', help='Verbose output, for debugging purposes', default=False, is_flag=True)
@click.argument('pipeline_file', type=str, nargs=-1)
def main(verbose, pipeline_file):

    for pipe in pipeline_file:
        nector = Nector.create(pipe)
        nector.start_pipeline()

if __name__ == "__main__":
    main()
