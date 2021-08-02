import logging

from cloud_init_utils import utils


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


    def run(self, config):

        logger.info("config: `%s`", config)


        yaml_dict = utils.get_yaml_file_string_from_dict(
            config.cloud_init_settings.format_as_yaml_dict())

        import pprint
        logger.info("yaml dict: `%s`", pprint.pformat(yaml_dict))
