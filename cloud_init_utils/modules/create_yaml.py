import logging

logger = logging.getLogger(__name__)

class CreateYaml:

    @staticmethod
    def create_subparser_command(argparse_subparser):
        '''
        populate the argparse arguments for this module

        @param argparse_subparser - the object returned by ArgumentParser.add_subparsers()
        that we call add_parser() on to add arguments and such

        '''

        parser = argparse_subparser.add_parser("create_yaml")

        create_yaml_obj = CreateYaml()

        # set the function that is called when this command is used
        parser.set_defaults(func_to_run=create_yaml_obj.run)


    def run(self, parsed_args):

        logger.info("hey there")