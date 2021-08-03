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

        parser.add_argument("--output-file", dest="output_file", type=utils.isFileType(strict=False), help="Where to save the YAML file")

        create_yaml_obj = CreateYaml()

        # set the function that is called when this command is used
        parser.set_defaults(func_to_run=create_yaml_obj.run)


    def run(self, config, parsed_args):

        logger.info("config: `%s`", config)


        yaml_string = utils.get_yaml_file_string_from_dict(
            config.cloud_init_settings.format_as_yaml_dict())

        logger.info("writing yaml file to `%s`", parsed_args.output_file)
        with open(parsed_args.output_file, "w", encoding="utf-8") as f:

            f.write(yaml_string)
